from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
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


def list_exports(
    session: Session,
    *,
    project_id: uuid.UUID | str | None = None,
    export_type: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Export]:
    statement = select(Export).order_by(Export.created_at.desc()).limit(limit).offset(offset)
    if project_id is not None:
        statement = statement.where(Export.project_id == coerce_uuid(project_id))
    if export_type:
        statement = statement.where(Export.export_type == export_type)
    if status:
        statement = statement.where(Export.status == status)
    return list(session.scalars(statement))


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
