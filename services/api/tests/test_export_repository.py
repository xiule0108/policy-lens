from app.repositories.exports import create_export, get_export, update_export_status
from app.repositories.projects import create_project


def test_export_repository_create_and_update(db_session) -> None:
    project = create_project(db_session, {"name": "Export workspace"})
    export = create_export(
        db_session,
        {
            "project_id": project.id,
            "export_type": "policy_originals",
            "formats": ["zip", "json"],
            "manifest": {"mode": "related_policy_bundle"},
        },
    )

    assert get_export(db_session, export.id).status == "queued"

    updated = update_export_status(
        db_session,
        export.id,
        "completed_mock",
        storage_key="exports/mock/policy_export_bundle",
        manifest={"mode": "related_policy_bundle", "sha256": "0" * 64},
    )

    assert updated is not None
    assert updated.status == "completed_mock"
    assert updated.storage_key == "exports/mock/policy_export_bundle"
    assert updated.manifest["sha256"] == "0" * 64
