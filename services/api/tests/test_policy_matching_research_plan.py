from app.repositories.analysis_jobs import create_analysis_job
from app.repositories.analysis_results import get_analysis_result_by_job_id
from app.repositories.claims import list_claims
from app.repositories.document_chunks import create_document_chunks
from app.repositories.documents import create_document
from app.repositories.policies import create_policy
from app.repositories.policy_matches import list_policy_matches
from app.repositories.policy_sections import create_policy_sections
from app.repositories.policy_versions import create_policy_version
from app.repositories.projects import create_project
from app.research.plan_builder import build_research_plan
from app.research.plan_executor import execute_research_plan
from app.schemas.common import AnalysisJobRequest


def setup_research_plan_fixture(db_session):
    project = create_project(db_session, {"name": "Evidence plan project", "industry": "energy"})
    article = create_document(
        db_session,
        {
            "project_id": project.id,
            "document_role": "research_article",
            "title": "新能源消纳研究",
            "file_name": "article.txt",
            "file_type": ".txt",
            "parse_status": "parsed",
        },
    )
    create_document_chunks(
        db_session,
        [
            {
                "project_id": project.id,
                "document_id": article.id,
                "chunk_index": 0,
                "content": "中国新能源储能需求预计增长，电价政策和监管规则将影响投资节奏。",
                "content_type": "paragraph",
                "token_count": 30,
            }
        ],
    )
    policy = create_policy(
        db_session,
        {
            "title": "新能源储能电价政策",
            "normalized_title": "新能源储能电价政策",
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
            "normalized_text": "鼓励新能源储能投资，完善电价政策和监管规则。",
            "is_current": True,
        },
    )
    create_policy_sections(
        db_session,
        [
            {
                "policy_id": policy.id,
                "version_id": version.id,
                "heading": "电价政策",
                "section_path": "第一条",
                "content": "鼓励新能源储能投资，完善电价政策和监管规则。",
                "order_index": 0,
            }
        ],
    )
    job = create_analysis_job(
        db_session,
        {
            "project_id": project.id,
            "document_id": article.id,
            "mode": "policy_deep_dive",
            "status": "queued",
            "model_profile": "china_balanced",
        },
    )
    plan = build_research_plan(
        AnalysisJobRequest(
            project_id=str(project.id),
            document_ids=[str(article.id)],
            analysis_types=["policy_deep_dive"],
            model_profile="china_balanced",
        )
    )
    return project, article, job, plan


def test_research_plan_creates_claim_policy_matches_and_evidence(db_session) -> None:
    project, article, job, plan = setup_research_plan_fixture(db_session)

    result = execute_research_plan(db_session, job.id, plan)

    claims = list_claims(db_session, document_id=article.id)
    matches = list_policy_matches(db_session, analysis_id=result.id)
    result_from_db = get_analysis_result_by_job_id(db_session, job.id)

    assert claims
    assert matches
    assert matches[0].analysis_id == result.id
    assert result_from_db.report_json["claim_policy_map"]
    assert result_from_db.report_json["fact_boundaries"]["original_facts"]
    assert result_from_db.report_json["fact_boundaries"]["retrieved_facts"]
    assert result_from_db.report_json["fact_boundaries"]["model_reasoning"] == []
    assert result_from_db.summary["claim_count"] == len(claims)
    assert result_from_db.summary["policy_match_count"] == len(matches)
    assert result_from_db.project_id == project.id
