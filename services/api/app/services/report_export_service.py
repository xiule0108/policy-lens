from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
from typing import Any
from uuid import UUID
import zipfile

from sqlalchemy.orm import Session

from app.db.config import settings
from app.db.models import AnalysisJob, AnalysisResult, PolicyMatch
from app.repositories.analysis_jobs import get_analysis_job
from app.repositories.analysis_results import get_analysis_result, get_analysis_result_by_job_id
from app.repositories.exports import create_export, update_export_status
from app.repositories.policy_matches import list_policy_matches
from app.schemas.common import EvidenceItem, ExportResponse, ReportExportRequest
from app.services.storage_service import ensure_child_path


CHECKSUM_PATH = "checksums/sha256.txt"


class ReportExportError(Exception):
    """Base class for report export failures."""


class ReportExportValidationError(ReportExportError):
    """Raised when a report export request is invalid."""


class ReportExportNotFoundError(ReportExportError):
    """Raised when the requested analysis result cannot be found."""


@dataclass(frozen=True)
class ReportExportResult:
    export_id: str
    storage_key: str
    absolute_path: Path
    manifest: dict[str, Any]
    status: str


def create_report_export(session: Session, payload: ReportExportRequest) -> ExportResponse:
    validate_report_export_request(payload)
    job, result = resolve_report_export_source(session, payload)
    if not result.report_markdown:
        raise ReportExportValidationError("analysis result report_markdown is empty.")
    if payload.project_id and payload.project_id != result.project_id:
        raise ReportExportValidationError("project_id does not match the analysis result.")

    db_export = create_export(
        session,
        {
            "project_id": payload.project_id or result.project_id,
            "analysis_id": result.id,
            "export_type": "report",
            "status": "running",
            "formats": list(payload.formats),
            "manifest": {
                "job_id": str(job.id) if job else str(result.job_id),
                "analysis_id": str(result.id),
                "formats": list(payload.formats),
            },
        },
    )
    try:
        policy_matches = list_policy_matches(session, analysis_id=result.id, limit=100_000)
        bundle = write_report_export_bundle(
            export_id=str(db_export.id),
            storage_root=Path(settings.storage_dir),
            payload=payload,
            result=result,
            job=job,
            policy_matches=policy_matches,
        )
    except Exception as exc:
        update_export_status(
            session,
            db_export.id,
            "failed",
            manifest={
                **(db_export.manifest or {}),
                "error": {"type": exc.__class__.__name__, "message": str(exc)},
            },
        )
        raise

    db_export = update_export_status(
        session,
        db_export.id,
        "completed",
        storage_key=bundle.storage_key,
        manifest=bundle.manifest,
    )
    return ExportResponse(
        export_id=str(db_export.id),
        status=db_export.status,
        mode="report",
        bundle_path=bundle.storage_key,
        manifest=bundle.manifest,
        evidence=[
            EvidenceItem(
                id=f"{db_export.id}_manifest",
                source_type="report_export_manifest",
                summary="Research report export bundle generated from an analysis result.",
                confidence=1.0,
            )
        ],
    )


def validate_report_export_request(payload: ReportExportRequest) -> None:
    if not payload.job_id and not payload.analysis_id:
        raise ReportExportValidationError("job_id or analysis_id must be provided.")
    if not payload.formats:
        raise ReportExportValidationError("formats must contain at least one report format.")


def resolve_report_export_source(
    session: Session, payload: ReportExportRequest
) -> tuple[AnalysisJob | None, AnalysisResult]:
    if payload.analysis_id:
        result = get_analysis_result(session, payload.analysis_id)
        if result is None:
            raise ReportExportNotFoundError("Analysis result not found.")
        return get_analysis_job(session, result.job_id), result
    if payload.job_id:
        job = get_analysis_job(session, payload.job_id)
        if job is None:
            raise ReportExportNotFoundError("Analysis job not found.")
        result = get_analysis_result_by_job_id(session, job.id)
        if result is None:
            raise ReportExportNotFoundError("Analysis result not found.")
        return job, result
    raise ReportExportValidationError("job_id or analysis_id must be provided.")


