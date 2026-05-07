from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Claim
from app.repositories._utils import coerce_uuid


def create_claim(session: Session, data: dict) -> Claim:
    return create_claims(session, [data])[0]


def create_claims(session: Session, claims: list[dict]) -> list[Claim]:
    records: list[Claim] = []
    batch_seen: dict[tuple[uuid.UUID, str], Claim] = {}
    for claim in claims:
        document_id = coerce_uuid(claim["document_id"])
        claim_text = str(claim["claim_text"]).strip()
        key = (document_id, claim_text)
        if key in batch_seen:
            records.append(batch_seen[key])
            continue
        existing = _get_claim_by_document_and_text(session, document_id, claim_text)
        if existing is not None:
            batch_seen[key] = existing
            records.append(existing)
            continue
        record = Claim(
            project_id=coerce_uuid(claim["project_id"]),
            document_id=document_id,
            claim_text=claim_text,
            claim_type=claim["claim_type"],
            topic=claim.get("topic"),
            industry=claim.get("industry"),
            jurisdiction=claim.get("jurisdiction"),
            confidence=_coerce_decimal(claim.get("confidence")),
            source_chunk_ids=claim.get("source_chunk_ids", []),
        )
        session.add(record)
        session.flush()
        batch_seen[key] = record
        records.append(record)
    session.commit()
    for record in records:
        session.refresh(record)
    return records


def get_claim(session: Session, claim_id: uuid.UUID | str) -> Claim | None:
    return session.get(Claim, coerce_uuid(claim_id))


def list_claims(
    session: Session,
    project_id: uuid.UUID | str | None = None,
    document_id: uuid.UUID | str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Claim]:
    statement = select(Claim).order_by(Claim.created_at.asc(), Claim.id.asc()).limit(limit).offset(offset)
    if project_id is not None:
        statement = statement.where(Claim.project_id == coerce_uuid(project_id))
    if document_id is not None:
        statement = statement.where(Claim.document_id == coerce_uuid(document_id))
    return list(session.scalars(statement))


def delete_claims_for_document(session: Session, document_id: uuid.UUID | str) -> None:
    for claim in list_claims(session, document_id=document_id, limit=10_000):
        session.delete(claim)
    session.commit()


def _get_claim_by_document_and_text(session: Session, document_id: uuid.UUID, claim_text: str) -> Claim | None:
    statement = select(Claim).where(Claim.document_id == document_id, Claim.claim_text == claim_text).limit(1)
    return session.scalar(statement)


def _coerce_decimal(value) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))
