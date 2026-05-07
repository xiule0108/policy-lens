from app.repositories.claims import create_claims
from app.repositories.documents import create_document
from app.repositories.policies import create_policy
from app.repositories.policy_sections import create_policy_sections
from app.repositories.policy_versions import create_policy_version
from app.repositories.projects import create_project
from app.services.policy_matching_service import match_claims_to_policy_sections


def setup_policy_match_fixture(db_session):
    project = create_project(db_session, {"name": "Policy matching project"})
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
    claim = create_claims(
        db_session,
        [
            {
                "project_id": project.id,
                "document_id": document.id,
                "claim_text": "中国新能源储能需求预计增长，监管政策将影响电价和投资节奏。",
                "claim_type": "forecast",
                "jurisdiction": "China",
                "confidence": 0.7,
                "source_chunk_ids": ["chunk-1"],
            }
        ],
    )[0]
    policy = create_policy(
        db_session,
        {
            "title": "新能源储能政策通知",
            "normalized_title": "新能源储能政策通知",
            "issuer": "国家能源局",
            "jurisdiction": "China",
            "policy_type": "notice",
            "status": "active",
        },
    )
    version = create_policy_version(
        db_session,
        {
            "policy_id": policy.id,
            "normalized_text": "支持新能源储能发展，完善电价机制。",
            "is_current": True,
        },
    )
    sections = create_policy_sections(
        db_session,
        [
            {
                "policy_id": policy.id,
                "version_id": version.id,
                "heading": "储能与电价机制",
                "section_path": "第一条",
                "content": "鼓励新能源储能投资，完善现货市场、电价机制和监管规则。",
                "order_index": 0,
            }
        ],
    )
    return claim, policy, sections[0]


def test_match_claims_to_policy_sections_builds_evidence(db_session) -> None:
    claim, policy, section = setup_policy_match_fixture(db_session)

    matches = match_claims_to_policy_sections(db_session, [claim], limit_per_claim=5)

    assert len(matches) == 1
    match = matches[0]
    assert match["claim_id"] == str(claim.id)
    assert match["policy_id"] == str(policy.id)
    assert match["policy_section_id"] == str(section.id)
    assert match["match_type"] in {"explicit", "implicit"}
    assert match["relevance_score"] > 0
    assert "新能源" in match["evidence"]["matched_terms"]
    assert match["evidence"]["claim_source_chunk_ids"] == ["chunk-1"]
    assert match["evidence"]["policy_quote"]
    assert match["evidence"]["fact_boundary"] == "retrieved_fact"
    assert match["evidence"]["score_components"]["jurisdiction_match"] is True


def test_match_claims_to_policy_sections_omits_zero_score(db_session) -> None:
    claim, _policy, _section = setup_policy_match_fixture(db_session)
    claim.claim_text = "Unrelated semiconductor export statement."
    claim.jurisdiction = "US"

    assert match_claims_to_policy_sections(db_session, [claim], limit_per_claim=5) == []
