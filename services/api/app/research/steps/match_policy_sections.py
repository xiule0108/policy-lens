from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.claims import get_claim
from app.research.plan_schema import ResearchPlan, StepRunResult
from app.services.policy_matching_service import match_claims_to_policy_sections


def run_match_policy_sections(
    session: Session,
    plan: ResearchPlan,
    step_outputs: dict[str, dict],
) -> StepRunResult:
    claim_refs = step_outputs.get("extract_claims", {}).get("claims", [])
    claims = []
    for claim_ref in claim_refs:
        claim = get_claim(session, claim_ref["claim_id"])
        if claim is not None:
            claims.append(claim)
    matches = match_claims_to_policy_sections(session, claims, limit_per_claim=5)
    return StepRunResult(
        output_ref={
            "match_count": len(matches),
            "matches": matches,
        }
    )
