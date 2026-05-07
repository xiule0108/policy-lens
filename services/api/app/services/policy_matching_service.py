from __future__ import annotations

import re
from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Claim, Policy, PolicySection, PolicyVersion


DOMAIN_TERMS = (
    "新能源",
    "储能",
    "电价",
    "监管",
    "政策",
    "市场",
    "投资",
    "风险",
    "补贴",
    "需求",
    "供给",
    "现货",
    "容量",
    "绿电",
    "绿证",
    "energy",
    "storage",
    "price",
    "regulation",
    "policy",
    "market",
    "investment",
    "risk",
    "subsidy",
    "demand",
    "supply",
)
STOPWORDS = {"this", "that", "with", "from", "into", "will", "have", "been", "and", "the"}


def match_claims_to_policy_sections(
    session: Session,
    claims: list[Claim],
    *,
    limit_per_claim: int = 5,
) -> list[dict]:
    sections = _current_policy_sections(session)
    matches: list[dict] = []
    for claim in claims:
        terms = extract_match_terms(claim.claim_text)
        claim_matches = []
        for policy, section in sections:
            score, matched_terms, components = _score_section(claim, terms, policy, section)
            if score <= 0:
                continue
            normalized_score = min(score / 10, 1.0)
            claim_matches.append(
                {
                    "project_id": str(claim.project_id),
                    "claim_id": str(claim.id),
                    "policy_id": str(policy.id),
                    "policy_section_id": str(section.id),
                    "match_type": _match_type(claim.claim_text, policy, section, matched_terms),
                    "relevance_score": round(normalized_score, 4),
                    "reason": _reason(matched_terms, normalized_score),
                    "evidence": _evidence(claim, policy, section, matched_terms, components),
                }
            )
        claim_matches.sort(key=lambda item: item["relevance_score"], reverse=True)
        matches.extend(claim_matches[:limit_per_claim])
    return matches


def extract_match_terms(text: str, limit: int = 12) -> list[str]:
    terms = [term for term in DOMAIN_TERMS if term.lower() in text.lower()]
    tokens = re.findall(r"[A-Za-z][A-Za-z-]{3,}|[\u4e00-\u9fff]{2,}", text)
    counts = Counter(token.lower() for token in tokens if token.lower() not in STOPWORDS)
    for token, _count in counts.most_common(limit):
        if token not in terms:
            terms.append(token)
    return terms[:limit]


def _current_policy_sections(session: Session) -> list[tuple[Policy, PolicySection]]:
    statement = (
        select(Policy, PolicySection)
        .join(PolicyVersion, PolicyVersion.policy_id == Policy.id)
        .join(PolicySection, PolicySection.version_id == PolicyVersion.id)
        .where(PolicyVersion.is_current.is_(True))
        .order_by(Policy.created_at.desc(), PolicySection.order_index.asc())
        .limit(1000)
    )
    return list(session.execute(statement).all())


def _score_section(
    claim: Claim,
    terms: list[str],
    policy: Policy,
    section: PolicySection,
) -> tuple[float, list[str], dict]:
    score = 0.0
    matched_terms: list[str] = []
    components = {
        "title_hits": 0,
        "section_hits": 0,
        "heading_hits": 0,
        "jurisdiction_match": False,
    }
    title = (policy.title or "").lower()
    issuer = (policy.issuer or "").lower()
    jurisdiction = (policy.jurisdiction or "").lower()
    policy_type = (policy.policy_type or "").lower()
    heading = (section.heading or "").lower()
    section_path = (section.section_path or "").lower()
    content = (section.content or "").lower()
    for term in terms:
        lowered = term.lower()
        term_score = 0.0
        if lowered in title:
            term_score += 2.0
            components["title_hits"] += 1
        if lowered in issuer or lowered in jurisdiction or lowered in policy_type:
            term_score += 1.0
        if lowered in heading or lowered in section_path:
            term_score += 1.5
            components["heading_hits"] += 1
        if lowered in content:
            term_score += 1.0
            components["section_hits"] += 1
        if term_score:
            score += term_score
            matched_terms.append(term)
    if claim.jurisdiction and policy.jurisdiction and claim.jurisdiction.lower() == policy.jurisdiction.lower():
        score += 1.0
        components["jurisdiction_match"] = True
    return min(score, 10.0), matched_terms, components


def _match_type(claim_text: str, policy: Policy, section: PolicySection, matched_terms: list[str]) -> str:
    lowered_claim = claim_text.lower()
    if (policy.title and policy.title.lower() in lowered_claim) or (
        section.heading and section.heading.lower() in lowered_claim
    ):
        return "explicit"
    if len(matched_terms) >= 2:
        return "implicit"
    return "related"


def _reason(matched_terms: list[str], score: float) -> str:
    terms = ", ".join(matched_terms[:6])
    return f"Matched policy section terms: {terms}. Relevance score: {score:.2f}."


def _evidence(
    claim: Claim,
    policy: Policy,
    section: PolicySection,
    matched_terms: list[str],
    components: dict,
) -> dict:
    return {
        "source": "deterministic_policy_matcher",
        "claim_text": claim.claim_text,
        "claim_source_chunk_ids": [str(chunk_id) for chunk_id in claim.source_chunk_ids],
        "policy_id": str(policy.id),
        "policy_title": policy.title,
        "policy_section_id": str(section.id),
        "policy_section_heading": section.heading,
        "matched_terms": matched_terms,
        "claim_quote": _quote(claim.claim_text),
        "policy_quote": _quote(section.content),
        "score_components": components,
        "fact_boundary": "retrieved_fact",
    }


def _quote(text: str, max_chars: int = 240) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    return normalized[:max_chars]
