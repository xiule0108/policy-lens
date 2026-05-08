from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import ImpactItem
from app.repositories._utils import coerce_optional_uuid, coerce_uuid


def create_impact_item(session: Session, data: dict) -> ImpactItem:
    return create_impact_items(session, [data])[0]


def create_impact_items(session: Session, items: list[dict]) -> list[ImpactItem]:
    records = [
        ImpactItem(
            project_id=coerce_uuid(item["project_id"]),
            analysis_id=coerce_optional_uuid(item.get("analysis_id")),
            policy_id=coerce_optional_uuid(item.get("policy_id")),
            impact_subject=item.get("impact_subject"),
            impact_direction=item.get("impact_direction"),
            impact_horizon=item.get("impact_horizon"),
            impact_mechanism=item.get("impact_mechanism"),
            market_variable=item.get("market_variable"),
            analysis_text=item["analysis_text"],
            confidence=_coerce_decimal(item.get("confidence")),
            citations=item.get("citations", []),
        )
        for item in items
    ]
    session.add_all(records)
    session.commit()
    for record in records:
        session.refresh(record)
    return records


def get_impact_item(session: Session, impact_item_id: uuid.UUID | str) -> ImpactItem | None:
    return session.get(ImpactItem, coerce_uuid(impact_item_id))


def list_impact_items(
    session: Session,
    *,
    project_id: uuid.UUID | str | None = None,
    analysis_id: uuid.UUID | str | None = None,
    policy_id: uuid.UUID | str | None = None,
    impact_direction: str | None = None,
    impact_subject: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[ImpactItem]:
    statement = select(ImpactItem).order_by(ImpactItem.created_at.asc(), ImpactItem.id.asc()).limit(limit).offset(offset)
    if project_id is not None:
        statement = statement.where(ImpactItem.project_id == coerce_uuid(project_id))
    if analysis_id is not None:
        statement = statement.where(ImpactItem.analysis_id == coerce_uuid(analysis_id))
    if policy_id is not None:
        statement = statement.where(ImpactItem.policy_id == coerce_uuid(policy_id))
    if impact_direction:
        statement = statement.where(ImpactItem.impact_direction == impact_direction)
    if impact_subject:
        statement = statement.where(ImpactItem.impact_subject == impact_subject)
    return list(session.scalars(statement))


def delete_impact_items_for_analysis(session: Session, analysis_id: uuid.UUID | str) -> None:
    statement = delete(ImpactItem).where(ImpactItem.analysis_id == coerce_uuid(analysis_id))
    session.execute(statement)
    session.commit()


def _coerce_decimal(value) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))
