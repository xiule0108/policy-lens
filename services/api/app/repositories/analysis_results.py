from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AnalysisResult
from app.repositories._utils import coerce_uuid


def create_analysis_result(session: Session, data: dict) -> AnalysisResult:
    result = AnalysisResult(
        project_id=coerce_uuid(data["project_id"]),
        job_id=coerce_uuid(data["job_id"]),
        summary=data.get("summary", {}),
        claims=data.get("claims", []),
        related_policies=data.get("related_policies", []),
        impact_matrix=data.get("impact_matrix", []),
        report_markdown=data.get("report_markdown"),
        report_json=data.get("report_json", {}),
    )
    session.add(result)
    session.commit()
    session.refresh(result)
    return result


def get_analysis_result(session: Session, result_id: uuid.UUID | str) -> AnalysisResult | None:
    return session.get(AnalysisResult, coerce_uuid(result_id))


def get_analysis_result_by_job_id(session: Session, job_id: uuid.UUID | str) -> AnalysisResult | None:
    statement = (
        select(AnalysisResult)
        .where(AnalysisResult.job_id == coerce_uuid(job_id))
        .order_by(AnalysisResult.created_at.desc())
        .limit(1)
    )
    return session.scalar(statement)


def update_analysis_result(session: Session, result_id: uuid.UUID | str, data: dict) -> AnalysisResult | None:
    result = get_analysis_result(session, result_id)
    if result is None:
        return None
    allowed_fields = {
        "summary",
        "claims",
        "related_policies",
        "impact_matrix",
        "report_markdown",
        "report_json",
    }
    for key, value in data.items():
        if key in allowed_fields:
            setattr(result, key, value)
    session.commit()
    session.refresh(result)
    return result
