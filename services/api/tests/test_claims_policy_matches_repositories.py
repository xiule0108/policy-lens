from uuid import uuid4

from app.repositories.claims import create_claims, get_claim, list_claims
from app.repositories.documents import create_document
from app.repositories.policies import create_policy
from app.repositories.policy_matches import (
    create_policy_matches,
    delete_policy_matches_for_analysis,
    get_policy_match,
    list_policy_matches,
)
from app.repositories.policy_sections import create_policy_sections
from app.repositories.policy_versions import create_policy_version
from app.repositories.projects import create_project


def setup_repository_fixture(db_session):
    project = create_project(db_session, {"name": "Evidence repository project"})
    document = create_document(
        db_session,
        {
            "project_id": project.id,
            "document_role": "research_article",
            "title": "Market note",
            "file_name": "article.txt",
            "file_type": ".txt",
            "parse_status": "parsed",
        },
    )
    policy = create_policy(db_session, {"title": "Energy policy", "jurisdiction": "China"})
    version = create_policy_version(db_session, {"policy_id": policy.id, "normalized_text": "Energy text"})
    section = create_policy_sections(
        db_session,
        [
            {
                "policy_id": policy.id,
                "version_id": version.id,
                "content": "Energy policy section",
                "order_index": 0,
            }
        ],
    )[0]
    return project, document, policy, section


def test_claims_repository_deduplicates_by_document_and_text(db_session) -> None:
    project, document, _policy, _section = setup_repository_fixture(db_session)

    claims = create_claims(
        db_session,
        [
            {
                "project_id": project.id,
                "document_id": document.id,
                "claim_text": "Energy storage demand grows.",
                "claim_type": "forecast",
                "confidence": 0.7,
                "source_chunk_ids": ["chunk-1"],
            },
            {
                "project_id": project.id,
                "document_id": document.id,
                "claim_text": "Energy storage demand grows.",
                "claim_type": "forecast",
                "confidence": 0.7,
                "source_chunk_ids": ["chunk-1"],
            },
        ],
    )

    assert len(claims) == 2
    assert claims[0].id == claims[1].id
    assert get_claim(db_session, claims[0].id).claim_text == "Energy storage demand grows."
    assert [claim.id for claim in list_claims(db_session, document_id=document.id)] == [claims[0].id]


def test_policy_matches_repository_filters_and_deletes(db_session) -> None:
    project, document, policy, section = setup_repository_fixture(db_session)
    claim = create_claims(
        db_session,
        [
            {
                "project_id": project.id,
                "document_id": document.id,
                "claim_text": "Energy policy affects investment.",
                "claim_type": "judgment",
                "source_chunk_ids": ["chunk-1"],
            }
        ],
    )[0]
    analysis_id = uuid4()

    matches = create_policy_matches(
        db_session,
        [
            {
                "project_id": project.id,
                "analysis_id": analysis_id,
                "claim_id": claim.id,
                "policy_id": policy.id,
                "policy_section_id": section.id,
                "match_type": "implicit",
                "relevance_score": 0.6,
                "reason": "Matched energy policy terms.",
                "evidence": {
                    "source": "deterministic_policy_matcher",
                    "source_chunk_id": "chunk-1",
                    "policy_section_id": str(section.id),
                    "quote": "Energy policy section",
                },
            }
        ],
    )

    assert get_policy_match(db_session, matches[0].id).id == matches[0].id
    assert list_policy_matches(db_session, analysis_id=analysis_id)[0].id == matches[0].id
    assert list_policy_matches(db_session, claim_id=claim.id)[0].id == matches[0].id
    assert list_policy_matches(db_session, policy_id=policy.id)[0].id == matches[0].id

    delete_policy_matches_for_analysis(db_session, analysis_id)

    assert list_policy_matches(db_session, analysis_id=analysis_id) == []
