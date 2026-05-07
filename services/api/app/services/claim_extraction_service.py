from __future__ import annotations

import re
from collections.abc import Iterable

from app.db.models import DocumentChunk


CLAIM_KEYWORDS = (
    "政策",
    "市场",
    "行业",
    "价格",
    "需求",
    "供给",
    "投资",
    "风险",
    "监管",
    "补贴",
    "电价",
    "碳价",
    "储能",
    "新能源",
    "现货",
    "容量",
    "绿电",
    "绿证",
    "policy",
    "market",
    "industry",
    "price",
    "demand",
    "supply",
    "investment",
    "risk",
    "regulation",
    "subsidy",
    "storage",
    "renewable",
)
FORECAST_MARKERS = ("预计", "预测", "有望", "可能", "将", "未来", "forecast", "likely", "may")
RECOMMENDATION_MARKERS = ("建议", "应当", "需要", "推动", "鼓励", "recommend", "should", "need")
JUDGMENT_MARKERS = ("风险", "不确定", "压力", "挑战", "risk", "uncertain", "pressure", "challenge")
FACT_MARKERS = (r"\b20\d{2}\b", r"\d", "已经", "发布", "实施")
JURISDICTIONS = (
    ("China", ("中国", "China")),
    ("EU", ("欧盟", "EU")),
    ("US", ("美国", "United States", "US")),
)
ENERGY_TERMS = ("能源", "储能", "新能源", "电价", "绿电", "绿证", "energy", "storage", "renewable")


def extract_claims_from_chunks(
    *,
    project_id: str,
    document_id: str,
    chunks: list[DocumentChunk],
    max_claims: int = 20,
) -> list[dict]:
    candidates: list[dict] = []
    seen: set[str] = set()
    for chunk in chunks:
        for sentence in _split_sentences(chunk.content):
            normalized = _normalize_sentence(sentence)
            if not _is_claim_candidate(normalized) or normalized in seen:
                continue
            seen.add(normalized)
            candidates.append(
                {
                    "project_id": project_id,
                    "document_id": document_id,
                    "claim_text": normalized,
                    "claim_type": classify_claim_type(normalized),
                    "topic": _topic(normalized),
                    "industry": "energy" if _contains_any(normalized, ENERGY_TERMS) else None,
                    "jurisdiction": detect_jurisdiction(normalized),
                    "confidence": _confidence(normalized),
                    "source_chunk_ids": [str(chunk.id)],
                }
            )
            if len(candidates) >= max_claims:
                return candidates
    return candidates


def classify_claim_type(text: str) -> str:
    if _contains_any(text, RECOMMENDATION_MARKERS):
        return "recommendation"
    if _contains_any(text, JUDGMENT_MARKERS):
        return "judgment"
    if _contains_any(text, FORECAST_MARKERS):
        return "forecast"
    if any(re.search(pattern, text) for pattern in FACT_MARKERS):
        return "fact"
    return "signal"


def detect_jurisdiction(text: str) -> str | None:
    for normalized, markers in JURISDICTIONS:
        if _contains_any(text, markers):
            return normalized
    return None


def _split_sentences(text: str) -> Iterable[str]:
    for sentence in re.split(r"(?<=[。！？.!?])\s+|[。！？!?]\s*", text.replace("\n", " ")):
        stripped = sentence.strip(" ;；,，")
        if stripped:
            yield stripped


def _normalize_sentence(sentence: str) -> str:
    return re.sub(r"\s+", " ", sentence).strip()


def _is_claim_candidate(sentence: str) -> bool:
    return 12 <= len(sentence) <= 300 and _contains_any(sentence, CLAIM_KEYWORDS)


def _topic(sentence: str) -> str | None:
    for keyword in CLAIM_KEYWORDS:
        if keyword in sentence:
            return keyword
    return None


def _confidence(sentence: str) -> float:
    confidence = 0.55
    if detect_jurisdiction(sentence):
        confidence += 0.05
    if any(re.search(pattern, sentence) for pattern in FACT_MARKERS):
        confidence += 0.05
    if _contains_any(sentence, ENERGY_TERMS):
        confidence += 0.05
    return min(confidence, 0.75)


def _contains_any(text: str, markers: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(marker.lower() in lowered for marker in markers)
