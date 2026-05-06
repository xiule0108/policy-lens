from pathlib import Path

from fastapi.testclient import TestClient

from app.db.config import settings
from app.main import app
from app.repositories.documents import create_document, get_document
from app.repositories.projects import create_project


client = TestClient(app)


def create_project_via_api() -> str:
    response = client.post(
        "/api/projects",
        json={
            "name": "Parse workspace",
            "industry": "energy",
            "jurisdictions": ["China"],
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def upload_text_document(project_id: str, content: bytes = b"Policy paragraph\nSecond paragraph"):
    return client.post(
        "/api/documents/upload",
        data={
            "project_id": project_id,
            "document_role": "research_article",
            "title": "Uploaded memo",
        },
        files={"file": ("memo.txt", content, "text/plain")},
    )


def test_parse_uploaded_txt_document_creates_chunks_and_updates_status(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    project_id = create_project_via_api()
    upload_response = upload_text_document(project_id)
    assert upload_response.status_code == 201
    document_id = upload_response.json()["id"]

    parse_response = client.post(f"/api/documents/{document_id}/parse")

    assert parse_response.status_code == 200
    parse_payload = parse_response.json()
    assert parse_payload["document_id"] == document_id
    assert parse_payload["parse_status"] == "parsed"
    assert parse_payload["chunk_count"] >= 1

    detail_response = client.get(f"/api/documents/{document_id}")
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["parse_status"] == "parsed"
    assert detail_payload["metadata"]["content_type"] == "text/plain"
    assert detail_payload["metadata"]["original_filename"] == "memo.txt"
    assert detail_payload["metadata"]["safe_filename"] == "memo.txt"
    assert detail_payload["metadata"]["parse_summary"]["chunk_count"] == parse_payload["chunk_count"]

    chunks_response = client.get(f"/api/documents/{document_id}/chunks")
    assert chunks_response.status_code == 200
    chunks_payload = chunks_response.json()
    assert chunks_payload["total"] == parse_payload["chunk_count"]
    assert chunks_payload["items"][0]["chunk_index"] == 0
    assert "Policy paragraph" in chunks_payload["items"][0]["content"]


def test_reparse_replaces_old_chunks_without_accumulating(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    project_id = create_project_via_api()
    upload_response = upload_text_document(project_id, b"One paragraph")
    document_id = upload_response.json()["id"]

    first_response = client.post(f"/api/documents/{document_id}/parse")
    second_response = client.post(f"/api/documents/{document_id}/parse")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    chunks_response = client.get(f"/api/documents/{document_id}/chunks")
    assert chunks_response.json()["total"] == second_response.json()["chunk_count"]


def test_parse_chinese_txt_sets_language(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    project_id = create_project_via_api()
    upload_response = upload_text_document(project_id, "新能源政策推动市场变化".encode())
    document_id = upload_response.json()["id"]

    parse_response = client.post(f"/api/documents/{document_id}/parse")

    assert parse_response.status_code == 200
    assert parse_response.json()["language"] == "zh-CN"


def test_get_chunks_returns_404_for_missing_document() -> None:
    response = client.get("/api/documents/11111111-1111-4111-8111-111111111111/chunks")

    assert response.status_code == 404


def test_parse_rejects_invalid_document_id() -> None:
    response = client.post("/api/documents/not-a-uuid/parse")

    assert response.status_code == 422


def test_parse_returns_404_when_file_is_missing(tmp_path, monkeypatch, db_session) -> None:
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    project = create_project(db_session, {"name": "Missing file workspace"})
    document = create_document(
        db_session,
        {
            "project_id": project.id,
            "document_role": "research_article",
            "file_name": "missing.txt",
            "file_type": ".txt",
            "storage_key": "documents/project/document/missing.txt",
        },
    )

    response = client.post(f"/api/documents/{document.id}/parse")

    assert response.status_code == 404


def test_parse_unsupported_extension_sets_failed(tmp_path, monkeypatch, db_session) -> None:
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    project = create_project(db_session, {"name": "Unsupported workspace"})
    file_path = tmp_path / "documents" / str(project.id) / "doc" / "memo.exe"
    file_path.parent.mkdir(parents=True)
    file_path.write_text("hello", encoding="utf-8")
    document = create_document(
        db_session,
        {
            "project_id": project.id,
            "document_role": "research_article",
            "file_name": "memo.exe",
            "file_type": ".exe",
            "storage_key": f"documents/{project.id}/doc/memo.exe",
        },
    )

    response = client.post(f"/api/documents/{document.id}/parse")

    assert response.status_code == 400
    db_session.expire_all()
    document_after = get_document(db_session, document.id)
    assert document_after.parse_status == "failed"
    assert document_after.metadata_["parse_error"]["type"] == "UnsupportedDocumentTypeError"


def test_parse_empty_text_returns_422_and_records_error(tmp_path, monkeypatch, db_session) -> None:
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    project = create_project(db_session, {"name": "Empty parser workspace"})
    file_path = tmp_path / "documents" / str(project.id) / "doc" / "empty.txt"
    file_path.parent.mkdir(parents=True)
    file_path.write_text("   \n", encoding="utf-8")
    document = create_document(
        db_session,
        {
            "project_id": project.id,
            "document_role": "research_article",
            "file_name": "empty.txt",
            "file_type": ".txt",
            "storage_key": f"documents/{project.id}/doc/empty.txt",
        },
    )

    response = client.post(f"/api/documents/{document.id}/parse")

    assert response.status_code == 422
    db_session.expire_all()
    document_after = get_document(db_session, document.id)
    assert document_after.parse_status == "failed"
    assert "parse_error" in document_after.metadata_


def test_successful_reparse_clears_previous_parse_error(tmp_path, monkeypatch, db_session) -> None:
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    project = create_project(db_session, {"name": "Reparse workspace"})
    file_path = tmp_path / "documents" / str(project.id) / "doc" / "memo.txt"
    file_path.parent.mkdir(parents=True)
    file_path.write_text("   \n", encoding="utf-8")
    document = create_document(
        db_session,
        {
            "project_id": project.id,
            "document_role": "research_article",
            "file_name": "memo.txt",
            "file_type": ".txt",
            "storage_key": f"documents/{project.id}/doc/memo.txt",
            "metadata": {
                "content_type": "text/plain",
                "original_filename": "memo.txt",
                "safe_filename": "memo.txt",
            },
        },
    )

    failed_response = client.post(f"/api/documents/{document.id}/parse")

    assert failed_response.status_code == 422
    db_session.expire_all()
    failed_document = get_document(db_session, document.id)
    assert failed_document.parse_status == "failed"
    assert "parse_error" in failed_document.metadata_

    file_path.write_text("Valid policy text for parsing.", encoding="utf-8")
    parsed_response = client.post(f"/api/documents/{document.id}/parse")

    assert parsed_response.status_code == 200
    db_session.expire_all()
    parsed_document = get_document(db_session, document.id)
    assert parsed_document.parse_status == "parsed"
    assert "parse_error" not in parsed_document.metadata_
    assert "parse_summary" in parsed_document.metadata_
    assert parsed_document.metadata_["content_type"] == "text/plain"
    assert parsed_document.metadata_["original_filename"] == "memo.txt"
    assert parsed_document.metadata_["safe_filename"] == "memo.txt"
