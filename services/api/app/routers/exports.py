from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.config import settings
from app.db.session import get_session
from app.repositories.exports import get_export
from app.schemas.common import (
    ExportDetailResponse,
    ExportResponse,
    PolicyOriginalExportRequest,
    ReportExportRequest,
)
from app.services.export_service import create_report_export
from app.services.policy_export_service import (
    PolicyExportCurrentVersionError,
    PolicyExportNotFoundError,
    PolicyExportValidationError,
    create_policy_original_export,
)
from app.services.report_export_service import (
    ReportExportNotFoundError,
    ReportExportValidationError,
)
from app.services.storage_service import StorageError, resolve_storage_path

router = APIRouter()


@router.post("/policy-originals", response_model=ExportResponse, status_code=202)
def export_policy_originals(
    payload: PolicyOriginalExportRequest,
    session: Session = Depends(get_session),
) -> ExportResponse:
    try:
        return create_policy_original_export(session, payload)
    except PolicyExportNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (PolicyExportValidationError, PolicyExportCurrentVersionError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{export_id}", response_model=ExportDetailResponse)
def get_export_record(export_id: UUID, session: Session = Depends(get_session)) -> ExportDetailResponse:
    export = get_export(session, export_id)
    if export is None:
        raise HTTPException(status_code=404, detail="Export not found.")
    return ExportDetailResponse(
        export_id=str(export.id),
        project_id=str(export.project_id) if export.project_id else None,
        analysis_id=str(export.analysis_id) if export.analysis_id else None,
        export_type=export.export_type,
        status=export.status,
        formats=export.formats or [],
        storage_key=export.storage_key,
        manifest=export.manifest or {},
        created_at=export.created_at,
        finished_at=export.finished_at,
    )


@router.get("/{export_id}/download")
def download_export(export_id: UUID, session: Session = Depends(get_session)) -> FileResponse:
    export = get_export(session, export_id)
    if export is None:
        raise HTTPException(status_code=404, detail="Export not found.")
    if export.status != "completed":
        raise HTTPException(status_code=409, detail="Export is not completed.")
    if not export.storage_key:
        raise HTTPException(status_code=404, detail="Export file not found.")
    try:
        export_path = resolve_storage_path(Path(settings.storage_dir), export.storage_key)
    except StorageError as exc:
        raise HTTPException(status_code=404, detail="Export file not found.") from exc
    if not export_path.exists() or not export_path.is_file():
        raise HTTPException(status_code=404, detail="Export file not found.")
    return FileResponse(
        export_path,
        media_type="application/zip",
        filename=download_filename(export.export_type, export.id),
    )


@router.post("/report", response_model=ExportResponse, status_code=202)
def export_report(payload: ReportExportRequest, session: Session = Depends(get_session)) -> ExportResponse:
    try:
        return create_report_export(payload, session=session)
    except ReportExportNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ReportExportValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def download_filename(export_type: str, export_id: UUID) -> str:
    if export_type == "policy_originals":
        return f"policy_export_{export_id}.zip"
    if export_type == "report":
        return f"report_export_{export_id}.zip"
    return f"export_{export_id}.zip"
