from __future__ import annotations

from datetime import datetime, timezone
import uuid

from sqlalchemy.orm import Session

from app.db.models import Export
from app.repositories._utils import coerce_optional_uuid, coerce_uuid


def create_export(session: Session, data: dict) -> Export:
    export = Export(
        project_id=coerce_optional_uuid(data.get("project_id")),
        analysis_id=coerce_optional_uuid(data.get("analysis_id")),
        export_type=data["export_type"],
        status=data.get("status", "queued"),
        formats=data.get("formats", []),
        storage_key=data.get("storage_key"),
        manifest=data.get("manifest", {}),
    )
    session.add(export)
    session.commit()
    session.refresh(export)
    return export


def get_export(session: Session, export_id: uuid.UUID | str) -> Export | None:
    return session.get(Export, coerce_uuid(export_id))


def update_export_status(
    session: Session,
    export_id: uuid.UUID | str,
    status: str,
    storage_key: str | None = None,
    manifest: dict | None = None,
) -> Export | None:
    export = get_export(session, export_id)
    if export is None:
        return None
    export.status = status
    if storage_key is not None:
        export.storage_key = storage_key
    if manifest is not None:
        export.manifest = manifest
    if status.startswith("completed") or status in {"failed", "cancelled"}:
        export.finished_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(export)
    return export
