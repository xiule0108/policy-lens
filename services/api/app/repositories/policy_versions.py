from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.db.base import utc_now
from app.db.models import PolicyVersion
from app.repositories._utils import coerce_uuid


def create_policy_version(session: Session, data: dict) -> PolicyVersion:
    version = PolicyVersion(
        policy_id=coerce_uuid(data["policy_id"]),
        version_label=data.get("version_label"),
        source_url=data.get("source_url"),
        captured_at=data.get("captured_at") or utc_now(),
        normalized_text=data.get("normalized_text"),
        sha256=data.get("sha256"),
        is_current=data.get("is_current", True),
        metadata_=data.get("metadata", {}),
    )
    session.add(version)
    session.commit()
    session.refresh(version)
    return version


def get_policy_version(session: Session, version_id: uuid.UUID | str) -> PolicyVersion | None:
    return session.get(PolicyVersion, coerce_uuid(version_id))


def get_current_policy_version(session: Session, policy_id: uuid.UUID | str) -> PolicyVersion | None:
    statement = (
        select(PolicyVersion)
        .where(PolicyVersion.policy_id == coerce_uuid(policy_id), PolicyVersion.is_current.is_(True))
        .order_by(PolicyVersion.captured_at.desc(), PolicyVersion.created_at.desc())
        .limit(1)
    )
    return session.scalar(statement)


def list_policy_versions(
    session: Session,
    policy_id: uuid.UUID | str,
    limit: int = 50,
    offset: int = 0,
) -> list[PolicyVersion]:
    statement = (
        select(PolicyVersion)
        .where(PolicyVersion.policy_id == coerce_uuid(policy_id))
        .order_by(PolicyVersion.captured_at.desc(), PolicyVersion.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(session.scalars(statement))


def set_policy_versions_not_current(session: Session, policy_id: uuid.UUID | str) -> None:
    statement = (
        update(PolicyVersion)
        .where(PolicyVersion.policy_id == coerce_uuid(policy_id))
        .values(is_current=False)
    )
    session.execute(statement)
    session.commit()
