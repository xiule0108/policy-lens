from __future__ import annotations

from uuid import UUID

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.models import AnalysisJob as AnalysisJobModel
from app.db.models import AnalysisResult as AnalysisResultModel
from app.db.models import AnalysisStep as AnalysisStepModel
from app.db.models import Claim as ClaimModel
from app.db.models import ImpactItem as ImpactItemModel
from app.db.models import PolicyMatch as PolicyMatchModel
from app.db.session import get_session
from app.repositories.analysis_jobs import create_analysis_job as repo_create_analysis_job
from app.repositories.analysis_jobs import get_analysis_job as repo_get_analysis_job
from app.repositories.analysis_jobs import list_analysis_jobs as repo_list_analysis_jobs
from app.repositories.analysis_results import get_analysis_result_by_job_id
from app.repositories.analysis_steps import get_analysis_step_by_step_id, list_analysis_steps
from app.repositories.claims import list_claims
from app.repositories.documents import get_document
from app.repositories.impact_items import list_impact_items
from app.repositories.policy_matches import list_policy_matches
from app.repositories.projects import get_project
from app.research.plan_builder import build_research_plan
from app.research.plan_executor import execute_research_plan
from app.schemas.common import (
    AnalysisClaimListResponse,
    AnalysisClaimResponse,
    AnalysisEvidenceResponse,
    AnalysisJobListResponse,
    AnalysisJobRequest,
    AnalysisJobResponse,
    AnalysisReportResponse,
    AnalysisResultResponse,
    AnalysisStepListResponse,
    AnalysisStepResponse,
    ImpactItemResponse,
    ImpactMatrixResponse,
    PolicyMatchListResponse,
    PolicyMatchResponse,
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


@router.get("/jobs", response_model=AnalysisJobListResponse)
def list_analysis_job_records(
    project_id: UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    session: Session = Depends(get_session),
) -> AnalysisJobListResponse:
    if project_id is not None and get_project(session, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    jobs = repo_list_analysis_jobs(session, project_id=project_id, limit=limit, offset=offset)
    return AnalysisJobListResponse(
        items=[
            _to_job_response(
                job,
                result_id=str(result.id) if (result := get_analysis_result_by_job_id(session, job.id)) else None,
            )
            for job in jobs
        ]
    )


@router.get("/jobs/{job_id}", response_model=AnalysisJobResponse)
def get_analysis_job(job_id: UUID, session: Session = Depends(get_session)) -> AnalysisJobResponse:
    job = repo_get_analysis_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Analysis job not found.")
    result = get_analysis_result_by_job_id(session, job.id)
    return _to_job_response(job, result_id=str(result.id) if result else None)


@router.get("/jobs/{job_id}/steps", response_model=AnalysisStepListResponse)
def get_analysis_job_steps(job_id: UUID, session: Session = Depends(get_session)) -> AnalysisStepListResponse:
    job = repo_get_analysis_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Analysis job not found.")
    return AnalysisStepListResponse(items=[_to_step_response(step) for step in list_analysis_steps(session, job.id)])


@router.get("/jobs/{job_id}/plan")
def get_analysis_job_plan(job_id: UUID, session: Session = Depends(get_session)) -> dict:
    job = repo_get_analysis_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Analysis job not found.")
    plan_step = get_analysis_step_by_step_id(session, job.id, "research_plan")
    if plan_step is None:
        raise HTTPException(status_code=404, detail="Research plan not found.")
    return plan_step.output_ref.get("plan", {})


@router.get("/jobs/{job_id}/result", response_model=AnalysisResultResponse)
def get_analysis_job_result(job_id: UUID, session: Session = Depends(get_session)) -> AnalysisResultResponse:
    job = repo_get_analysis_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Analysis job not found.")
    result = get_analysis_result_by_job_id(session, job.id)
    if result is None:
        raise HTTPException(status_code=404, detail="Analysis result not found.")
    return _to_result_response(result)


@router.get("/jobs/{job_id}/claims", response_model=AnalysisClaimListResponse)
def get_analysis_job_claims(job_id: UUID, session: Session = Depends(get_session)) -> AnalysisClaimListResponse:
    job = repo_get_analysis_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Analysis job not found.")
    if job.document_id is None:
        return AnalysisClaimListResponse(items=[])
    claims = list_claims(session, document_id=job.document_id, limit=500)
    return AnalysisClaimListResponse(items=[_to_claim_response(claim) for claim in claims])


@router.get("/jobs/{job_id}/policy-matches", response_model=PolicyMatchListResponse)
def get_analysis_job_policy_matches(
    job_id: UUID,
    session: Session = Depends(get_session),
) -> PolicyMatchListResponse:
    job = repo_get_analysis_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Analysis job not found.")
    result = get_analysis_result_by_job_id(session, job.id)
    if result is None:
        raise HTTPException(status_code=404, detail="Analysis result not found.")
    matches = list_policy_matches(session, analysis_id=result.id, limit=500)
    return PolicyMatchListResponse(items=[_to_policy_match_response(match) for match in matches])


@router.get("/jobs/{job_id}/evidence", response_model=AnalysisEvidenceResponse)
def get_analysis_job_evidence(job_id: UUID, session: Session = Depends(get_session)) -> AnalysisEvidenceResponse:
    job = repo_get_analysis_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Analysis job not found.")
    result = get_analysis_result_by_job_id(session, job.id)
    if result is None:
        raise HTTPException(status_code=404, detail="Analysis result not found.")
    report_json = result.report_json or {}
    return AnalysisEvidenceResponse(
        job_id=str(job.id),
        result_id=str(result.id),
        claim_policy_map=report_json.get("claim_policy_map", []),
        fact_boundaries=report_json.get("fact_boundaries", {}),
    )


@router.get("/jobs/{job_id}/impact-matrix", response_model=ImpactMatrixResponse)
def get_analysis_job_impact_matrix(job_id: UUID, session: Session = Depends(get_session)) -> ImpactMatrixResponse:
    job = repo_get_analysis_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Analysis job not found.")
    result = get_analysis_result_by_job_id(session, job.id)
    if result is None:
        raise HTTPException(status_code=404, detail="Analysis result not found.")
    items = list_impact_items(session, analysis_id=result.id, limit=500)
    return ImpactMatrixResponse(items=[_to_impact_item_response(item) for item in items])


@router.get("/jobs/{job_id}/report", response_model=AnalysisReportResponse)
def get_analysis_job_report(job_id: UUID, session: Session = Depends(get_session)) -> AnalysisReportResponse:
    job = repo_get_analysis_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Analysis job not found.")
    result = get_analysis_result_by_job_id(session, job.id)
    if result is None:
        raise HTTPException(status_code=404, detail="Analysis result not found.")
    report_json = result.report_json or {}
    return AnalysisReportResponse(
        job_id=str(job.id),
        result_id=str(result.id),
        report_markdown=result.report_markdown,
        report_outline=report_json.get("report_outline", {}),
        fact_boundaries=report_json.get("fact_boundaries", {}),
    )


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


def _to_claim_response(claim: ClaimModel) -> AnalysisClaimResponse:
    return AnalysisClaimResponse(
        id=str(claim.id),
        project_id=str(claim.project_id),
        document_id=str(claim.document_id),
        claim_text=claim.claim_text,
        claim_type=claim.claim_type,
        topic=claim.topic,
        industry=claim.industry,
        jurisdiction=claim.jurisdiction,
        confidence=float(claim.confidence) if claim.confidence is not None else None,
        source_chunk_ids=[str(chunk_id) for chunk_id in claim.source_chunk_ids],
        created_at=claim.created_at,
    )


def _to_policy_match_response(match: PolicyMatchModel) -> PolicyMatchResponse:
    return PolicyMatchResponse(
        id=str(match.id),
        project_id=str(match.project_id),
        analysis_id=str(match.analysis_id) if match.analysis_id else None,
        claim_id=str(match.claim_id),
        policy_id=str(match.policy_id),
        policy_section_id=str(match.policy_section_id) if match.policy_section_id else None,
        match_type=match.match_type,
        relevance_score=float(match.relevance_score) if match.relevance_score is not None else None,
        reason=match.reason,
        evidence=match.evidence,
        created_at=match.created_at,
    )


def _to_impact_item_response(item: ImpactItemModel) -> ImpactItemResponse:
    return ImpactItemResponse(
        id=str(item.id),
        project_id=str(item.project_id),
        analysis_id=str(item.analysis_id) if item.analysis_id else None,
        policy_id=str(item.policy_id) if item.policy_id else None,
        impact_subject=item.impact_subject,
        impact_direction=item.impact_direction,
        impact_horizon=item.impact_horizon,
        impact_mechanism=item.impact_mechanism,
        market_variable=item.market_variable,
        analysis_text=item.analysis_text,
        confidence=float(item.confidence) if item.confidence is not None else None,
        citations=item.citations,
        created_at=item.created_at,
    )
