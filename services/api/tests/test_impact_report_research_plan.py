from app.repositories.analysis_jobs import create_analysis_job
from app.repositories.analysis_results import get_analysis_result_by_job_id
from app.repositories.document_chunks import create_document_chunks
from app.repositories.documents import create_document
from app.repositories.impact_items import list_impact_items
from app.repositories.policies import create_policy
from app.repositories.policy_matches import list_policy_matches
from app.repositories.policy_sections import create_policy_sections
from app.repositories.policy_versions import create_policy_version
from app.repositories.projects import create_project
from app.research.plan_builder import build_research_plan
from app.research.plan_executor import execute_research_plan
from app.schemas.common import AnalysisJobRequest


def setup_impact_plan_fixture(db_session):
    project = create_project(db_session, {"name": "Impact plan project", "industry": "energy"})
    article = create_document(
        db_session,
        {
            "project_id": project.id,
            "document_role": "research_article",
            "title": "新能源投资研究",
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
                "content": "中国新能源储能需求预计在2026年增长，电价政策将支持投资并改善电网消纳。",
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
            "normalized_text": "鼓励新能源储能投资，完善电价政策和电网消纳机制。",
            "is_current": True,
        },
    )
    create_policy_sections(
        db_session,
        [
            {
                "policy_id": policy.id,
                "version_id": version.id,
                "heading": "电价与消纳",
                "section_path": "第一条",
                "content": "鼓励新能源储能投资，完善电价政策和电网消纳机制。",
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
    return project, job, plan


def test_research_plan_persists_impact_matrix_and_markdown_report(db_session) -> None:
    _project, job, plan = setup_impact_plan_fixture(db_session)

    result = execute_research_plan(db_session, job.id, plan)

    impact_items = list_impact_items(db_session, analysis_id=result.id)
    result_from_db = get_analysis_result_by_job_id(db_session, job.id)

    assert impact_items
    assert impact_items[0].analysis_id == result.id
    assert impact_items[0].citations
    policy_matches = list_policy_matches(db_session, analysis_id=result.id)
    policy_match_ids = {str(match.id) for match in policy_matches}
    impact_policy_match_id = impact_items[0].citations[1]["policy_match_id"]
    assert impact_policy_match_id in policy_match_ids
    assert result_from_db.impact_matrix
    assert result_from_db.impact_matrix[0]["citations"][1]["policy_match_id"] in policy_match_ids
    persisted_step_impact = result_from_db.report_json["step_outputs"]["build_impact_matrix"]["impact_matrix"][0]
    assert persisted_step_impact["citations"][1]["policy_match_id"] in policy_match_ids
    assert result_from_db.report_markdown.startswith("# 政策与市场研究解析报告")
    assert result_from_db.report_json["report_outline"]["generation_method"] == "deterministic_rule_based"
    assert result_from_db.report_json["report_outline"]["llm_used"] is False
