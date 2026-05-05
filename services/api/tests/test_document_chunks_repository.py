from app.repositories.document_chunks import (
    count_document_chunks,
    create_document_chunks,
    delete_document_chunks,
    list_document_chunks,
)
from app.repositories.documents import create_document
from app.repositories.projects import create_project


def test_document_chunks_repository_crud(db_session) -> None:
    project = create_project(db_session, {"name": "Chunk workspace"})
    document = create_document(
        db_session,
        {
            "project_id": project.id,
            "document_role": "research_article",
            "file_name": "memo.txt",
            "file_type": ".txt",
        },
    )

    chunks = create_document_chunks(
        db_session,
        [
            {
                "document_id": document.id,
                "project_id": project.id,
                "chunk_index": 0,
                "content": "First chunk",
                "content_type": "paragraph",
                "token_count": 5,
                "metadata": {"source": "test"},
            },
            {
                "document_id": document.id,
                "project_id": project.id,
                "chunk_index": 1,
                "content": "Second chunk",
                "content_type": "paragraph",
                "token_count": 6,
            },
        ],
    )

    assert len(chunks) == 2
    assert count_document_chunks(db_session, document.id) == 2
    assert [chunk.content for chunk in list_document_chunks(db_session, document.id)] == [
        "First chunk",
        "Second chunk",
    ]
    assert list_document_chunks(db_session, document.id, limit=1, offset=1)[0].content == "Second chunk"

    delete_document_chunks(db_session, document.id)

    assert count_document_chunks(db_session, document.id) == 0
