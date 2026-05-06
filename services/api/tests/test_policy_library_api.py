from fastapi.testclient import TestClient

from app.db.config import settings
from app.main import app


client = TestClient(app)


def create_project() -> str:
    response = client.post(
        "/api/projects",
        json={"name": "Policy library workspace", "industry": "energy", "jurisdictions": ["China"]},
    )
    assert response.status_code == 201
    return response.json()["id"]


def upload_policy_document(project_id: str, *, role: str = "policy", content: bytes = b"# Policy title\n\nSupport clean energy."):
    return client.post(
        "/api/documents/upload",
        data={"project_id": project_id, "document_role": role, "title": "Uploaded policy"},
        files={"file": ("policy.md", content, "text/markdown")},
    )


def create_parsed_policy_document(
    project_id: str,
    *,
    title: str = "Uploaded policy",
    content: bytes = b"# Policy title\n\nSupport clean energy.",
) -> str:
    upload_response = client.post(
        "/api/documents/upload",
        data={"project_id": project_id, "document_role": "policy", "title": title},
        files={"file": ("policy.md", content, "text/markdown")},
    )
    assert upload_response.status_code == 201
    document_id = upload_response.json()["id"]
    parse_response = client.post(f"/api/documents/{document_id}/parse")
    assert parse_response.status_code == 200
    return document_id


def test_policy_library_api_full_flow(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    project_id = create_project()
    document_id = create_parsed_policy_document(project_id)

    ingest_response = client.post(
        "/api/policies/from-document",
        json={
            "document_id": document_id,
            "issuer": "National Energy Office",
            "jurisdiction": "China",
            "policy_type": "notice",
            "status": "active",
            "version_label": "initial",
        },
    )

    assert ingest_response.status_code == 201
    ingest_payload = ingest_response.json()
    policy_id = ingest_payload["policy_id"]
    assert ingest_payload["section_count"] >= 2
    assert ingest_payload["already_ingested"] is False

    list_response = client.get("/api/policies", params={"query": "Policy title", "jurisdiction": "China"})
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()["items"]] == [policy_id]

    search_response = client.post("/api/policies/search", json={"query": "energy", "limit": 10})
    assert search_response.status_code == 200
    assert search_response.json()["total"] == 1
    assert search_response.json()["items"][0]["id"] == policy_id

    detail_response = client.get(f"/api/policies/{policy_id}")
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["id"] == policy_id
    assert detail_payload["issuer"] == "National Energy Office"
    assert detail_payload["current_version_id"] == ingest_payload["version_id"]

    versions_response = client.get(f"/api/policies/{policy_id}/versions")
    assert versions_response.status_code == 200
    assert [item["id"] for item in versions_response.json()["items"]] == [ingest_payload["version_id"]]

    sections_response = client.get(f"/api/policies/{policy_id}/sections")
    assert sections_response.status_code == 200
    assert sections_response.json()["total"] == ingest_payload["section_count"]
    assert sections_response.json()["items"][0]["order_index"] == 0

    original_response = client.get(f"/api/policies/{policy_id}/original")
    assert original_response.status_code == 200
    original_payload = original_response.json()
    assert original_payload["policy_id"] == policy_id
    assert "Support clean energy." in original_payload["normalized_text"]
    assert original_payload["sections_count"] == ingest_payload["section_count"]

    duplicate_response = client.post("/api/policies/from-document", json={"document_id": document_id})
    assert duplicate_response.status_code == 200
    assert duplicate_response.json()["already_ingested"] is True
    assert duplicate_response.json()["version_id"] == ingest_payload["version_id"]

    forced_response = client.post(
        "/api/policies/from-document",
        json={"document_id": document_id, "force_new_version": True, "version_label": "second"},
    )
    assert forced_response.status_code == 201
    assert forced_response.json()["policy_id"] == policy_id
    assert forced_response.json()["version_id"] != ingest_payload["version_id"]
    assert len(client.get(f"/api/policies/{policy_id}/versions").json()["items"]) == 2


def test_policy_library_api_rejects_rebinding_ingested_document(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    project_id = create_project()
    first_document_id = create_parsed_policy_document(project_id, title="First policy")
    first_ingest = client.post("/api/policies/from-document", json={"document_id": first_document_id})
    assert first_ingest.status_code == 201

    second_document_id = create_parsed_policy_document(project_id, title="Second policy")
    second_ingest = client.post("/api/policies/from-document", json={"document_id": second_document_id})
    assert second_ingest.status_code == 201
    second_policy_id = second_ingest.json()["policy_id"]

    conflict_response = client.post(
        "/api/policies/from-document",
        json={"document_id": first_document_id, "policy_id": second_policy_id, "force_new_version": True},
    )

    assert conflict_response.status_code == 409


def test_policy_search_applies_filters_before_limit(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    project_id = create_project()
    china_document_id = create_parsed_policy_document(
        project_id,
        title="China energy policy",
        content=b"# Energy transition policy\n\nChina clean energy text.",
    )
    china_ingest = client.post(
        "/api/policies/from-document",
        json={
            "document_id": china_document_id,
            "jurisdiction": "China",
            "policy_type": "notice",
        },
    )
    assert china_ingest.status_code == 201
    china_policy_id = china_ingest.json()["policy_id"]

    eu_document_id = create_parsed_policy_document(
        project_id,
        title="EU energy policy",
        content=b"# Energy transition policy\n\nEU clean energy text.",
    )
    eu_ingest = client.post(
        "/api/policies/from-document",
        json={
            "document_id": eu_document_id,
            "jurisdiction": "EU",
            "policy_type": "memo",
        },
    )
    assert eu_ingest.status_code == 201

    search_response = client.post(
        "/api/policies/search",
        json={"query": "Energy", "jurisdictions": ["China"], "policy_types": ["notice"], "limit": 1},
    )

    assert search_response.status_code == 200
    assert [item["id"] for item in search_response.json()["items"]] == [china_policy_id]


def test_policy_library_api_errors(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    project_id = create_project()

    missing_policy_response = client.get("/api/policies/11111111-1111-4111-8111-111111111111")
    assert missing_policy_response.status_code == 404

    pending_upload = upload_policy_document(project_id)
    pending_document_id = pending_upload.json()["id"]
    pending_ingest = client.post("/api/policies/from-document", json={"document_id": pending_document_id})
    assert pending_ingest.status_code == 409

    article_upload = upload_policy_document(project_id, role="research_article")
    article_document_id = article_upload.json()["id"]
    article_parse = client.post(f"/api/documents/{article_document_id}/parse")
    assert article_parse.status_code == 200
    article_ingest = client.post("/api/policies/from-document", json={"document_id": article_document_id})
    assert article_ingest.status_code == 409
