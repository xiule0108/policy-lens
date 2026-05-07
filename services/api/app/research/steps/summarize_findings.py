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
    retrieval = step_outputs.get("retrieve_policy_candidates", {})
    document = context.get("document", {})
    candidates = retrieval.get("candidates", [])
    summary = {
        "document_title": document.get("title"),
        "document_language": document.get("language"),
        "chunk_count": context.get("chunk_count", 0),
        "summary_fallback": signals.get("summary_fallback", ""),
        "policy_candidate_count": len(candidates),
    }
    claims = [
        {
            "claim_text": term,
            "claim_type": "signal",
            "source": "deterministic_extractor",
            "evidence": [{"source_type": "document_context", "document_id": plan.document_id}],
        }
        for term in signals.get("policy_terms") or signals.get("keywords", [])[:5]
    ]
    fact_boundaries = {
        "original_facts": [
            {
                "source": "document",
                "document_id": plan.document_id,
                "summary": signals.get("summary_fallback", ""),
            }
        ],
        "retrieved_facts": [
            {
                "source": "policy_candidate",
                "policy_id": candidate["policy_id"],
                "title": candidate["title"],
                "score": candidate["score"],
            }
            for candidate in candidates
        ],
        "model_reasoning": [],
    }
    return StepRunResult(
        output_ref={
            "summary": summary,
            "claims": claims,
            "related_policies": candidates,
            "impact_matrix": [],
            "fact_boundaries": fact_boundaries,
        }
    )
