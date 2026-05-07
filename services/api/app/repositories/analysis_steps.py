from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AnalysisStep
from app.repositories._utils import coerce_uuid


def create_analysis_step(session: Session, data: dict) -> AnalysisStep:
    step = AnalysisStep(
        job_id=coerce_uuid(data["job_id"]),
        step_id=data["step_id"],
        tool_name=data.get("tool_name"),
        status=data.get("status", "pending"),
        model_provider=data.get("model_provider"),
        model_name=data.get("model_name"),
        input_ref=data.get("input_ref", {}),
        output_ref=data.get("output_ref", {}),
        token_usage=data.get("token_usage", {}),
        latency_ms=data.get("latency_ms"),
        error_message=data.get("error_message"),
    )
    session.add(step)
    session.commit()
    session.refresh(step)
    return step


def get_analysis_step_by_db_id(session: Session, step_id: uuid.UUID | str) -> AnalysisStep | None:
    return session.get(AnalysisStep, coerce_uuid(step_id))


def get_analysis_step(session: Session, step_id: uuid.UUID | str) -> AnalysisStep | None:
    return get_analysis_step_by_db_id(session, step_id)


def get_analysis_step_by_step_id(
    session: Session,
    job_id: uuid.UUID | str,
    step_id: str,
) -> AnalysisStep | None:
    statement = select(AnalysisStep).where(
        AnalysisStep.job_id == coerce_uuid(job_id),
        AnalysisStep.step_id == step_id,
    )
    return session.scalar(statement)


def list_analysis_steps(session: Session, job_id: uuid.UUID | str) -> list[AnalysisStep]:
    statement = (
        select(AnalysisStep)
        .where(AnalysisStep.job_id == coerce_uuid(job_id))
        .order_by(AnalysisStep.created_at.asc(), AnalysisStep.step_id.asc())
    )
    return list(session.scalars(statement))


def update_analysis_step(
    session: Session,
    step_db_id: uuid.UUID | str,
    *,
    status: str | None = None,
    output_ref: dict | None = None,
    token_usage: dict | None = None,
    latency_ms: int | None = None,
    error_message: str | None = None,
    model_provider: str | None = None,
    model_name: str | None = None,
) -> AnalysisStep | None:
    step = get_analysis_step_by_db_id(session, step_db_id)
    if step is None:
        return None
    if status is not None:
        step.status = status
    if output_ref is not None:
        step.output_ref = output_ref
    if token_usage is not None:
        step.token_usage = token_usage
    if latency_ms is not None:
        step.latency_ms = latency_ms
    if error_message is not None:
        step.error_message = error_message
    if model_provider is not None:
        step.model_provider = model_provider
    if model_name is not None:
        step.model_name = model_name
    session.commit()
    session.refresh(step)
    return step
