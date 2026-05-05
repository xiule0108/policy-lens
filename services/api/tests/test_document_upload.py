from hashlib import sha256

from fastapi.testclient import TestClient

from app.db.config import settings
from app.repositories.documents import get_document
from app.main import app
from app.routers import documents as document_router


client = TestClient(app)


def create_project() -> str:
    response = client.post(
        "/api/projects",
        json={
            "name": "Upload workspace",
            "industry": "energy",
            "jurisdictions": ["China"],
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def upload_txt(project_id: str, content: bytes = b"hello policy\n"):
    return client.post(
        "/api/documents/upload",
        data={
            "project_id": project_id,
            "document_role": "research_article",
            "title": "Policy memo",
            "source_url": "https://example.com/source",
        },
        files={"file": ("memo.txt", content, "text/plain")},
    )


def test_upload_document_persists_file_and_document_record(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    project_id = create_project()
    content = b"uploaded research text\n"

    upload_response = upload_txt(project_id, content)

    assert upload_response.status_code == 201
    payload = upload_response.json()
    assert payload["project_id"] == project_id
    assert payload["document_role"] == "research_article"
    assert payload["title"] == "Policy memo"
    assert payload["file_name"] == "memo.txt"
    assert payload["file_type"] == ".txt"
    assert payload["file_size"] == len(content)
    assert payload["content_type"] == "text/plain"
    assert payload["storage_key"].startswith(f"documents/{project_id}/{payload['id']}/")
    assert payload["parse_status"] == "pending"
    assert payload["source_url"] == "https://example.com/source"
    assert payload["sha256"] == sha256(content).hexdigest()
    assert (tmp_path / payload["storage_key"]).read_bytes() == content

    list_response = client.get("/api/documents", params={"project_id": project_id})
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()["items"]] == [payload["id"]]

    detail_response = client.get(f"/api/documents/{payload['id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["sha256"] == sha256(content).hexdigest()

    download_response = client.get(f"/api/documents/{payload['id']}/download")
    assert download_response.status_code == 200
    assert download_response.content == content
    assert "memo.txt" in download_response.headers["content-disposition"]
    assert str(tmp_path) not in download_response.headers["content-disposition"]


def test_upload_document_accepts_unicode_filename_and_preserves_metadata(
    tmp_path,
    monkeypatch,
    db_session,
) -> None:
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    project_id = create_project()
    content = "中文政策文件".encode()

    response = client.post(
        "/api/documents/upload",
        data={
            "project_id": project_id,
            "document_role": "policy",
            "title": "中文政策文件",
        },
        files={"file": ("政策报告.pdf", content, "application/pdf")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["file_name"] == "政策报告.pdf"
    assert payload["file_type"] == ".pdf"
    assert payload["metadata"]["original_filename"] == "政策报告.pdf"
    assert payload["metadata"]["safe_filename"] == "政策报告.pdf"
    assert not payload["storage_key"].startswith(str(tmp_path))

    document = get_document(db_session, payload["id"])
    assert document is not None
    assert document.metadata_["original_filename"] == "政策报告.pdf"
    assert document.metadata_["safe_filename"] == "政策报告.pdf"

    download_response = client.get(f"/api/documents/{payload['id']}/download")
    assert download_response.status_code == 200
    assert download_response.content == content


def test_upload_document_rejects_invalid_project_id() -> None:
    response = client.post(
        "/api/documents/upload",
        data={"project_id": "project_demo_001", "document_role": "research_article"},
        files={"file": ("memo.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 422


def test_upload_document_rejects_missing_project(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    missing_project_id = "11111111-1111-4111-8111-111111111111"

    response = upload_txt(missing_project_id)

    assert response.status_code == 404
    assert list(tmp_path.rglob("*")) == []


def test_upload_document_rejects_invalid_document_role() -> None:
    project_id = create_project()
    response = client.post(
        "/api/documents/upload",
        data={"project_id": project_id, "document_role": "invalid_role"},
        files={"file": ("memo.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 422


def test_upload_document_rejects_unsupported_extension(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    project_id = create_project()
    response = client.post(
        "/api/documents/upload",
        data={"project_id": project_id, "document_role": "research_article"},
        files={"file": ("runner.exe", b"hello", "application/octet-stream")},
    )

    assert response.status_code == 400
    assert list(tmp_path.rglob("*")) == []


def test_upload_document_rejects_empty_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    project_id = create_project()

    response = upload_txt(project_id, b"")

    assert response.status_code == 400
    assert list(tmp_path.rglob("*")) == []


def test_upload_document_rejects_oversized_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    monkeypatch.setattr(settings, "max_upload_size_mb", 0)
    project_id = create_project()

    response = upload_txt(project_id, b"too large")

    assert response.status_code == 413
    assert list(tmp_path.rglob("*")) == []


def test_upload_document_cleans_file_when_database_insert_fails(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    project_id = create_project()

    def fail_create_document(*args, **kwargs):
        raise RuntimeError("db insert failed")

    monkeypatch.setattr(document_router, "create_document", fail_create_document)

    response = upload_txt(project_id, b"will be cleaned")

    assert response.status_code == 500
    assert list(tmp_path.rglob("*")) == []
