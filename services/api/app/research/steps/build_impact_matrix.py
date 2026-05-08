from __future__ import annotations

from sqlalchemy.orm import Session

from app.research.plan_schema import ResearchPlan, StepRunResult
from app.services.impact_matrix_service import build_impact_matrix


def run_build_impact_matrix(
    session: Session,
    plan: ResearchPlan,
    step_outputs: dict[str, dict],
) -> StepRunResult:
    claims = step_outputs.get("extract_claims", {}).get("claims", [])
    matches = step_outputs.get("match_policy_sections", {}).get("matches", [])
    claim_policy_map = step_outputs.get("build_evidence_map", {}).get("claim_policy_map", [])
    impact_matrix = build_impact_matrix(
        project_id=plan.project_id,
        analysis_id=None,
        claims=claims,
        policy_matches=matches,
        claim_policy_map=claim_policy_map,
    )
    return StepRunResult(
        output_ref={
            "impact_count": len(impact_matrix),
            "impact_matrix": impact_matrix,
        }
    )
