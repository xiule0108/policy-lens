from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import PolicyMatch
from app.repositories._utils import coerce_optional_uuid, coerce_uuid


def create_policy_match(session: Session, data: dict) -> PolicyMatch:
    return create_policy_matches(session, [data])[0]


def create_policy_matches(session: Session, matches: list[dict]) -> list[PolicyMatch]:
    records = [
        PolicyMatch(
            project_id=coerce_uuid(match["project_id"]),
            analysis_id=coerce_optional_uuid(match.get("analysis_id")),
            claim_id=coerce_uuid(match["claim_id"]),
            policy_id=coerce_uuid(match["policy_id"]),
            policy_section_id=coerce_optional_uuid(match.get("policy_section_id")),
            match_type=match["match_type"],
            relevance_score=_coerce_decimal(match.get("relevance_score")),
            reason=match.get("reason"),
            evidence=match.get("evidence", {}),
        )
        for match in matches
    ]
    session.add_all(records)
    session.commit()
    for record in records:
        session.refresh(record)
    return records


def get_policy_match(session: Session, match_id: uuid.UUID | str) -> PolicyMatch | None:
    return session.get(PolicyMatch, coerce_uuid(match_id))


def list_policy_matches(
    session: Session,
    project_id: uuid.UUID | str | None = None,
    analysis_id: uuid.UUID | str | None = None,
    claim_id: uuid.UUID | str | None = None,
    policy_id: uuid.UUID | str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[PolicyMatch]:
    statement = select(PolicyMatch).order_by(PolicyMatch.created_at.asc(), PolicyMatch.id.asc()).limit(limit).offset(offset)
    if project_id is not None:
        statement = statement.where(PolicyMatch.project_id == coerce_uuid(project_id))
    if analysis_id is not None:
        statement = statement.where(PolicyMatch.analysis_id == coerce_uuid(analysis_id))
    if claim_id is not None:
        statement = statement.where(PolicyMatch.claim_id == coerce_uuid(claim_id))
    if policy_id is not None:
        statement = statement.where(PolicyMatch.policy_id == coerce_uuid(policy_id))
    return list(session.scalars(statement))


def delete_policy_matches_for_analysis(session: Session, analysis_id: uuid.UUID | str) -> None:
    statement = delete(PolicyMatch).where(PolicyMatch.analysis_id == coerce_uuid(analysis_id))
    session.execute(statement)
    session.commit()


def _coerce_decimal(value) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))
