from __future__ import annotations

from uuid import uuid4

from app.db.base import utc_now
from app.research.plan_schema import ResearchPlan, ResearchPlanStep
from app.schemas.common import AnalysisJobRequest


def build_research_plan(request: AnalysisJobRequest) -> ResearchPlan:
    if not request.document_ids:
        raise ValueError("document_ids must contain at least one document id.")
    mode = request.analysis_types[0] if request.analysis_types else "policy_deep_dive"
    document_id = str(request.document_ids[0])
    project_id = str(request.project_id)
    model_profile = request.model_profile
    return ResearchPlan(
        plan_id=f"research_plan_{uuid4().hex[:12]}",
        project_id=project_id,
        document_id=document_id,
        mode=mode,
        model_profile=model_profile,
        created_at=utc_now(),
        metadata={
            "analysis_types": request.analysis_types or ["policy_deep_dive"],
            "use_llm": request.use_llm,
            "provider_id": request.provider_id,
            "model": request.model,
        },
        steps=[
            ResearchPlanStep(
                step_id="parse_document_if_needed",
                name="Parse document if needed",
                tool_name="parse_document_if_needed",
                description="Parse the uploaded document when chunks are not available yet.",
                input_ref={"document_id": document_id},
                output_key="parse_document",
            ),
            ResearchPlanStep(
                step_id="collect_document_context",
                name="Collect document context",
                tool_name="collect_document_context",
                description="Collect document metadata and chunk references for downstream analysis.",
                depends_on=["parse_document_if_needed"],
                input_ref={"document_id": document_id},
                output_key="document_context",
            ),
            ResearchPlanStep(
                step_id="extract_article_signals",
                name="Extract article signals",
                tool_name="extract_article_signals",
                description="Extract deterministic keywords, policy terms, years, and jurisdictions.",
                depends_on=["collect_document_context"],
                input_ref={"from_step": "collect_document_context"},
                output_key="article_signals",
            ),
            ResearchPlanStep(
                step_id="extract_claims",
                name="Extract article claims",
                tool_name="extract_claims",
                description="Extract deterministic article claims from document chunks and persist them.",
                depends_on=["collect_document_context"],
                input_ref={"from_step": "collect_document_context"},
                output_key="claims",
            ),
            ResearchPlanStep(
                step_id="retrieve_policy_candidates",
                name="Retrieve policy candidates",
                tool_name="retrieve_policy_candidates",
                description="Retrieve local policy candidates with SQL-backed keyword matching.",
                depends_on=["extract_article_signals"],
                input_ref={"from_step": "extract_article_signals"},
                output_key="policy_candidates",
            ),
            ResearchPlanStep(
                step_id="match_policy_sections",
                name="Match policy sections",
                tool_name="match_policy_sections",
                description="Match persisted claims to current policy sections with deterministic evidence.",
                depends_on=["extract_claims", "retrieve_policy_candidates"],
                input_ref={"from_steps": ["extract_claims", "retrieve_policy_candidates"]},
                output_key="policy_matches",
            ),
            ResearchPlanStep(
                step_id="build_evidence_map",
                name="Build evidence map",
                tool_name="build_evidence_map",
                description="Build claim-policy evidence maps and factual boundaries.",
                depends_on=["extract_claims", "match_policy_sections"],
                input_ref={"from_steps": ["extract_claims", "match_policy_sections"]},
                output_key="evidence_map",
            ),
            ResearchPlanStep(
                step_id="build_impact_matrix",
                name="Build impact matrix",
                tool_name="build_impact_matrix",
                description="Build deterministic policy impact matrix items from evidence.",
                depends_on=["build_evidence_map"],
                input_ref={"from_step": "build_evidence_map"},
                output_key="impact_matrix",
            ),
            ResearchPlanStep(
                step_id="summarize_findings",
                name="Summarize findings",
                tool_name="summarize_findings",
                description="Build a deterministic summary and fact boundary skeleton.",
                depends_on=["build_impact_matrix"],
                input_ref={"from_step": "build_impact_matrix"},
                output_key="summary",
                model_profile=model_profile,
            ),
            ResearchPlanStep(
                step_id="draft_markdown_report",
                name="Draft markdown report",
                tool_name="draft_markdown_report",
                description="Draft a deterministic Markdown research report from analysis outputs.",
                depends_on=["summarize_findings"],
                input_ref={"from_step": "summarize_findings"},
                output_key="markdown_report",
            ),
        ],
    )
