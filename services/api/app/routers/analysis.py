from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import AnalysisJob as AnalysisJobModel
from app.db.models import AnalysisResult as AnalysisResultModel
from app.db.models import AnalysisStep as AnalysisStepModel
from app.db.session import get_session
from app.repositories.analysis_jobs import create_analysis_job as repo_create_analysis_job
from app.repositories.analysis_jobs import get_analysis_job as repo_get_analysis_job
from app.repositories.analysis_results import get_analysis_result_by_job_id
from app.repositories.analysis_steps import get_analysis_step_by_step_id, list_analysis_steps
from app.repositories.documents import get_document
from app.repositories.projects import get_project
from app.research.plan_builder import build_research_plan
from app.research.plan_executor import execute_research_plan
from app.schemas.common import (
    AnalysisJobRequest,
    AnalysisJobResponse,
    AnalysisResultResponse,
    AnalysisStepListResponse,
    AnalysisStepResponse,
)

router = APIRouter()


@router.post("/jobs", response_model=AnalysisJobResponse, status_code=201)
def create_analysis_job(
    payload: AnalysisJobRequest,
    session: Session = Depends(get_session),
) -> AnalysisJobResponse:
    project = get_project(session, payload.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    if not payload.document_ids:
        raise HTTPException(status_code=422, detail="document_ids must contain at least one document id.")
    document = get_document(session, payload.document_ids[0])
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    if document.project_id != project.id:
        raise HTTPException(status_code=409, detail="Document does not belong to the project.")

    mode = payload.analysis_types[0] if payload.analysis_types else "policy_deep_dive"
    job = repo_create_analysis_job(
        session,
        {
            "project_id": project.id,
            "document_id": document.id,
            "mode": mode,
            "status": "queued",
            "model_profile": payload.model_profile,
            "progress": 0,
        },
    )
    try:
        plan = build_research_plan(payload)
        result = execute_research_plan(session, job.id, plan)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)[:500] or type(exc).__name__) from exc

    refreshed = repo_get_analysis_job(session, job.id) or job
    return _to_job_response(refreshed, result_id=str(result.id))


@router.get("/jobs/{job_id}", response_model=AnalysisJobResponse)
def get_analysis_job(job_id: str, session: Session = Depends(get_session)) -> AnalysisJobResponse:
    job = repo_get_analysis_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Analysis job not found.")
    result = get_analysis_result_by_job_id(session, job.id)
    return _to_job_response(job, result_id=str(result.id) if result else None)


@router.get("/jobs/{job_id}/steps", response_model=AnalysisStepListResponse)
def get_analysis_job_steps(job_id: str, session: Session = Depends(get_session)) -> AnalysisStepListResponse:
    job = repo_get_analysis_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Analysis job not found.")
    return AnalysisStepListResponse(items=[_to_step_response(step) for step in list_analysis_steps(session, job.id)])


@router.get("/jobs/{job_id}/plan")
def get_analysis_job_plan(job_id: str, session: Session = Depends(get_session)) -> dict:
    job = repo_get_analysis_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Analysis job not found.")
    plan_step = get_analysis_step_by_step_id(session, job.id, "research_plan")
    if plan_step is None:
        raise HTTPException(status_code=404, detail="Research plan not found.")
    return plan_step.output_ref.get("plan", {})


@router.get("/jobs/{job_id}/result", response_model=AnalysisResultResponse)
def get_analysis_job_result(job_id: str, session: Session = Depends(get_session)) -> AnalysisResultResponse:
    job = repo_get_analysis_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Analysis job not found.")
    result = get_analysis_result_by_job_id(session, job.id)
    if result is None:
        raise HTTPException(status_code=404, detail="Analysis result not found.")
    return _to_result_response(result)


def _to_job_response(job: AnalysisJobModel, result_id: str | None = None) -> AnalysisJobResponse:
    return AnalysisJobResponse(
        id=str(job.id),
        project_id=str(job.project_id),
        document_id=str(job.document_id) if job.document_id else None,
        status=job.status,
        mode=job.mode,
        model_profile=job.model_profile,
        progress=float(job.progress),
        result_id=result_id,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )


def _to_step_response(step: AnalysisStepModel) -> AnalysisStepResponse:
    return AnalysisStepResponse(
        id=str(step.id),
        job_id=str(step.job_id),
        step_id=step.step_id,
        tool_name=step.tool_name,
        status=step.status,
        model_provider=step.model_provider,
        model_name=step.model_name,
        input_ref=step.input_ref,
        output_ref=step.output_ref,
        token_usage=step.token_usage,
        latency_ms=step.latency_ms,
        error_message=step.error_message,
        created_at=step.created_at,
        updated_at=step.updated_at,
    )


def _to_result_response(result: AnalysisResultModel) -> AnalysisResultResponse:
    return AnalysisResultResponse(
        id=str(result.id),
        project_id=str(result.project_id),
        job_id=str(result.job_id),
        summary=result.summary,
        claims=result.claims,
        related_policies=result.related_policies,
        impact_matrix=result.impact_matrix,
        report_markdown=result.report_markdown,
        report_json=result.report_json,
        created_at=result.created_at,
    )
