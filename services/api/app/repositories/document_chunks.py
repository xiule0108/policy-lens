from __future__ import annotations

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.db.models import DocumentChunk
from app.repositories._utils import coerce_uuid


def create_document_chunks(session: Session, chunks: list[dict]) -> list[DocumentChunk]:
    records = [
        DocumentChunk(
            document_id=coerce_uuid(chunk["document_id"]),
            project_id=coerce_uuid(chunk["project_id"]),
            chunk_index=chunk["chunk_index"],
            page_start=chunk.get("page_start"),
            page_end=chunk.get("page_end"),
            section_title=chunk.get("section_title"),
            content=chunk["content"],
            content_type=chunk.get("content_type", "paragraph"),
            token_count=chunk.get("token_count"),
            metadata_=chunk.get("metadata", {}),
        )
        for chunk in chunks
    ]
    session.add_all(records)
    session.commit()
    for record in records:
        session.refresh(record)
    return records


def delete_document_chunks(session: Session, document_id: uuid.UUID | str) -> None:
    statement = delete(DocumentChunk).where(DocumentChunk.document_id == coerce_uuid(document_id))
    session.execute(statement)
    session.commit()


def list_document_chunks(
    session: Session,
    document_id: uuid.UUID | str,
    limit: int = 200,
    offset: int = 0,
) -> list[DocumentChunk]:
    statement = (
        select(DocumentChunk)
        .where(DocumentChunk.document_id == coerce_uuid(document_id))
        .order_by(DocumentChunk.chunk_index.asc())
        .limit(limit)
        .offset(offset)
    )
    return list(session.scalars(statement))


def count_document_chunks(session: Session, document_id: uuid.UUID | str) -> int:
    statement = select(func.count()).select_from(DocumentChunk).where(DocumentChunk.document_id == coerce_uuid(document_id))
    return int(session.scalar(statement) or 0)
