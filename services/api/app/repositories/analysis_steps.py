from __future__ import annotations

import uuid

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


def get_analysis_step(session: Session, step_id: uuid.UUID | str) -> AnalysisStep | None:
    return session.get(AnalysisStep, coerce_uuid(step_id))
