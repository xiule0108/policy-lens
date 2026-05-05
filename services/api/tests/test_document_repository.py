from app.repositories.documents import (
    create_document,
    list_documents,
    update_document_parse_status,
)
from app.repositories.projects import create_project


def test_document_repository_filters_by_project_and_updates_parse_status(db_session) -> None:
    first_project = create_project(db_session, {"name": "First workspace"})
    second_project = create_project(db_session, {"name": "Second workspace"})
    first_document = create_document(
        db_session,
        {
            "project_id": first_project.id,
            "document_role": "research_article",
            "file_name": "first.txt",
            "file_type": ".txt",
        },
    )
    create_document(
        db_session,
        {
            "project_id": second_project.id,
            "document_role": "policy",
            "file_name": "second.txt",
            "file_type": ".txt",
        },
    )

    assert [document.id for document in list_documents(db_session, project_id=first_project.id)] == [first_document.id]

    updated = update_document_parse_status(db_session, first_document.id, "parsed")

    assert updated is not None
    assert updated.parse_status == "parsed"
