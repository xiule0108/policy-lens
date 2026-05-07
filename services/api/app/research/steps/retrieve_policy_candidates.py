from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import PolicySection
from app.repositories.policies import list_policies
from app.repositories.policy_versions import get_current_policy_version
from app.research.plan_schema import ResearchPlan, StepRunResult


def run_retrieve_policy_candidates(
    session: Session,
    plan: ResearchPlan,
    step_outputs: dict[str, dict],
) -> StepRunResult:
    signals = step_outputs.get("extract_article_signals", {})
    terms = _candidate_terms(signals)
    candidates = []
    for policy in list_policies(session, limit=100):
        version = get_current_policy_version(session, policy.id)
        sections = _policy_sections(session, policy.id, version.id if version else None)
        score, matched_terms, section_refs = _score_policy(policy, sections, terms)
        if score <= 0:
            continue
        candidates.append(
            {
                "policy_id": str(policy.id),
                "title": policy.title,
                "issuer": policy.issuer,
                "jurisdiction": policy.jurisdiction,
                "policy_type": policy.policy_type,
                "current_version_id": str(version.id) if version else None,
                "matched_terms": matched_terms,
                "score": score,
                "section_refs": section_refs,
            }
        )
    candidates.sort(key=lambda item: item["score"], reverse=True)
    return StepRunResult(output_ref={"candidates": candidates[:20]})


def _candidate_terms(signals: dict) -> list[str]:
    terms = []
    for key in ("policy_terms", "keywords", "jurisdictions", "years"):
        terms.extend(signals.get(key, []))
    seen = set()
    unique_terms = []
    for term in terms:
        normalized = str(term).strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique_terms.append(normalized)
    return unique_terms[:20]


def _policy_sections(session: Session, policy_id, version_id) -> list[PolicySection]:
    statement = select(PolicySection).where(PolicySection.policy_id == policy_id)
    if version_id is not None:
        statement = statement.where(PolicySection.version_id == version_id)
    statement = statement.order_by(PolicySection.order_index.asc()).limit(20)
    return list(session.scalars(statement))


def _score_policy(policy, sections: list[PolicySection], terms: list[str]) -> tuple[float, list[str], list[dict]]:
    score = 0.0
    matched_terms = []
    section_refs = []
    title = (policy.title or "").lower()
    issuer = (policy.issuer or "").lower()
    jurisdiction = (policy.jurisdiction or "").lower()
    policy_type = (policy.policy_type or "").lower()
    for term in terms:
        term_score = 0.0
        if term in title:
            term_score += 2.0
        if term in issuer or term in jurisdiction or term in policy_type:
            term_score += 1.0
        matched_section_ids = []
        for section in sections:
            if term in (section.content or "").lower():
                term_score += 1.0
                matched_section_ids.append(str(section.id))
        if term_score:
            matched_terms.append(term)
            score += term_score
            for section_id in matched_section_ids[:3]:
                section_refs.append({"section_id": section_id, "matched_term": term})
    return score, matched_terms, section_refs[:10]
