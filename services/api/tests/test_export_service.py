import pytest
from sqlalchemy import select

from app.db.models import Export
from app.repositories.exports import get_export
from app.repositories.policies import create_policy
from app.repositories.policy_versions import create_policy_version
from app.repositories.projects import create_project
from app.schemas.common import PolicyOriginalExportRequest
from app.services import export_service
from app.services import policy_export_service


def test_policy_original_export_marks_db_record_failed_when_exporter_errors(
    db_session,
    monkeypatch,
) -> None:
    project = create_project(db_session, {"name": "Failure export workspace"})

    def raise_export_error(*args, **kwargs):
        raise RuntimeError("bundle write failed")

    policy = create_policy(db_session, {"title": "Export failure policy"})
    create_policy_version(
        db_session,
        {
            "policy_id": policy.id,
            "normalized_text": "Export failure text",
            "sha256": "a" * 64,
            "is_current": True,
        },
    )
    monkeypatch.setattr(policy_export_service, "write_policy_export_bundle", raise_export_error)

    with pytest.raises(RuntimeError, match="bundle write failed"):
        export_service.create_policy_original_export(
            PolicyOriginalExportRequest(
                project_id=project.id,
                policy_ids=[policy.id],
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
