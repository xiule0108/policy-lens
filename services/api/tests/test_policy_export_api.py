import json
import zipfile

from fastapi.testclient import TestClient

from app.db.config import settings
from app.main import app
from app.repositories.exports import create_export


client = TestClient(app)


def create_project() -> str:
    response = client.post(
        "/api/projects",
        json={"name": "Policy export workspace", "industry": "energy", "jurisdictions": ["China"]},
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_ingested_policy(project_id: str) -> tuple[str, str]:
    upload_response = client.post(
        "/api/documents/upload",
        data={"project_id": project_id, "document_role": "policy", "title": "Exportable policy"},
        files={"file": ("policy.md", b"# Exportable policy\n\nSupport clean energy.", "text/markdown")},
    )
    assert upload_response.status_code == 201
    document_id = upload_response.json()["id"]
    parse_response = client.post(f"/api/documents/{document_id}/parse")
    assert parse_response.status_code == 200
    ingest_response = client.post(
        "/api/policies/from-document",
        json={"document_id": document_id, "jurisdiction": "China", "policy_type": "notice"},
    )
    assert ingest_response.status_code == 201
    policy_id = ingest_response.json()["policy_id"]
    sections_response = client.get(f"/api/policies/{policy_id}/sections")
    assert sections_response.status_code == 200
    section_id = sections_response.json()["items"][0]["id"]
    return policy_id, section_id


def test_policy_export_api_create_detail_and_download(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    project_id = create_project()
    policy_id, _section_id = create_ingested_policy(project_id)

    export_response = client.post(
        "/api/exports/policy-originals",
        json={
            "project_id": project_id,
            "policy_ids": [policy_id],
            "mode": "single_policy_full_text",
            "formats": ["markdown", "json"],
        },
    )

    assert export_response.status_code == 202
    export_payload = export_response.json()
    assert export_payload["status"] == "completed"
    assert export_payload["bundle_path"] == f"exports/{export_payload['export_id']}/policy_export_bundle.zip"
    assert export_payload["manifest"]["policy_count"] == 1

    detail_response = client.get(f"/api/exports/{export_payload['export_id']}")
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["status"] == "completed"
    assert detail_payload["storage_key"] == export_payload["bundle_path"]
    assert detail_payload["formats"] == ["markdown", "json"]

    download_response = client.get(f"/api/exports/{export_payload['export_id']}/download")
    assert download_response.status_code == 200
    assert download_response.headers["content-type"] == "application/zip"
    assert str(tmp_path) not in download_response.headers.get("content-disposition", "")

    zip_path = tmp_path / export_payload["bundle_path"]
    with zipfile.ZipFile(zip_path) as bundle:
        assert "manifest.json" in bundle.namelist()
        assert f"policies/{policy_id}/policy.md" in bundle.namelist()
        manifest = json.loads(bundle.read("manifest.json").decode("utf-8"))
    assert manifest["policies"][0]["policy_id"] == policy_id


def test_policy_export_api_validation_errors(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    project_id = create_project()

    empty_response = client.post("/api/exports/policy-originals", json={"mode": "related_policy_bundle"})
    assert empty_response.status_code == 422

    missing_policy_response = client.post(
        "/api/exports/policy-originals",
        json={
            "project_id": project_id,
            "policy_ids": ["11111111-1111-4111-8111-111111111111"],
            "mode": "related_policy_bundle",
        },
    )
    assert missing_policy_response.status_code == 404

    cited_missing_response = client.post(
        "/api/exports/policy-originals",
        json={"project_id": project_id, "mode": "cited_sections_only"},
    )
    assert cited_missing_response.status_code == 422


def test_policy_export_download_rejects_unfinished_exports(db_session) -> None:
    export = create_export(
        db_session,
        {
            "export_type": "policy_originals",
            "status": "running",
            "formats": ["zip"],
            "manifest": {"mode": "related_policy_bundle"},
        },
    )

    response = client.get(f"/api/exports/{export.id}/download")

    assert response.status_code == 409
