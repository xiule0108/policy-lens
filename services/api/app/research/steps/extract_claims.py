from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.repositories.claims import create_claims
from app.repositories.document_chunks import list_document_chunks
from app.research.plan_schema import ResearchPlan, StepRunResult
from app.services.claim_extraction_service import extract_claims_from_chunks


def run_extract_claims(
    session: Session,
    plan: ResearchPlan,
    step_outputs: dict[str, dict],
) -> StepRunResult:
    chunks = list_document_chunks(session, plan.document_id, limit=500)
    claim_data = extract_claims_from_chunks(
        project_id=plan.project_id,
        document_id=plan.document_id,
        chunks=chunks,
        max_claims=20,
    )
    claims = create_claims(session, claim_data) if claim_data else []
    return StepRunResult(
        output_ref={
            "claim_count": len({str(claim.id) for claim in claims}),
            "claims": [_claim_ref(claim) for claim in claims],
        }
    )


def _claim_ref(claim) -> dict:
    return {
        "claim_id": str(claim.id),
        "claim_text": claim.claim_text,
        "claim_type": claim.claim_type,
        "topic": claim.topic,
        "industry": claim.industry,
        "jurisdiction": claim.jurisdiction,
        "confidence": _float_or_none(claim.confidence),
        "source_chunk_ids": [str(chunk_id) for chunk_id in claim.source_chunk_ids],
    }


def _float_or_none(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)
