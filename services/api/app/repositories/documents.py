from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Document
from app.repositories._utils import coerce_uuid


def create_document(session: Session, data: dict) -> Document:
    document = Document(
        project_id=coerce_uuid(data["project_id"]),
        document_role=data["document_role"],
        title=data.get("title"),
        file_name=data["file_name"],
        file_type=data["file_type"],
        file_size=data.get("file_size"),
        storage_key=data.get("storage_key"),
        language=data.get("language"),
        page_count=data.get("page_count"),
        parse_status=data.get("parse_status", "pending"),
        source_url=data.get("source_url"),
        sha256=data.get("sha256"),
        metadata_=data.get("metadata", {}),
    )
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
