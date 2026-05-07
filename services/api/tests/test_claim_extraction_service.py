from app.repositories.document_chunks import create_document_chunks
from app.repositories.documents import create_document
from app.repositories.projects import create_project
from app.services.claim_extraction_service import extract_claims_from_chunks


def create_article_chunks(db_session):
    project = create_project(db_session, {"name": "Claim extraction project"})
    document = create_document(
        db_session,
        {
            "project_id": project.id,
            "document_role": "research_article",
            "title": "新能源市场研究",
            "file_name": "article.txt",
            "file_type": ".txt",
            "parse_status": "parsed",
        },
    )
    chunks = create_document_chunks(
        db_session,
        [
            {
                "project_id": project.id,
                "document_id": document.id,
                "chunk_index": 0,
                "content": "中国新能源储能需求预计将在2026年继续增长。建议推动现货市场和绿电交易机制。",
                "content_type": "paragraph",
            },
            {
                "project_id": project.id,
                "document_id": document.id,
                "chunk_index": 1,
                "content": "监管风险和电价不确定性可能影响投资节奏。2025年补贴政策已经改变供给结构。",
                "content_type": "paragraph",
            },
        ],
    )
    return project, document, chunks


def test_extract_claims_from_chinese_energy_chunks(db_session) -> None:
    project, document, chunks = create_article_chunks(db_session)

    claims = extract_claims_from_chunks(
        project_id=str(project.id),
        document_id=str(document.id),
        chunks=chunks,
        max_claims=10,
    )

    assert claims
    assert {claim["claim_type"] for claim in claims} >= {"forecast", "recommendation", "judgment", "fact"}
    assert all(claim["source_chunk_ids"] for claim in claims)
    assert claims[0]["jurisdiction"] == "China"
    assert claims[0]["confidence"] >= 0.55


def test_extract_claims_deduplicates_and_respects_max_claims(db_session) -> None:
    project, document, chunks = create_article_chunks(db_session)
    chunks[1].content = chunks[0].content

    claims = extract_claims_from_chunks(
        project_id=str(project.id),
        document_id=str(document.id),
        chunks=chunks,
        max_claims=1,
    )

    assert len(claims) == 1
    assert claims[0]["claim_text"]
