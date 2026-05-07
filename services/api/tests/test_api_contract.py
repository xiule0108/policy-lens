from fastapi.testclient import TestClient

from app.db.config import settings
from app.main import app


client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_provider_presets_include_china_and_custom_options() -> None:
    response = client.get("/api/llm/providers")
    assert response.status_code == 200
    provider_ids = {item["id"] for item in response.json()["items"]}
    assert "dashscope" in provider_ids
    assert "qianfan" in provider_ids
    assert "hunyuan" in provider_ids
    assert "volcark" in provider_ids
    assert "zhipu" in provider_ids
    assert "deepseek" in provider_ids
    assert "kimi" in provider_ids
    assert "minimax" in provider_ids
    assert "spark" in provider_ids
    assert "openai_compatible_custom" in provider_ids
    assert "local" in provider_ids


def test_projects_api_uses_database_records() -> None:
    empty_response = client.get("/api/projects")
    assert empty_response.status_code == 200
    assert empty_response.json()["items"] == []

    create_response = client.post(
        "/api/projects",
        json={
            "name": "Database backed workspace",
            "industry": "energy",
            "jurisdictions": ["China"],
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == "Database backed workspace"
    assert created["jurisdictions"] == ["China"]

    list_response = client.get("/api/projects")
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()["items"]] == [created["id"]]


def test_policy_original_export_returns_manifest(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    project_response = client.post(
        "/api/projects",
        json={
            "name": "Export API workspace",
            "industry": "energy",
            "jurisdictions": ["China"],
        },
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]
    upload_response = client.post(
        "/api/documents/upload",
        data={"project_id": project_id, "document_role": "policy", "title": "Export contract policy"},
        files={"file": ("policy.md", b"# Export contract policy\n\nSupport clean energy.", "text/markdown")},
    )
    assert upload_response.status_code == 201
    document_id = upload_response.json()["id"]
    parse_response = client.post(f"/api/documents/{document_id}/parse")
    assert parse_response.status_code == 200
    ingest_response = client.post("/api/policies/from-document", json={"document_id": document_id})
    assert ingest_response.status_code == 201
    policy_id = ingest_response.json()["policy_id"]

    response = client.post(
        "/api/exports/policy-originals",
        json={
            "project_id": project_id,
            "policy_ids": [policy_id],
            "mode": "related_policy_bundle",
        },
    )
    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["manifest"]["policy_count"] == 1
    assert payload["manifest"]["checksums"]["path"] == "checksums/sha256.txt"


def test_policy_original_export_rejects_invalid_project_id() -> None:
    response = client.post(
        "/api/exports/policy-originals",
        json={
            "project_id": "project_demo_001",
            "policy_ids": ["policy_demo_001"],
            "mode": "related_policy_bundle",
        },
    )

    assert response.status_code == 422
