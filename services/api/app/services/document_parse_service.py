from __future__ import annotations

from dataclasses import dataclass
from datetime import timezone
from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.base import utc_now
from app.db.config import settings
from app.repositories.document_chunks import create_document_chunks, delete_document_chunks
from app.repositories.documents import get_document, update_document_after_parse
from app.services.chunking_service import build_document_chunks
from app.services.document_parser import EmptyParsedDocumentError, parse_document_file
from app.services.storage_service import StorageError, resolve_storage_path


class DocumentParseServiceError(Exception):
    """Base class for parse orchestration errors."""


class DocumentNotFoundError(DocumentParseServiceError):
    """Raised when a document row does not exist."""


class DocumentFileNotFoundError(DocumentParseServiceError):
    """Raised when a document file cannot be resolved or found."""


@dataclass(frozen=True)
class ParseDocumentResult:
    document_id: str
    parse_status: str
    chunk_count: int
    page_count: int | None
    language: str | None
    title: str | None
    error: str | None = None


def parse_error_metadata(exc: Exception) -> dict:
    return {
        "parse_error": {
            "type": type(exc).__name__,
            "message": str(exc),
            "occurred_at": utc_now().astimezone(timezone.utc).isoformat(),
        }
    }


def fail_document_parse(session: Session, document_id: UUID, exc: Exception) -> None:
    update_document_after_parse(
        session,
        document_id,
        parse_status="failed",
        metadata_patch=parse_error_metadata(exc),
    )


def parse_document_by_id(session: Session, document_id: UUID) -> ParseDocumentResult:
    document = get_document(session, document_id)
    if document is None:
        raise DocumentNotFoundError("Document not found.")
    if not document.storage_key:
        exc = DocumentFileNotFoundError("Document file not found.")
        fail_document_parse(session, document_id, exc)
        raise exc

    try:
        file_path = resolve_storage_path(Path(settings.storage_dir), document.storage_key)
    except StorageError as exc:
        parse_exc = DocumentFileNotFoundError("Document file not found.")
        fail_document_parse(session, document_id, parse_exc)
        raise parse_exc from exc
    if not file_path.exists() or not file_path.is_file():
        exc = DocumentFileNotFoundError("Document file not found.")
        fail_document_parse(session, document_id, exc)
        raise exc

    update_document_after_parse(session, document_id, parse_status="parsing", metadata_remove_keys=["parse_error"])

    try:
        parsed = parse_document_file(file_path, document.file_type)
        chunks = build_document_chunks(
            document_id=str(document.id),
            project_id=str(document.project_id),
            blocks=parsed.blocks,
            max_chars=settings.chunk_max_chars,
        )
        if not chunks:
            raise EmptyParsedDocumentError("No extractable text found.")
        delete_document_chunks(session, document.id)
        create_document_chunks(session, chunks)
        updated = update_document_after_parse(
            session,
            document.id,
            parse_status="parsed",
            title=parsed.title,
            language=parsed.language,
            page_count=parsed.page_count,
            metadata_remove_keys=["parse_error"],
            metadata_patch={
                "parse_summary": {
                    **parsed.metadata,
                    "chunk_count": len(chunks),
                }
            },
        )
        return ParseDocumentResult(
            document_id=str(document.id),
            parse_status=updated.parse_status if updated else "parsed",
            chunk_count=len(chunks),
            page_count=parsed.page_count,
            language=parsed.language,
            title=updated.title if updated else parsed.title,
        )
    except Exception as exc:
        fail_document_parse(session, document.id, exc)
        raise
