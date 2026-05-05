import pytest
from sqlalchemy import select

from app.db.models import Export
from app.repositories.exports import get_export
from app.repositories.projects import create_project
from app.schemas.common import PolicyOriginalExportRequest
from app.services import export_service


def test_policy_original_export_marks_db_record_failed_when_exporter_errors(
    db_session,
    monkeypatch,
) -> None:
    project = create_project(db_session, {"name": "Failure export workspace"})

    def raise_export_error(*args, **kwargs):
        raise RuntimeError("bundle write failed")

    monkeypatch.setattr(export_service, "create_mock_policy_export_bundle", raise_export_error)

    with pytest.raises(RuntimeError, match="bundle write failed"):
        export_service.create_policy_original_export(
            PolicyOriginalExportRequest(
                project_id=str(project.id),
                policy_ids=["policy_demo_001"],
                mode="related_policy_bundle",
            ),
            session=db_session,
        )

    export_ids = db_session.scalars(select(Export.id)).all()
    assert len(export_ids) == 1
    export = get_export(db_session, export_ids[0])
    assert export is not None
    assert export.status == "failed"
    assert export.manifest["error"]["message"] == "bundle write failed"
