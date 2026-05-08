from __future__ import annotations

import copy
import time
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.base import utc_now
from app.db.models import PolicyMatch
from app.repositories.analysis_jobs import get_analysis_job, update_analysis_job_status
from app.repositories.analysis_results import create_analysis_result, update_analysis_result
from app.repositories.analysis_steps import create_analysis_step, update_analysis_step
from app.repositories.impact_items import create_impact_items
from app.repositories.policy_matches import create_policy_matches
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
        try:
            result = _persist_result(session, job_id, plan, step_outputs)
        except Exception as exc:
            update_analysis_job_status(
                session,
                job_id,
                status="failed",
                progress=0.95,
                error_message=_short_error(exc),
                finished_at=utc_now(),
            )
            raise
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
    impact_output = step_outputs.get("build_impact_matrix", {})
    report_output = step_outputs.get("draft_markdown_report", {})
    impact_matrix = impact_output.get("impact_matrix", [])
    report_json = {
        "research_plan": plan.model_dump(mode="json"),
        "step_outputs": step_outputs,
        "claim_policy_map": summary_output.get("claim_policy_map", []),
        "fact_boundaries": summary_output.get(
            "fact_boundaries",
            {"original_facts": [], "retrieved_facts": [], "model_reasoning": []},
        ),
        "report_outline": report_output.get("report_outline", {}),
    }
    result = create_analysis_result(
        session,
        {
            "project_id": plan.project_id,
            "job_id": job_id,
            "summary": summary_output.get("summary", {}),
            "claims": summary_output.get("claims", []),
            "related_policies": summary_output.get("related_policies", []),
            "impact_matrix": impact_matrix,
            "report_markdown": report_output.get("report_markdown"),
            "report_json": report_json,
        },
    )
    created_matches = _persist_policy_matches(
        session,
        result.id,
        step_outputs.get("match_policy_sections", {}).get("matches", []),
    )
    enriched_impact_matrix = _enrich_impact_matrix_with_policy_match_ids(impact_matrix, created_matches)
    if enriched_impact_matrix != impact_matrix:
        report_json = copy.deepcopy(report_json)
        report_json.setdefault("step_outputs", {}).setdefault("build_impact_matrix", {})[
            "impact_matrix"
        ] = enriched_impact_matrix
        result = update_analysis_result(
            session,
            result.id,
            {"impact_matrix": enriched_impact_matrix, "report_json": report_json},
        ) or result
    _persist_impact_items(session, result.id, enriched_impact_matrix)
    return result


def _persist_policy_matches(session: Session, analysis_id, matches: list[dict]) -> list[PolicyMatch]:
    if not matches:
        return []
    records = [{**match, "analysis_id": analysis_id} for match in matches]
    return create_policy_matches(session, records)


def _persist_impact_items(session: Session, analysis_id, items: list[dict]) -> None:
    if not items:
        return
    records = [{**item, "analysis_id": analysis_id} for item in items]
    create_impact_items(session, records)


def _enrich_impact_matrix_with_policy_match_ids(
    impact_matrix: list[dict], policy_matches: list[PolicyMatch]
) -> list[dict]:
    if not impact_matrix or not policy_matches:
        return impact_matrix
    match_lookup = {
        _match_key(str(match.claim_id), str(match.policy_id), _str_or_none(match.policy_section_id)): str(match.id)
        for match in policy_matches
    }
    enriched = copy.deepcopy(impact_matrix)
    for item in enriched:
        citations = item.get("citations") or []
        claim_citation = next((citation for citation in citations if citation.get("source_type") == "claim"), None)
        policy_citation = next(
            (citation for citation in citations if citation.get("source_type") == "policy_section"),
            None,
        )
        if not claim_citation or not policy_citation:
            continue
        policy_match_id = match_lookup.get(
            _match_key(
                _str_or_none(claim_citation.get("claim_id")),
                _str_or_none(policy_citation.get("policy_id")),
                _str_or_none(policy_citation.get("policy_section_id")),
            )
        )
        if policy_match_id:
            policy_citation["policy_match_id"] = policy_match_id
    return enriched


def _match_key(
    claim_id: str | None, policy_id: str | None, policy_section_id: str | None
) -> tuple[str | None, str | None, str | None]:
    return claim_id, policy_id, policy_section_id


def _str_or_none(value) -> str | None:
    return str(value) if value is not None else None


def _short_error(exc: Exception) -> str:
    return str(exc)[:500] or type(exc).__name__
