from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.schemas.common import ExportResponse, EvidenceItem, PolicyOriginalExportRequest, ReportExportRequest
from app.services.policy_export_service import create_policy_original_export as create_real_policy_original_export


def create_policy_original_export(
    payload: PolicyOriginalExportRequest,
    session: Session | None = None,
) -> ExportResponse:
    if session is None:
        raise ValueError("A database session is required for policy original exports.")
    return create_real_policy_original_export(session, payload)


def create_report_export(payload: ReportExportRequest) -> ExportResponse:
    export_id = f"report_{uuid4().hex[:8]}"
    generated_at = datetime.now(timezone.utc).isoformat()
    return ExportResponse(
        export_id=export_id,
        status="queued_mock",
        mode=f"report_{payload.report_format}",
        bundle_path=None,
        manifest={
            "export_id": export_id,
            "project_id": payload.project_id,
            "format": payload.report_format,
            "generated_at": generated_at,
            "include_policy_originals": payload.include_policy_originals,
            "include_evidence_bundle": payload.include_evidence_bundle,
            "fact_boundaries": {
                "original_facts": [],
                "retrieved_facts": [],
                "model_reasoning": "Report generation is reserved for a future worker pipeline.",
            },
        },
        evidence=[],
    )
