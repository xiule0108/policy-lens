from __future__ import annotations

import time
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.base import utc_now
from app.repositories.analysis_jobs import get_analysis_job, update_analysis_job_status
from app.repositories.analysis_results import create_analysis_result
from app.repositories.analysis_steps import create_analysis_step, update_analysis_step
from app.research.plan_schema import ResearchPlan
from app.research.step_registry import get_step_handler


def execute_research_plan(session: Session, job_id: UUID | str, plan: ResearchPlan):
    job = get_analysis_job(session, job_id)
    if job is None:
        raise ValueError("Analysis job not found.")
    update_analysis_job_status(session, job_id, status="running", progress=0.05, started_at=utc_now())
    _record_plan_step(session, job_id, plan)

    step_outputs: dict[str, dict] = {}
    total_steps = len(plan.steps)
    try:
        for index, plan_step in enumerate(plan.steps, start=1):
            step_record = create_analysis_step(
                session,
                {
                    "job_id": job_id,
                    "step_id": plan_step.step_id,
                    "tool_name": plan_step.tool_name,
                    "status": "running",
                    "input_ref": plan_step.input_ref,
                },
            )
            started = time.perf_counter()
            try:
                result = get_step_handler(plan_step.tool_name)(session, plan, step_outputs)
                latency_ms = max(0, int((time.perf_counter() - started) * 1000))
                status = "skipped" if result.output_ref.get("skipped_reason") else "done"
                update_analysis_step(
                    session,
                    step_record.id,
                    status=status,
                    output_ref=result.output_ref,
                    token_usage=result.token_usage,
                    latency_ms=latency_ms,
                    model_provider=result.model_provider,
                    model_name=result.model_name,
                )
                step_outputs[plan_step.step_id] = result.output_ref
                update_analysis_job_status(
                    session,
                    job_id,
                    status="running",
                    progress=min(0.95, 0.1 + (index / total_steps) * 0.8),
                )
            except Exception as exc:
                update_analysis_step(
                    session,
                    step_record.id,
                    status="failed",
                    error_message=_short_error(exc),
                    latency_ms=max(0, int((time.perf_counter() - started) * 1000)),
                )
                update_analysis_job_status(
                    session,
                    job_id,
                    status="failed",
                    progress=min(0.95, 0.1 + (index / total_steps) * 0.8),
                    error_message=_short_error(exc),
                    finished_at=utc_now(),
                )
                raise
        result = _persist_result(session, job_id, plan, step_outputs)
        update_analysis_job_status(session, job_id, status="completed", progress=1.0, finished_at=utc_now())
        return result
    except Exception:
        raise


def _record_plan_step(session: Session, job_id, plan: ResearchPlan) -> None:
    create_analysis_step(
        session,
        {
            "job_id": job_id,
            "step_id": "research_plan",
            "tool_name": "plan_builder",
            "status": "done",
            "input_ref": {"project_id": plan.project_id, "document_id": plan.document_id, "mode": plan.mode},
            "output_ref": {"plan": plan.model_dump(mode="json")},
        },
    )


def _persist_result(session: Session, job_id, plan: ResearchPlan, step_outputs: dict[str, dict]):
    summary_output = step_outputs.get("summarize_findings", {})
    return create_analysis_result(
        session,
        {
            "project_id": plan.project_id,
            "job_id": job_id,
            "summary": summary_output.get("summary", {}),
            "claims": summary_output.get("claims", []),
            "related_policies": summary_output.get("related_policies", []),
            "impact_matrix": summary_output.get("impact_matrix", []),
            "report_json": {
                "research_plan": plan.model_dump(mode="json"),
                "step_outputs": step_outputs,
                "fact_boundaries": summary_output.get(
                    "fact_boundaries",
                    {"original_facts": [], "retrieved_facts": [], "model_reasoning": []},
                ),
            },
        },
    )


def _short_error(exc: Exception) -> str:
    return str(exc)[:500] or type(exc).__name__
