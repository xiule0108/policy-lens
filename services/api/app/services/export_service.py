from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.db.config import settings
from app.schemas.common import ExportResponse, EvidenceItem, PolicyOriginalExportRequest, ReportExportRequest
from packages.exporters.policy_original_exporter.exporter import create_mock_policy_export_bundle


def create_policy_original_export(payload: PolicyOriginalExportRequest) -> ExportResponse:
    export_id = f"export_{uuid4().hex[:8]}"
    result = create_mock_policy_export_bundle(
        export_id=export_id,
        mode=payload.mode,
        policy_ids=payload.policy_ids,
        cited_section_ids=payload.cited_section_ids,
        output_root=Path(settings.storage_dir),
        include_snapshots=payload.include_snapshots,
    )
    return ExportResponse(
        export_id=export_id,
        status="queued_mock",
        mode=payload.mode,
        bundle_path=str(result.bundle_path),
        manifest=result.manifest,
        evidence=[
            EvidenceItem(
                id=f"{export_id}_manifest",
                source_type="policy_export_manifest",
                summary="Mock export manifest generated with source, timestamp, and checksum placeholders.",
                confidence=1.0,
            )
        ],
    )


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
