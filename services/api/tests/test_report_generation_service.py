from app.services.report_generation_service import generate_markdown_report


def test_generate_markdown_report_contains_required_sections() -> None:
    markdown, outline = generate_markdown_report(
        summary={
            "document_title": "新能源消纳研究",
            "document_language": "zh-CN",
            "chunk_count": 3,
            "claim_count": 1,
            "policy_candidate_count": 1,
            "policy_match_count": 1,
        },
        claims=[
            {
                "claim_id": "claim-1",
                "claim_text": "新能源储能需求预计增长。",
                "claim_type": "forecast",
                "source_chunk_ids": ["chunk-1"],
            }
        ],
        related_policies=[{"policy_id": "policy-1", "title": "新能源储能政策", "score": 0.8}],
        policy_matches=[
            {
                "claim_id": "claim-1",
                "policy_id": "policy-1",
                "policy_section_id": "section-1",
                "reason": "Matched terms.",
                "evidence": {"policy_quote": "鼓励新能源储能投资。"},
            }
        ],
        impact_matrix=[
            {
                "impact_subject": "investor",
                "impact_direction": "positive",
                "impact_horizon": "medium",
                "impact_mechanism": "price_mechanism",
                "market_variable": "electricity_price",
                "analysis_text": "rule_based_assessment: ...",
            }
        ],
        fact_boundaries={"original_facts": [{}], "retrieved_facts": [{}], "model_reasoning": []},
        claim_policy_map=[{"claim_id": "claim-1", "claim_text": "新能源储能需求预计增长。", "matches": []}],
    )

    assert "# 政策与市场研究解析报告" in markdown
    assert "## 1. 文章概览" in markdown
    assert "## 4. 政策影响矩阵" in markdown
    assert "| 影响主体 | 方向 | 周期 | 机制 | 市场变量 | 依据 |" in markdown
    assert "## 5. 证据链" in markdown
    assert "模型推理：无" in markdown
    assert outline["generation_method"] == "deterministic_rule_based"
    assert outline["llm_used"] is False
    assert any(section["title"] == "政策影响矩阵" for section in outline["sections"])
