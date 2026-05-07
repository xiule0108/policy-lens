from __future__ import annotations

from sqlalchemy.orm import Session

from app.research.plan_schema import ResearchPlan, StepRunResult


def run_summarize_findings(
    session: Session,
    plan: ResearchPlan,
    step_outputs: dict[str, dict],
) -> StepRunResult:
    context = step_outputs.get("collect_document_context", {})
    signals = step_outputs.get("extract_article_signals", {})
    extracted_claims = step_outputs.get("extract_claims", {})
    retrieval = step_outputs.get("retrieve_policy_candidates", {})
    policy_matches = step_outputs.get("match_policy_sections", {})
    evidence_map = step_outputs.get("build_evidence_map", {})
    document = context.get("document", {})
    candidates = retrieval.get("candidates", [])
    claims = extracted_claims.get("claims", [])
    matches = policy_matches.get("matches", [])
    summary = {
        "document_title": document.get("title"),
        "document_language": document.get("language"),
        "chunk_count": context.get("chunk_count", 0),
        "summary_fallback": signals.get("summary_fallback", ""),
        "claim_count": len(claims),
        "policy_candidate_count": len(candidates),
        "policy_match_count": len(matches),
    }
    fact_boundaries = evidence_map.get(
        "fact_boundaries",
        {"original_facts": [], "retrieved_facts": [], "model_reasoning": []},
    )
    return StepRunResult(
        output_ref={
            "summary": summary,
            "claims": claims,
            "related_policies": candidates,
            "impact_matrix": [],
            "fact_boundaries": fact_boundaries,
            "claim_policy_map": evidence_map.get("claim_policy_map", []),
            "policy_matches": matches,
        }
    )
