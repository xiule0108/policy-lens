from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.schemas.common import (
    ExportResponse,
    PolicyOriginalExportRequest,
    ReportExportRequest,
)
from app.services.export_service import create_policy_original_export, create_report_export

router = APIRouter()


@router.post("/policy-originals", response_model=ExportResponse, status_code=202)
def export_policy_originals(
    payload: PolicyOriginalExportRequest,
    session: Session = Depends(get_session),
) -> ExportResponse:
    return create_policy_original_export(payload, session=session)


@router.post("/report", response_model=ExportResponse, status_code=202)
def export_report(payload: ReportExportRequest) -> ExportResponse:
    return create_report_export(payload)
