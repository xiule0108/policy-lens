from __future__ import annotations

import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models import Policy
from app.repositories._utils import coerce_optional_uuid, coerce_uuid


def create_policy(session: Session, data: dict) -> Policy:
    policy = Policy(
        source_id=coerce_optional_uuid(data.get("source_id")),
        title=data["title"],
        normalized_title=data.get("normalized_title"),
        issuer=data.get("issuer"),
        issuer_level=data.get("issuer_level"),
        jurisdiction=data.get("jurisdiction"),
        policy_type=data.get("policy_type"),
        publish_date=data.get("publish_date"),
        effective_date=data.get("effective_date"),
        expiry_date=data.get("expiry_date"),
        status=data.get("status", "unknown"),
        source_url=data.get("source_url"),
        sha256=data.get("sha256"),
        metadata_=data.get("metadata", {}),
    )
    session.add(policy)
    session.commit()
    session.refresh(policy)
    return policy


def get_policy(session: Session, policy_id: uuid.UUID | str) -> Policy | None:
    return session.get(Policy, coerce_uuid(policy_id))


def list_policies(session: Session, limit: int = 50, offset: int = 0) -> list[Policy]:
    statement = select(Policy).order_by(Policy.created_at.desc()).limit(limit).offset(offset)
    return list(session.scalars(statement))


def search_policies_by_keyword(session: Session, query: str, limit: int = 20) -> list[Policy]:
    like_query = f"%{query.strip()}%"
    statement = (
        select(Policy)
        .where(
            or_(
                Policy.title.ilike(like_query),
                Policy.normalized_title.ilike(like_query),
                Policy.issuer.ilike(like_query),
            )
        )
        .order_by(Policy.created_at.desc())
        .limit(limit)
    )
    return list(session.scalars(statement))
