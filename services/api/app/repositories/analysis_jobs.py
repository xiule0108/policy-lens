from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AnalysisJob
from app.repositories._utils import coerce_optional_uuid, coerce_uuid


def create_analysis_job(session: Session, data: dict) -> AnalysisJob:
    job = AnalysisJob(
        project_id=coerce_uuid(data["project_id"]),
        document_id=coerce_optional_uuid(data.get("document_id")),
        mode=data["mode"],
        status=data.get("status", "queued"),
        model_profile=data.get("model_profile"),
        progress=data.get("progress", 0),
        error_message=data.get("error_message"),
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def get_analysis_job(session: Session, job_id: uuid.UUID | str) -> AnalysisJob | None:
    return session.get(AnalysisJob, coerce_uuid(job_id))


def list_analysis_jobs(
    session: Session,
    project_id: uuid.UUID | str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[AnalysisJob]:
    statement = select(AnalysisJob).order_by(AnalysisJob.created_at.desc()).limit(limit).offset(offset)
    if project_id is not None:
        statement = statement.where(AnalysisJob.project_id == coerce_uuid(project_id))
    return list(session.scalars(statement))


def update_analysis_job_status(
    session: Session,
    job_id: uuid.UUID | str,
    *,
    status: str,
    progress: float | Decimal | None = None,
    error_message: str | None = None,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
) -> AnalysisJob | None:
    job = get_analysis_job(session, job_id)
    if job is None:
        return None
    job.status = status
    if progress is not None:
        job.progress = Decimal(str(progress))
    if error_message is not None:
        job.error_message = error_message
    if started_at is not None:
        job.started_at = started_at
    if finished_at is not None:
        job.finished_at = finished_at
    session.commit()
    session.refresh(job)
    return job
