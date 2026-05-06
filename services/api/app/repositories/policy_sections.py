from __future__ import annotations

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.db.models import PolicySection
from app.repositories._utils import coerce_uuid


def create_policy_sections(session: Session, sections: list[dict]) -> list[PolicySection]:
    records = [
        PolicySection(
            policy_id=coerce_uuid(section["policy_id"]),
            version_id=coerce_uuid(section["version_id"]),
            section_path=section.get("section_path"),
            heading=section.get("heading"),
            content=section["content"],
            order_index=section["order_index"],
            token_count=section.get("token_count"),
            metadata_=section.get("metadata", {}),
        )
        for section in sections
    ]
    session.add_all(records)
    session.commit()
    for record in records:
        session.refresh(record)
    return records


def delete_policy_sections(session: Session, version_id: uuid.UUID | str) -> None:
    statement = delete(PolicySection).where(PolicySection.version_id == coerce_uuid(version_id))
    session.execute(statement)
    session.commit()


def list_policy_sections(
    session: Session,
    policy_id: uuid.UUID | str,
    version_id: uuid.UUID | str | None = None,
    limit: int = 200,
    offset: int = 0,
) -> list[PolicySection]:
    statement = select(PolicySection).where(PolicySection.policy_id == coerce_uuid(policy_id))
    if version_id is not None:
        statement = statement.where(PolicySection.version_id == coerce_uuid(version_id))
    statement = statement.order_by(PolicySection.order_index.asc()).limit(limit).offset(offset)
    return list(session.scalars(statement))


def count_policy_sections(
    session: Session,
    policy_id: uuid.UUID | str,
    version_id: uuid.UUID | str | None = None,
) -> int:
    statement = select(func.count()).select_from(PolicySection).where(PolicySection.policy_id == coerce_uuid(policy_id))
    if version_id is not None:
        statement = statement.where(PolicySection.version_id == coerce_uuid(version_id))
    return int(session.scalar(statement) or 0)
