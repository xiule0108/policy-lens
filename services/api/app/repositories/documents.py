from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Document
from app.repositories._utils import coerce_uuid


def create_document(session: Session, data: dict) -> Document:
    document_data = {
        "project_id": coerce_uuid(data["project_id"]),
        "document_role": data["document_role"],
        "title": data.get("title"),
        "file_name": data["file_name"],
        "file_type": data["file_type"],
        "file_size": data.get("file_size"),
        "storage_key": data.get("storage_key"),
        "language": data.get("language"),
        "page_count": data.get("page_count"),
        "parse_status": data.get("parse_status", "pending"),
        "source_url": data.get("source_url"),
        "sha256": data.get("sha256"),
        "metadata_": data.get("metadata", {}),
    }
    if data.get("id") is not None:
        document_data["id"] = coerce_uuid(data["id"])
    document = Document(**document_data)
    session.add(document)
    session.commit()
    session.refresh(document)
    return document


def get_document(session: Session, document_id: uuid.UUID | str) -> Document | None:
    return session.get(Document, coerce_uuid(document_id))


def list_documents(
    session: Session,
    project_id: uuid.UUID | str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Document]:
    statement = select(Document).order_by(Document.created_at.desc()).limit(limit).offset(offset)
    if project_id is not None:
        statement = statement.where(Document.project_id == coerce_uuid(project_id))
    return list(session.scalars(statement))


def update_document_parse_status(
    session: Session,
    document_id: uuid.UUID | str,
    parse_status: str,
) -> Document | None:
    document = get_document(session, document_id)
    if document is None:
        return None
    document.parse_status = parse_status
    session.commit()
    session.refresh(document)
    return document


def update_document_after_parse(
    session: Session,
    document_id: uuid.UUID | str,
    *,
    parse_status: str,
    title: str | None = None,
    language: str | None = None,
    page_count: int | None = None,
    metadata_patch: dict | None = None,
) -> Document | None:
    document = get_document(session, document_id)
    if document is None:
        return None
    document.parse_status = parse_status
    if title is not None:
        document.title = title
    if language is not None:
        document.language = language
    if page_count is not None:
        document.page_count = page_count
    if metadata_patch:
        document.metadata_ = {
            **(document.metadata_ or {}),
            **metadata_patch,
        }
    session.commit()
    session.refresh(document)
    return document
