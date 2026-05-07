from __future__ import annotations

from sqlalchemy.orm import Session

from app.research.plan_schema import ResearchPlan, StepRunResult


def run_build_evidence_map(
    session: Session,
    plan: ResearchPlan,
    step_outputs: dict[str, dict],
) -> StepRunResult:
    claims = step_outputs.get("extract_claims", {}).get("claims", [])
    matches = step_outputs.get("match_policy_sections", {}).get("matches", [])
    matches_by_claim: dict[str, list[dict]] = {}
    for match in matches:
        matches_by_claim.setdefault(match["claim_id"], []).append(match)
    claim_policy_map = [
        {
            "claim_id": claim["claim_id"],
            "claim_text": claim["claim_text"],
            "claim_type": claim["claim_type"],
            "source_chunk_ids": claim.get("source_chunk_ids", []),
            "matches": matches_by_claim.get(claim["claim_id"], []),
        }
        for claim in claims
    ]
    fact_boundaries = {
        "original_facts": [
            {
                "source": "document_claim",
                "document_id": plan.document_id,
                "claim_id": claim["claim_id"],
                "claim_text": claim["claim_text"],
                "source_chunk_ids": claim.get("source_chunk_ids", []),
            }
            for claim in claims
        ],
        "retrieved_facts": [
            {
                "source": "policy_section_match",
                "claim_id": match["claim_id"],
                "policy_id": match["policy_id"],
                "policy_section_id": match.get("policy_section_id"),
                "evidence": match.get("evidence", {}),
            }
            for match in matches
        ],
        "model_reasoning": [],
    }
    return StepRunResult(
        output_ref={
            "claim_policy_map": claim_policy_map,
            "fact_boundaries": fact_boundaries,
        }
    )
