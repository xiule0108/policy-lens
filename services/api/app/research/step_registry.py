from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.orm import Session

from app.research.plan_schema import ResearchPlan, StepRunResult
from app.research.steps.collect_document_context import run_collect_document_context
from app.research.steps.extract_article_signals import run_extract_article_signals
from app.research.steps.parse_document import run_parse_document_if_needed
from app.research.steps.retrieve_policy_candidates import run_retrieve_policy_candidates
from app.research.steps.summarize_findings import run_summarize_findings


StepHandler = Callable[[Session, ResearchPlan, dict[str, dict]], StepRunResult]


STEP_HANDLERS: dict[str, StepHandler] = {
    "parse_document_if_needed": run_parse_document_if_needed,
    "collect_document_context": run_collect_document_context,
    "extract_article_signals": run_extract_article_signals,
    "retrieve_policy_candidates": run_retrieve_policy_candidates,
    "summarize_findings": run_summarize_findings,
}


def get_step_handler(tool_name: str) -> StepHandler:
    try:
        return STEP_HANDLERS[tool_name]
    except KeyError as exc:
        raise ValueError(f"Unknown research step tool: {tool_name}") from exc
