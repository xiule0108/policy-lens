from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.document_chunks import list_document_chunks
from app.repositories.documents import get_document
from app.research.plan_schema import ResearchPlan, StepRunResult


def run_collect_document_context(
    session: Session,
    plan: ResearchPlan,
    step_outputs: dict[str, dict],
) -> StepRunResult:
    document = get_document(session, plan.document_id)
    if document is None:
        raise ValueError("Document not found.")
    chunks = list_document_chunks(session, document.id, limit=500)
    text = "\n\n".join(chunk.content for chunk in chunks)
    text_preview = text[:4000]
    return StepRunResult(
        output_ref={
            "document": {
                "id": str(document.id),
                "project_id": str(document.project_id),
                "title": document.title,
                "document_role": document.document_role,
                "language": document.language,
                "parse_status": document.parse_status,
                "source_url": document.source_url,
                "sha256": document.sha256,
            },
            "chunk_count": len(chunks),
            "chunk_ids": [str(chunk.id) for chunk in chunks],
            "text_preview": text_preview,
        }
    )
