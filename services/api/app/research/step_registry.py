from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.orm import Session

from app.research.plan_schema import ResearchPlan, StepRunResult
from app.research.steps.build_evidence_map import run_build_evidence_map
from app.research.steps.build_impact_matrix import run_build_impact_matrix
from app.research.steps.collect_document_context import run_collect_document_context
from app.research.steps.draft_markdown_report import run_draft_markdown_report
from app.research.steps.extract_article_signals import run_extract_article_signals
from app.research.steps.extract_claims import run_extract_claims
from app.research.steps.match_policy_sections import run_match_policy_sections
from app.research.steps.parse_document import run_parse_document_if_needed
from app.research.steps.retrieve_policy_candidates import run_retrieve_policy_candidates
from app.research.steps.summarize_findings import run_summarize_findings


StepHandler = Callable[[Session, ResearchPlan, dict[str, dict]], StepRunResult]


STEP_HANDLERS: dict[str, StepHandler] = {
    "parse_document_if_needed": run_parse_document_if_needed,
    "collect_document_context": run_collect_document_context,
    "extract_article_signals": run_extract_article_signals,
    "extract_claims": run_extract_claims,
    "retrieve_policy_candidates": run_retrieve_policy_candidates,
    "match_policy_sections": run_match_policy_sections,
    "build_evidence_map": run_build_evidence_map,
    "build_impact_matrix": run_build_impact_matrix,
    "summarize_findings": run_summarize_findings,
    "draft_markdown_report": run_draft_markdown_report,
}


def get_step_handler(tool_name: str) -> StepHandler:
    try:
        return STEP_HANDLERS[tool_name]
    except KeyError as exc:
        raise ValueError(f"Unknown research step tool: {tool_name}") from exc
