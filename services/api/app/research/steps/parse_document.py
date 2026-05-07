from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.document_chunks import count_document_chunks
from app.repositories.documents import get_document
from app.research.plan_schema import ResearchPlan, StepRunResult
from app.services.document_parse_service import parse_document_by_id


def run_parse_document_if_needed(
    session: Session,
    plan: ResearchPlan,
    step_outputs: dict[str, dict],
) -> StepRunResult:
    document = get_document(session, plan.document_id)
    if document is None:
        raise ValueError("Document not found.")
    chunk_count = count_document_chunks(session, document.id)
    if document.parse_status == "parsed" and chunk_count > 0:
        return StepRunResult(
            output_ref={
                "document_id": str(document.id),
                "parse_status": "parsed",
                "chunk_count": chunk_count,
                "skipped_reason": "document_already_parsed",
            }
        )

    result = parse_document_by_id(session, UUID(str(document.id)))
    return StepRunResult(
        output_ref={
            "document_id": result.document_id,
            "parse_status": result.parse_status,
            "chunk_count": result.chunk_count,
            "page_count": result.page_count,
            "language": result.language,
            "title": result.title,
        }
    )
