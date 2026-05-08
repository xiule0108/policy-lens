from sqlalchemy.orm import Session

from app.schemas.common import ExportResponse, PolicyOriginalExportRequest, ReportExportRequest
from app.services.policy_export_service import create_policy_original_export as create_real_policy_original_export
from app.services.report_export_service import create_report_export as create_real_report_export


def create_policy_original_export(
    payload: PolicyOriginalExportRequest,
    session: Session | None = None,
) -> ExportResponse:
    if session is None:
        raise ValueError("A database session is required for policy original exports.")
    return create_real_policy_original_export(session, payload)


def create_report_export(payload: ReportExportRequest, session: Session | None = None) -> ExportResponse:
    if session is None:
        raise ValueError("A database session is required for report exports.")
    return create_real_report_export(session, payload)
