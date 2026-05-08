from __future__ import annotations


SUBJECT_RULES = (
    ("investor", ("投资", "investor", "capital", "融资")),
    ("company", ("企业", "公司", "business", "company")),
    ("grid", ("电网", "grid", "并网", "消纳")),
    ("consumer", ("消费者", "用户", "consumer")),
    ("government", ("政府", "监管", "审批")),
    ("market", ("行业", "产业", "market", "市场")),
)
DIRECTION_RULES = (
    ("negative", ("风险", "压力", "限制", "成本上升", "下滑", "negative", "risk")),
    ("positive", ("支持", "鼓励", "补贴", "增长", "改善", "促进", "positive", "support")),
    ("uncertain", ("不确定", "可能", "取决于", "uncertainty")),
)
HORIZON_RULES = (
    ("short", ("短期", "immediate", "near term", "当年")),
    ("medium", ("中期", "2026", "2027", "三年", "3年")),
    ("long", ("长期", "2030", "远期", "long term")),
)
MECHANISM_RULES = (
    ("subsidy", ("补贴",)),
    ("price_mechanism", ("电价", "价格")),
    ("capacity_mechanism", ("容量",)),
    ("spot_market", ("现货",)),
    ("green_power_certificate", ("绿电", "绿证")),
    ("grid_connection_consumption", ("并网", "消纳")),
    ("regulation_approval", ("监管", "审批")),
    ("carbon_market", ("碳价", "碳市场")),
    ("investment_financing", ("投资", "融资")),
)
MARKET_VARIABLE_RULES = (
    ("electricity_price", ("电价",)),
    ("coal_price", ("煤价",)),
    ("gas_price", ("气价",)),
    ("oil_price", ("油价",)),
    ("carbon_price", ("碳价",)),
    ("demand", ("需求",)),
    ("supply", ("供给",)),
    ("investment", ("投资",)),
    ("cost", ("成本",)),
    ("profit", ("利润",)),
    ("capacity", ("装机",)),
    ("storage", ("储能",)),
    ("green_power", ("绿电",)),
    ("green_certificate", ("绿证",)),
)


def build_impact_matrix(
    *,
    project_id: str,
    analysis_id: str | None,
    claims: list[dict],
    policy_matches: list[dict],
    claim_policy_map: list[dict],
) -> list[dict]:
    claims_by_id = {claim.get("claim_id") or claim.get("id"): claim for claim in claims}
    maps_by_claim = {item.get("claim_id"): item for item in claim_policy_map}
    items = []
    for match in policy_matches:
        claim_id = match.get("claim_id")
        claim = claims_by_id.get(claim_id) or maps_by_claim.get(claim_id) or {}
        text = _combined_text(claim, match)
        mechanism = _select_rule(text, MECHANISM_RULES, "policy_signal")
        market_variable = _select_rule(text, MARKET_VARIABLE_RULES, "policy_impact")
        impact_item = {
            "project_id": project_id,
            "analysis_id": analysis_id,
            "policy_id": match.get("policy_id"),
            "impact_subject": _select_rule(text, SUBJECT_RULES, "industry"),
            "impact_direction": _select_rule(text, DIRECTION_RULES, "neutral"),
            "impact_horizon": _select_rule(text, HORIZON_RULES, "uncertain"),
            "impact_mechanism": mechanism,
            "market_variable": market_variable,
            "analysis_text": _analysis_text(claim, mechanism, market_variable, text),
            "confidence": _confidence(match),
            "citations": _citations(claim, match),
        }
        items.append(impact_item)
    return items


def _combined_text(claim: dict, match: dict) -> str:
    evidence = match.get("evidence", {})
    parts = [
        claim.get("claim_text", ""),
        evidence.get("policy_title", ""),
        evidence.get("policy_quote", ""),
        " ".join(evidence.get("matched_terms", [])),
    ]
    return " ".join(part for part in parts if part)


def _select_rule(text: str, rules: tuple[tuple[str, tuple[str, ...]], ...], default: str) -> str:
    lowered = text.lower()
    for value, markers in rules:
        if any(marker.lower() in lowered for marker in markers):
            return value
    return default


def _analysis_text(claim: dict, mechanism: str, market_variable: str, text: str) -> str:
    direction = _select_rule(text, DIRECTION_RULES, "neutral")
    horizon = _select_rule(text, HORIZON_RULES, "uncertain")
    claim_text = claim.get("claim_text", "")
    return (
        f"rule_based_assessment: 该政策条款与文章观点“{claim_text}”存在匹配，"
        f"主要通过“{mechanism}”影响“{market_variable}”。当前规则判断影响方向为 {direction}，"
        f"影响周期为 {horizon}。该结论来自文章 chunk 与政策条款的确定性关键词匹配，需人工复核政策执行强度。"
    )


def _confidence(match: dict) -> float:
    score = match.get("relevance_score") or 0
    try:
        numeric_score = float(score)
    except (TypeError, ValueError):
        numeric_score = 0.0
    return round(max(0.5, min(0.85, 0.5 + numeric_score * 0.25)), 4)


def _citations(claim: dict, match: dict) -> list[dict]:
    evidence = match.get("evidence", {})
    source_chunk_ids = claim.get("source_chunk_ids") or evidence.get("claim_source_chunk_ids", [])
    return [
        {
            "source_type": "claim",
            "claim_id": claim.get("claim_id") or match.get("claim_id"),
            "claim_text": claim.get("claim_text") or evidence.get("claim_text"),
            "source_chunk_ids": source_chunk_ids,
        },
        {
            "source_type": "policy_section",
            "policy_id": match.get("policy_id"),
            "policy_section_id": match.get("policy_section_id"),
            "policy_title": evidence.get("policy_title"),
            "policy_quote": evidence.get("policy_quote"),
            "matched_terms": evidence.get("matched_terms", []),
        },
    ]
