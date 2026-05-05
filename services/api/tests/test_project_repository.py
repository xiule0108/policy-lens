from app.repositories.projects import (
    create_project,
    delete_project,
    get_project,
    list_projects,
    update_project,
)


def test_project_repository_crud(db_session) -> None:
    project = create_project(
        db_session,
        {
            "name": "New energy policy",
            "description": "Policy impact workspace",
            "industry": "energy",
            "jurisdictions": ["China", "EU"],
            "default_model_profile": "china_balanced",
        },
    )

    assert get_project(db_session, project.id).name == "New energy policy"
    assert list_projects(db_session) == [project]

    updated = update_project(db_session, project.id, {"status": "archived"})
    assert updated is not None
    assert updated.status == "archived"

    assert delete_project(db_session, project.id) is True
    assert get_project(db_session, project.id) is None
