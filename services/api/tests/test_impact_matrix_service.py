from app.services.impact_matrix_service import build_impact_matrix


def test_build_impact_matrix_derives_fields_and_citations() -> None:
    claim = {
        "claim_id": "claim-1",
        "claim_text": "中国新能源储能需求预计在2026年增长，电价政策将支持电网消纳和投资。",
        "claim_type": "forecast",
        "source_chunk_ids": ["chunk-1"],
    }
    match = {
        "claim_id": "claim-1",
        "policy_id": "policy-1",
        "policy_section_id": "section-1",
        "relevance_score": 0.8,
        "evidence": {
            "policy_title": "新能源储能电价政策",
            "policy_quote": "鼓励新能源储能投资，完善电价政策和电网消纳机制。",
            "matched_terms": ["新能源", "储能", "电价", "投资"],
            "claim_source_chunk_ids": ["chunk-1"],
        },
    }
    claim_policy_map = [{**claim, "matches": [match]}]

    items = build_impact_matrix(
        project_id="project-1",
        analysis_id="analysis-1",
        claims=[claim],
        policy_matches=[match],
        claim_policy_map=claim_policy_map,
    )

    assert len(items) == 1
    item = items[0]
    assert item["impact_subject"] == "investor"
    assert item["impact_direction"] == "positive"
    assert item["impact_horizon"] == "medium"
    assert item["impact_mechanism"] == "price_mechanism"
    assert item["market_variable"] == "electricity_price"
    assert item["confidence"] >= 0.6
    assert "rule_based_assessment" in item["analysis_text"]
    assert item["citations"][0]["source_type"] == "claim"
    assert item["citations"][1]["source_type"] == "policy_section"
    assert item["citations"][1]["policy_quote"]


def test_build_impact_matrix_handles_negative_uncertain_defaults() -> None:
    claim = {
        "claim_id": "claim-2",
        "claim_text": "监管风险和成本上升可能对企业利润形成压力。",
        "claim_type": "judgment",
        "source_chunk_ids": ["chunk-2"],
    }
    match = {
        "claim_id": "claim-2",
        "policy_id": "policy-2",
        "policy_section_id": "section-2",
        "relevance_score": 0.5,
        "evidence": {
            "policy_title": "监管规则",
            "policy_quote": "加强审批监管。",
            "matched_terms": ["监管", "风险"],
            "claim_source_chunk_ids": ["chunk-2"],
        },
    }

    items = build_impact_matrix(
        project_id="project-1",
        analysis_id=None,
        claims=[claim],
        policy_matches=[match],
        claim_policy_map=[{**claim, "matches": [match]}],
    )

    assert items[0]["impact_subject"] == "company"
    assert items[0]["impact_direction"] == "negative"
    assert items[0]["impact_horizon"] == "uncertain"
    assert items[0]["impact_mechanism"] == "regulation_approval"
    assert items[0]["market_variable"] == "cost"
