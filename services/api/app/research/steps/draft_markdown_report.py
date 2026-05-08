from __future__ import annotations

from sqlalchemy.orm import Session

from app.research.plan_schema import ResearchPlan, StepRunResult
from app.services.report_generation_service import generate_markdown_report


def run_draft_markdown_report(
    session: Session,
    plan: ResearchPlan,
    step_outputs: dict[str, dict],
) -> StepRunResult:
    summary_output = step_outputs.get("summarize_findings", {})
    report_markdown, report_outline = generate_markdown_report(
        summary=summary_output.get("summary", {}),
        claims=summary_output.get("claims", []),
        related_policies=summary_output.get("related_policies", []),
        policy_matches=summary_output.get("policy_matches", []),
        impact_matrix=summary_output.get("impact_matrix", []),
        fact_boundaries=summary_output.get("fact_boundaries", {}),
        claim_policy_map=summary_output.get("claim_policy_map", []),
    )
    return StepRunResult(
        output_ref={
            "report_markdown": report_markdown,
            "report_outline": report_outline,
        }
    )
