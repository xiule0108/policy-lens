from hashlib import sha256
from io import BytesIO

import pytest
from starlette.datastructures import Headers, UploadFile

from app.services.storage_service import (
    EmptyUploadError,
    UploadExtensionError,
    UploadTooLargeError,
    normalize_filename,
    save_upload_file,
    validate_upload_extension,
)


def make_upload(filename: str, content: bytes, content_type: str = "text/plain") -> UploadFile:
    return UploadFile(
        BytesIO(content),
        filename=filename,
        headers=Headers({"content-type": content_type}),
    )


def test_normalize_filename_prevents_path_traversal() -> None:
    assert normalize_filename("../secret/../../policy draft.md") == "policy_draft.md"
    assert normalize_filename(r"..\\secret\\report.pdf") == "report.pdf"
    assert normalize_filename("../secret/政策报告.pdf") == "政策报告.pdf"
    assert normalize_filename("\x00\x1f") == "upload.bin"
    assert normalize_filename("a" * 220 + ".pdf").endswith(".pdf")
    assert len(normalize_filename("a" * 220 + ".pdf")) <= 180


def test_normalize_filename_preserves_unicode_names_and_extensions() -> None:
    assert normalize_filename("政策报告.pdf") == "政策报告.pdf"
    assert normalize_filename("关于新能源消纳的通知.docx").endswith(".docx")
    assert normalize_filename("国家能源局文件.txt") == "国家能源局文件.txt"
    assert normalize_filename("Résumé énergie.pdf") == "Résumé_énergie.pdf"


def test_validate_upload_extension_accepts_supported_extensions() -> None:
    allowed = {".pdf", ".docx", ".txt", ".md", ".html"}

    assert validate_upload_extension("report.PDF", allowed) == ".pdf"
    assert validate_upload_extension("brief.docx", allowed) == ".docx"
    assert validate_upload_extension("notes.txt", allowed) == ".txt"
    assert validate_upload_extension("memo.md", allowed) == ".md"
    assert validate_upload_extension("page.html", allowed) == ".html"


def test_validate_upload_extension_rejects_unsupported_extensions() -> None:
    with pytest.raises(UploadExtensionError):
        validate_upload_extension("runner.exe", {".pdf", ".txt"})


def test_save_upload_file_writes_chunks_and_calculates_sha256(tmp_path) -> None:
    content = b"policy evidence\nwith two lines\n"
    stored = save_upload_file(
        upload_file=make_upload("policy.txt", content),
        storage_root=tmp_path,
        project_id="project-1",
        document_id="document-1",
        max_size_bytes=1024,
        allowed_extensions={".txt"},
    )

    assert stored.storage_key == "documents/project-1/document-1/policy.txt"
    assert stored.absolute_path.read_bytes() == content
    assert stored.file_size == len(content)
    assert stored.sha256 == sha256(content).hexdigest()
    assert stored.file_name == "policy.txt"
    assert stored.file_type == ".txt"
    assert stored.content_type == "text/plain"


def test_save_upload_file_accepts_unicode_filename(tmp_path) -> None:
    content = "政策原文".encode()
    stored = save_upload_file(
        upload_file=make_upload("政策报告.pdf", content, "application/pdf"),
        storage_root=tmp_path,
        project_id="project-1",
        document_id="document-1",
        max_size_bytes=1024,
        allowed_extensions={".pdf"},
    )

    assert stored.storage_key == "documents/project-1/document-1/政策报告.pdf"
    assert stored.absolute_path.read_bytes() == content
    assert stored.file_name == "政策报告.pdf"
    assert stored.original_filename == "政策报告.pdf"
    assert stored.file_type == ".pdf"


def test_save_upload_file_rejects_empty_file_and_cleans_tmp(tmp_path) -> None:
    with pytest.raises(EmptyUploadError):
        save_upload_file(
            upload_file=make_upload("empty.txt", b""),
            storage_root=tmp_path,
            project_id="project-1",
            document_id="document-1",
            max_size_bytes=1024,
            allowed_extensions={".txt"},
        )

    assert list(tmp_path.rglob("*")) == []


def test_save_upload_file_rejects_oversized_file_and_cleans_tmp(tmp_path) -> None:
    with pytest.raises(UploadTooLargeError):
        save_upload_file(
            upload_file=make_upload("large.txt", b"abcdef"),
            storage_root=tmp_path,
            project_id="project-1",
            document_id="document-1",
            max_size_bytes=3,
            allowed_extensions={".txt"},
        )

    assert list(tmp_path.rglob("*")) == []
