#!/usr/bin/env python3
"""Run the PolicyLens v0.1 demo workflow against a running API server."""

from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = REPO_ROOT / "examples"
API_BASE_URL = os.environ.get("POLICYLENS_API_BASE_URL", "http://localhost:8000").rstrip("/")


class DemoStepError(RuntimeError):
    def __init__(self, step: str, status: int | None, body: str):
        self.step = step
        self.status = status
        self.body = body
        super().__init__(f"{step} failed")


def main() -> int:
    try:
        run_workflow()
    except DemoStepError as exc:
        print(f"Step failed: {exc.step}", file=sys.stderr)
        if exc.status is not None:
            print(f"HTTP status: {exc.status}", file=sys.stderr)
        print("Response body:", file=sys.stderr)
        print(exc.body, file=sys.stderr)
        return 1
    except URLError as exc:
        print(f"Could not reach PolicyLens API at {API_BASE_URL}: {exc}", file=sys.stderr)
        return 1
    return 0


def run_workflow() -> None:
    request_json("health", "GET", "/api/health", expected={200})

    project = request_json(
        "create project",
        "POST",
        "/api/projects",
        {
            "name": f"PolicyLens v0.1 demo {uuid.uuid4().hex[:8]}",
            "description": "Created by scripts/e2e_demo.py",
            "industry": "energy",
            "jurisdictions": ["China"],
            "default_model_profile": "china_balanced",
        },
        expected={201},
    )
    project_id = project["id"]

    policy_upload = upload_file(
        "upload policy document",
        "/api/documents/upload",
        fields={
            "project_id": project_id,
            "document_role": "policy",
            "title": "示例储能政策",
        },
        file_path=EXAMPLES_DIR / "demo-policy-notice.txt",
        content_type="text/plain",
        expected={201},
    )
    policy_document_id = policy_upload["id"]

    request_json("parse policy document", "POST", f"/api/documents/{policy_document_id}/parse", expected={200})

    metadata = json.loads((EXAMPLES_DIR / "demo-policy-metadata.json").read_text(encoding="utf-8"))
    policy_ingest = request_json(
        "ingest policy",
        "POST",
        "/api/policies/from-document",
        {"document_id": policy_document_id, **metadata},
        expected={201, 200},
    )
    policy_id = policy_ingest["policy_id"]

    article_upload = upload_file(
        "upload research article",
        "/api/documents/upload",
        fields={
            "project_id": project_id,
            "document_role": "research_article",
            "title": "新能源储能市场研究",
        },
        file_path=EXAMPLES_DIR / "demo-research-article.txt",
        content_type="text/plain",
        expected={201},
    )
    article_document_id = article_upload["id"]

    request_json("parse research article", "POST", f"/api/documents/{article_document_id}/parse", expected={200})

    analysis = request_json(
        "run analysis",
        "POST",
        "/api/analysis/jobs",
        {
            "project_id": project_id,
            "document_ids": [article_document_id],
            "analysis_types": ["policy_deep_dive"],
            "model_profile": "china_balanced",
        },
        expected={201},
    )
    job_id = analysis["id"]

    request_json("get evidence", "GET", f"/api/analysis/jobs/{job_id}/evidence", expected={200})
    request_json("get impact matrix", "GET", f"/api/analysis/jobs/{job_id}/impact-matrix", expected={200})
    request_json("get report", "GET", f"/api/analysis/jobs/{job_id}/report", expected={200})

    report_export = request_json(
        "create report export",
        "POST",
        "/api/exports/report",
        {
            "job_id": job_id,
            "formats": ["markdown", "json", "html"],
            "include_evidence_bundle": True,
            "include_impact_matrix": True,
            "include_policy_matches": True,
        },
        expected={202},
    )
    report_export_id = report_export["export_id"]
    request_json("get report export", "GET", f"/api/exports/{report_export_id}", expected={200})

    policy_export = request_json(
        "create policy original export",
        "POST",
        "/api/exports/policy-originals",
        {
            "project_id": project_id,
            "policy_ids": [policy_id],
            "mode": "single_policy_full_text",
            "formats": ["markdown", "json"],
        },
        expected={202},
    )
    policy_export_id = policy_export["export_id"]
    request_json("get policy export", "GET", f"/api/exports/{policy_export_id}", expected={200})

    print("PolicyLens v0.1 demo workflow completed successfully.")
    print(f"Project ID: {project_id}")
    print(f"Policy ID: {policy_id}")
    print(f"Analysis Job ID: {job_id}")
    print(f"Report Export ID: {report_export_id}")
    print(f"Policy Export ID: {policy_export_id}")


def request_json(
    step: str,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    *,
    expected: set[int],
) -> dict[str, Any]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    request = Request(f"{API_BASE_URL}{path}", data=body, headers=headers, method=method)
    status, response_body = open_request(step, request)
    if status not in expected:
        raise DemoStepError(step, status, response_body)
    if not response_body:
        return {}
    return json.loads(response_body)


def upload_file(
    step: str,
    path: str,
    *,
    fields: dict[str, str],
    file_path: Path,
    content_type: str,
    expected: set[int],
) -> dict[str, Any]:
    boundary = f"PolicyLensBoundary{uuid.uuid4().hex}"
    body = build_multipart_body(boundary, fields, file_path, content_type)
    request = Request(
        f"{API_BASE_URL}{path}",
        data=body,
        headers={
            "Accept": "application/json",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    status, response_body = open_request(step, request)
    if status not in expected:
        raise DemoStepError(step, status, response_body)
    return json.loads(response_body)


def build_multipart_body(boundary: str, fields: dict[str, str], file_path: Path, content_type: str) -> bytes:
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.append(f"--{boundary}\r\n".encode())
        chunks.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        chunks.append(str(value).encode("utf-8"))
        chunks.append(b"\r\n")
    chunks.append(f"--{boundary}\r\n".encode())
    chunks.append(
        (
            f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode()
    )
    chunks.append(file_path.read_bytes())
    chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks)


def open_request(step: str, request: Request) -> tuple[int, str]:
    try:
        with urlopen(request, timeout=60) as response:
            return response.status, response.read().decode("utf-8")
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise DemoStepError(step, exc.code, body) from exc


if __name__ == "__main__":
    raise SystemExit(main())
