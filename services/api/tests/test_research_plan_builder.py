import pytest

from app.research.plan_builder import build_research_plan
from app.schemas.common import AnalysisJobRequest


def test_default_research_plan_contains_expected_steps() -> None:
    request = AnalysisJobRequest(
        project_id="11111111-1111-4111-8111-111111111111",
        document_ids=["22222222-2222-4222-8222-222222222222"],
        analysis_types=["policy_deep_dive"],
        model_profile="china_balanced",
    )

    plan = build_research_plan(request)

    assert plan.project_id == str(request.project_id)
    assert plan.document_id == str(request.document_ids[0])
    assert plan.mode == "policy_deep_dive"
    assert plan.plan_id
    assert [step.step_id for step in plan.steps] == [
        "parse_document_if_needed",
        "collect_document_context",
        "extract_article_signals",
        "extract_claims",
        "retrieve_policy_candidates",
        "match_policy_sections",
        "build_evidence_map",
        "summarize_findings",
    ]
    assert plan.steps[0].tool_name == "parse_document_if_needed"
    assert plan.steps[-1].depends_on == ["build_evidence_map"]
    assert plan.metadata["analysis_types"] == ["policy_deep_dive"]


def test_research_plan_requires_document_id() -> None:
    request = AnalysisJobRequest(
        project_id="11111111-1111-4111-8111-111111111111",
        document_ids=[],
        analysis_types=["policy_deep_dive"],
    )

    with pytest.raises(ValueError, match="document_ids"):
        build_research_plan(request)


def test_research_plan_defaults_mode_from_analysis_types() -> None:
    request = AnalysisJobRequest(
        project_id="11111111-1111-4111-8111-111111111111",
        document_ids=["22222222-2222-4222-8222-222222222222"],
        analysis_types=["quick_summary", "policy_candidates"],
        use_llm=True,
        provider_id="local",
        model="user-configured",
    )

    plan = build_research_plan(request)

    assert plan.mode == "quick_summary"
    assert plan.metadata["analysis_types"] == ["quick_summary", "policy_candidates"]
    assert plan.metadata["use_llm"] is True
    assert plan.metadata["provider_id"] == "local"
    assert plan.metadata["model"] == "user-configured"
