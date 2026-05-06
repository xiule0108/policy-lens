import pytest

from app.repositories.document_chunks import create_document_chunks
from app.repositories.documents import create_document, get_document
from app.repositories.policies import create_policy
from app.repositories.policy_sections import count_policy_sections, list_policy_sections
from app.repositories.policy_versions import get_current_policy_version, list_policy_versions
from app.repositories.projects import create_project
from app.schemas.common import PolicyCreateFromDocumentRequest
from app.services.policy_ingestion_service import (
    PolicyDocumentNoChunksError,
    PolicyDocumentNotParsedError,
    PolicyDocumentRoleError,
    PolicyIngestionResult,
    PolicyNotFoundError,
    ingest_policy_from_document,
)


def create_policy_document(db_session, *, role: str = "policy", parse_status: str = "parsed", chunks: bool = True):
    project = create_project(db_session, {"name": "Policy ingestion workspace"})
    document = create_document(
        db_session,
        {
            "project_id": project.id,
            "document_role": role,
            "title": "Document policy title",
            "file_name": "policy.txt",
            "file_type": ".txt",
            "storage_key": f"documents/{project.id}/doc/policy.txt",
            "parse_status": parse_status,
            "source_url": "https://example.gov/policy",
            "sha256": "d" * 64,
            "metadata": {
                "content_type": "text/plain",
                "original_filename": "政策原文.txt",
                "safe_filename": "政策原文.txt",
                "parse_summary": {"chunk_count": 2},
            },
        },
    )
    if chunks:
        create_document_chunks(
            db_session,
            [
                {
                    "document_id": document.id,
                    "project_id": project.id,
                    "chunk_index": 0,
                    "section_title": "第一章",
                    "content": "第一章 总则",
                    "content_type": "heading",
                    "token_count": 8,
                    "metadata": {"parser": "txt_parser"},
                },
                {
                    "document_id": document.id,
                    "project_id": project.id,
                    "chunk_index": 1,
                    "page_start": 1,
                    "page_end": 1,
                    "section_title": "第一章",
                    "content": "支持新能源消纳。",
                    "content_type": "paragraph",
                    "token_count": 9,
                },
            ],
        )
    return document


def test_ingest_parsed_policy_document_creates_policy_version_sections_and_metadata(db_session) -> None:
    document = create_policy_document(db_session)

    result = ingest_policy_from_document(
        db_session,
        PolicyCreateFromDocumentRequest(
            document_id=document.id,
            issuer="国家能源局",
            jurisdiction="China",
            policy_type="notice",
            status="active",
            version_label="2026",
        ),
    )

    assert isinstance(result, PolicyIngestionResult)
    assert result.already_ingested is False
    assert result.title == "Document policy title"
    assert result.status == "active"
    assert result.section_count == 2

    current_version = get_current_policy_version(db_session, result.policy_id)
    assert current_version is not None
    assert str(current_version.id) == result.version_id
    assert current_version.normalized_text == "第一章 总则\n\n支持新能源消纳。"
    assert current_version.metadata_["source_document_id"] == str(document.id)
    assert count_policy_sections(db_session, result.policy_id, version_id=result.version_id) == 2
    sections = list_policy_sections(db_session, result.policy_id, version_id=result.version_id)
    assert sections[0].heading == "第一章"
    assert sections[0].metadata_["source_chunk_index"] == 0

    db_session.expire_all()
    updated_document = get_document(db_session, document.id)
    assert updated_document.metadata_["policy_ingestion"]["policy_id"] == result.policy_id
    assert updated_document.metadata_["content_type"] == "text/plain"
    assert updated_document.metadata_["parse_summary"] == {"chunk_count": 2}


def test_repeat_ingestion_returns_existing_result_without_duplicate_versions(db_session) -> None:
    document = create_policy_document(db_session)
    request = PolicyCreateFromDocumentRequest(document_id=document.id)

    first = ingest_policy_from_document(db_session, request)
    second = ingest_policy_from_document(db_session, request)

    assert second.already_ingested is True
    assert second.policy_id == first.policy_id
    assert second.version_id == first.version_id
    assert len(list_policy_versions(db_session, first.policy_id)) == 1


def test_force_new_version_creates_current_version_and_marks_old_not_current(db_session) -> None:
    document = create_policy_document(db_session)
    first = ingest_policy_from_document(db_session, PolicyCreateFromDocumentRequest(document_id=document.id))

    second = ingest_policy_from_document(
        db_session,
        PolicyCreateFromDocumentRequest(document_id=document.id, force_new_version=True, version_label="new"),
    )

    versions = list_policy_versions(db_session, first.policy_id)
    assert len(versions) == 2
    assert second.policy_id == first.policy_id
    assert second.version_id != first.version_id
    assert str(get_current_policy_version(db_session, first.policy_id).id) == second.version_id
    assert [version.is_current for version in versions] == [True, False]


def test_ingest_rejects_non_policy_pending_no_chunks_and_missing_policy(db_session) -> None:
    non_policy = create_policy_document(db_session, role="research_article")
    with pytest.raises(PolicyDocumentRoleError):
        ingest_policy_from_document(db_session, PolicyCreateFromDocumentRequest(document_id=non_policy.id))

    pending = create_policy_document(db_session, parse_status="pending")
    with pytest.raises(PolicyDocumentNotParsedError):
        ingest_policy_from_document(db_session, PolicyCreateFromDocumentRequest(document_id=pending.id))

    no_chunks = create_policy_document(db_session, chunks=False)
    with pytest.raises(PolicyDocumentNoChunksError):
        ingest_policy_from_document(db_session, PolicyCreateFromDocumentRequest(document_id=no_chunks.id))

    document = create_policy_document(db_session)
    missing_policy = create_policy(db_session, {"title": "Temporary policy"})
    missing_policy_id = missing_policy.id
    db_session.delete(missing_policy)
    db_session.commit()
    with pytest.raises(PolicyNotFoundError):
        ingest_policy_from_document(
            db_session,
            PolicyCreateFromDocumentRequest(document_id=document.id, policy_id=missing_policy_id),
        )