def write_report_export_bundle(
    *,
    export_id: str,
    storage_root: Path,
    payload: ReportExportRequest,
    result: AnalysisResult,
    job: AnalysisJob | None,
    policy_matches: list[PolicyMatch],
) -> ReportExportResult:
    generated_at = datetime.now(timezone.utc).isoformat()
    report_json = result.report_json or {}
    files: dict[str, bytes] = {}
    paths: dict[str, str] = {}

    if "markdown" in payload.formats:
        paths["markdown"] = "reports/report.md"
        files[paths["markdown"]] = text_bytes(result.report_markdown or "")
    if "json" in payload.formats:
        paths["json"] = "reports/report.json"
        files[paths["json"]] = json_bytes(build_report_json_payload(result))
    if "html" in payload.formats:
        paths["html"] = "reports/report.html"
        files[paths["html"]] = text_bytes(render_report_html(result.report_markdown or ""))

    if payload.include_evidence_bundle:
        paths["evidence"] = "evidence/evidence.json"
        files[paths["evidence"]] = json_bytes(
            {
                "claim_policy_map": report_json.get("claim_policy_map", []),
                "fact_boundaries": report_json.get("fact_boundaries", {}),
            }
        )
    if payload.include_impact_matrix:
        paths["impact_matrix"] = "impact_matrix/impact_matrix.json"
        files[paths["impact_matrix"]] = json_bytes(result.impact_matrix or [])
    if payload.include_policy_matches:
        paths["policy_matches"] = "policy_matches/policy_matches.json"
        files[paths["policy_matches"]] = json_bytes([policy_match_payload(match) for match in policy_matches])

    manifest = build_manifest(
        export_id=export_id,
        generated_at=generated_at,
        payload=payload,
        result=result,
        job=job,
        paths=paths,
    )
    files["manifest.json"] = json_bytes(manifest)
    files[CHECKSUM_PATH] = render_checksums(files)
    absolute_path, storage_key = write_zip_file(storage_root, export_id, files)
    return ReportExportResult(
        export_id=export_id,
        storage_key=storage_key,
        absolute_path=absolute_path,
        manifest=manifest,
        status="completed",
    )


def build_manifest(
    *,
    export_id: str,
    generated_at: str,
    payload: ReportExportRequest,
    result: AnalysisResult,
    job: AnalysisJob | None,
    paths: dict[str, str],
) -> dict[str, Any]:
    report_json = result.report_json or {}
    outline = report_json.get("report_outline", {})
    return {
        "export_id": export_id,
        "export_type": "report",
        "generated_at": generated_at,
        "project_id": str(payload.project_id or result.project_id),
        "job_id": str(job.id) if job else str(result.job_id),
        "analysis_id": str(result.id),
        "formats": list(payload.formats),
        "paths": paths,
        "checksums": {"algorithm": "sha256", "path": CHECKSUM_PATH},
        "generation_method": outline.get("generation_method", "deterministic_rule_based"),
        "llm_used": bool(outline.get("llm_used", False)),
    }


def build_report_json_payload(result: AnalysisResult) -> dict[str, Any]:
    return {
        "summary": result.summary or {},
        "claims": result.claims or [],
        "related_policies": result.related_policies or [],
        "impact_matrix": result.impact_matrix or [],
        "report_json": result.report_json or {},
        "created_at": result.created_at.isoformat(),
    }


def policy_match_payload(match: PolicyMatch) -> dict[str, Any]:
    return {
        "id": str(match.id),
        "project_id": str(match.project_id),
        "analysis_id": str(match.analysis_id) if match.analysis_id else None,
        "claim_id": str(match.claim_id),
        "policy_id": str(match.policy_id),
        "policy_section_id": str(match.policy_section_id) if match.policy_section_id else None,
        "match_type": match.match_type,
        "relevance_score": float(match.relevance_score) if match.relevance_score is not None else None,
        "reason": match.reason,
        "evidence": match.evidence or {},
        "created_at": match.created_at.isoformat(),
    }


def render_report_html(markdown: str) -> str:
    escaped = html.escape(markdown)
    return (
        "<!doctype html>\n"
        "<html><head><meta charset=\"utf-8\"><title>PolicyLens Report</title></head>"
        f"<body><pre>{escaped}</pre></body></html>"
    )


def write_zip_file(storage_root: Path, export_id: str, files: dict[str, bytes]) -> tuple[Path, str]:
    storage_root = storage_root.resolve()
    storage_key = f"exports/{export_id}/report_export_bundle.zip"
    target_path = ensure_child_path(storage_root, storage_root / storage_key)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = target_path.with_suffix(".zip.tmp")
    try:
        with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            for path, content in files.items():
                bundle.writestr(path, content)
        temp_path.replace(target_path)
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        if target_path.exists():
            target_path.unlink()
        raise
    return target_path, storage_key


def render_checksums(files: dict[str, bytes]) -> bytes:
    lines = []
    for path in sorted(files):
        if path == CHECKSUM_PATH:
            continue
        lines.append(f"{hashlib.sha256(files[path]).hexdigest()}  {path}")
    return ("\n".join(lines) + "\n").encode("utf-8")


def json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2, default=str).encode("utf-8")


def text_bytes(value: str) -> bytes:
    return value.encode("utf-8")
