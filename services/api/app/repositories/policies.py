from __future__ import annotations

import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models import Policy
from app.repositories._utils import coerce_optional_uuid, coerce_uuid


def create_policy(session: Session, data: dict) -> Policy:
    policy_data = {
        "source_id": coerce_optional_uuid(data.get("source_id")),
        "title": data["title"],
        "normalized_title": data.get("normalized_title"),
        "issuer": data.get("issuer"),
        "issuer_level": data.get("issuer_level"),
        "jurisdiction": data.get("jurisdiction"),
        "policy_type": data.get("policy_type"),
        "publish_date": data.get("publish_date"),
        "effective_date": data.get("effective_date"),
        "expiry_date": data.get("expiry_date"),
        "status": data.get("status", "unknown"),
        "source_url": data.get("source_url"),
        "sha256": data.get("sha256"),
        "metadata_": data.get("metadata", {}),
    }
    if data.get("id") is not None:
        policy_data["id"] = coerce_uuid(data["id"])
    policy = Policy(**policy_data)
    session.add(policy)
    session.commit()
    session.refresh(policy)
    return policy


def get_policy(session: Session, policy_id: uuid.UUID | str) -> Policy | None:
    return session.get(Policy, coerce_uuid(policy_id))


def list_policies(
    session: Session,
    *,
    query: str | None = None,
    jurisdiction: str | None = None,
    issuer: str | None = None,
    policy_type: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Policy]:
    statement = select(Policy).order_by(Policy.created_at.desc()).limit(limit).offset(offset)
    if query:
        like_query = f"%{query.strip()}%"
        statement = statement.where(
            or_(
                Policy.title.ilike(like_query),
                Policy.normalized_title.ilike(like_query),
                Policy.issuer.ilike(like_query),
                Policy.jurisdiction.ilike(like_query),
                Policy.policy_type.ilike(like_query),
            )
        )
    if jurisdiction:
        statement = statement.where(Policy.jurisdiction.ilike(f"%{jurisdiction.strip()}%"))
    if issuer:
        statement = statement.where(Policy.issuer.ilike(f"%{issuer.strip()}%"))
    if policy_type:
        statement = statement.where(Policy.policy_type == policy_type)
    if status:
        statement = statement.where(Policy.status == status)
    return list(session.scalars(statement))


def search_policies_by_keyword(session: Session, query: str, limit: int = 20) -> list[Policy]:
    if not query.strip():
        return list_policies(session, limit=limit)
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


def update_policy(session: Session, policy_id: uuid.UUID | str, data: dict) -> Policy | None:
    policy = get_policy(session, policy_id)
    if policy is None:
        return None
    for key in (
        "title",
        "normalized_title",
        "issuer",
        "issuer_level",
        "jurisdiction",
        "policy_type",
        "publish_date",
        "effective_date",
        "expiry_date",
        "status",
        "source_url",
        "sha256",
    ):
        if key in data:
            setattr(policy, key, data[key])
    if "metadata" in data:
        policy.metadata_ = {
            **(policy.metadata_ or {}),
            **(data["metadata"] or {}),
        }
    session.commit()
    session.refresh(policy)
    return policy
