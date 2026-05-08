from __future__ import annotations

from typing import Any


def generate_markdown_report(
    *,
    summary: dict,
    claims: list[dict],
    related_policies: list[dict],
    policy_matches: list[dict],
    impact_matrix: list[dict],
    fact_boundaries: dict,
    claim_policy_map: list[dict],
) -> tuple[str, dict]:
    outline = {
        "sections": [
            {"title": "文章概览", "source": "summary"},
            {"title": "核心观点", "source": "claims"},
            {"title": "关联政策与条款", "source": "policy_matches"},
            {"title": "政策影响矩阵", "source": "impact_matrix"},
            {"title": "证据链", "source": "claim_policy_map"},
            {"title": "风险与不确定性", "source": "rule_based_limitations"},
            {"title": "事实边界", "source": "fact_boundaries"},
            {"title": "后续研究建议", "source": "next_steps"},
        ],
        "generation_method": "deterministic_rule_based",
        "llm_used": False,
    }
    markdown = "\n".join(
        [
            "# 政策与市场研究解析报告",
            "",
            "## 1. 文章概览",
            f"- 文档标题：{summary.get('document_title') or '未命名'}",
            f"- 语言：{summary.get('document_language') or '未知'}",
            f"- chunk 数量：{summary.get('chunk_count', 0)}",
            f"- claim 数量：{summary.get('claim_count', len(claims))}",
            f"- 政策候选数量：{summary.get('policy_candidate_count', len(related_policies))}",
            f"- 政策匹配数量：{summary.get('policy_match_count', len(policy_matches))}",
            "",
            "## 2. 核心观点",
            *_claim_lines(claims),
            "",
            "## 3. 关联政策与条款",
            *_policy_match_lines(policy_matches, related_policies),
            "",
            "## 4. 政策影响矩阵",
            "| 影响主体 | 方向 | 周期 | 机制 | 市场变量 | 依据 |",
            "|---|---|---|---|---|---|",
            *_impact_rows(impact_matrix),
            "",
            "## 5. 证据链",
            *_evidence_lines(claim_policy_map),
            "",
            "## 6. 风险与不确定性",
            "- 当前分析为确定性规则生成。",
            "- 需要人工复核政策有效性、适用地区和执行强度。",
            "- 暂未接入 RAG、embedding 或 LLM 复核。",
            "",
            "## 7. 事实边界",
            f"- 原文事实：{len(fact_boundaries.get('original_facts', []))} 条",
            f"- 检索事实：{len(fact_boundaries.get('retrieved_facts', []))} 条",
            "- 模型推理：无",
            "",
            "## 8. 后续研究建议",
            "- 补充政策执行地区、适用主体和时间窗口核查。",
            "- 结合人工复核或后续 LLM 复核增强影响方向与强度判断。",
        ]
    )
    return markdown, outline


def _claim_lines(claims: list[dict]) -> list[str]:
    if not claims:
        return ["- 暂无可提取观点。"]
    return [f"- [{claim.get('claim_type', 'signal')}] {claim.get('claim_text', '')}" for claim in claims[:10]]


def _policy_match_lines(policy_matches: list[dict], related_policies: list[dict]) -> list[str]:
    if policy_matches:
        return [
            (
                f"- Claim {match.get('claim_id')} 匹配政策 {match.get('policy_id')} "
                f"条款 {match.get('policy_section_id')}，理由：{match.get('reason') or '规则命中'}"
            )
            for match in policy_matches[:10]
        ]
    if related_policies:
        return [f"- {policy.get('title')}，score={policy.get('score')}" for policy in related_policies[:10]]
    return ["- 暂无关联政策。"]


def _impact_rows(impact_matrix: list[dict]) -> list[str]:
    if not impact_matrix:
        return ["| 暂无 | 暂无 | 暂无 | 暂无 | 暂无 | 暂无 |"]
    return [
        (
            f"| {item.get('impact_subject') or ''} | {item.get('impact_direction') or ''} | "
            f"{item.get('impact_horizon') or ''} | {item.get('impact_mechanism') or ''} | "
            f"{item.get('market_variable') or ''} | {item.get('analysis_text', '')[:80]} |"
        )
        for item in impact_matrix[:20]
    ]


def _evidence_lines(claim_policy_map: list[dict]) -> list[str]:
    if not claim_policy_map:
        return ["- 暂无证据链。"]
    lines: list[str] = []
    for item in claim_policy_map[:10]:
        lines.append(f"### Claim {item.get('claim_id')}")
        lines.append(f"- 文章证据：{item.get('claim_text', '')}")
        matches = item.get("matches", [])
        if not matches:
            lines.append("- 政策条款：暂无匹配")
            continue
        for match in matches[:5]:
            evidence: dict[str, Any] = match.get("evidence", {})
            lines.append(f"- 政策条款：{evidence.get('policy_quote') or match.get('policy_section_id')}")
            lines.append(f"- 匹配理由：{match.get('reason') or '规则命中'}")
    return lines
