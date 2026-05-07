from __future__ import annotations

import re
from collections import Counter

from sqlalchemy.orm import Session

from app.research.plan_schema import ResearchPlan, StepRunResult


POLICY_MARKERS = ("政策", "通知", "规划", "办法", "条例", "意见", "规则", "policy", "notice", "plan", "regulation")
JURISDICTION_TERMS = ("中国", "China", "美国", "United States", "欧盟", "EU", "北京", "上海", "广东", "江苏", "浙江")
STOPWORDS = {
    "this",
    "that",
    "with",
    "from",
    "into",
    "market",
    "policy",
    "supports",
    "and",
    "the",
}


def run_extract_article_signals(
    session: Session,
    plan: ResearchPlan,
    step_outputs: dict[str, dict],
) -> StepRunResult:
    context = step_outputs.get("collect_document_context", {})
    text = context.get("text_preview", "")
    keywords = extract_keywords(text)
    policy_terms = [term for term in keywords if any(marker.lower() in term.lower() for marker in POLICY_MARKERS)]
    years = sorted(set(re.findall(r"\b20\d{2}\b", text)))
    jurisdictions = [term for term in JURISDICTION_TERMS if term in text]
    fallback = text.strip().replace("\n", " ")[:500]
    return StepRunResult(
        output_ref={
            "keywords": keywords,
            "policy_terms": policy_terms,
            "years": years,
            "jurisdictions": jurisdictions,
            "summary_fallback": fallback,
        }
    )


def extract_keywords(text: str, limit: int = 12) -> list[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z-]{3,}|[\u4e00-\u9fff]{2,}", text)
    normalized = [token.strip().lower() for token in tokens if token.strip()]
    counts = Counter(token for token in normalized if token not in STOPWORDS)
    return [token for token, _count in counts.most_common(limit)]
