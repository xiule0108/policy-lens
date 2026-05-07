from pathlib import Path

import pytest

from app.db.config import settings
from app.repositories.analysis_jobs import create_analysis_job, get_analysis_job
from app.repositories.analysis_results import get_analysis_result_by_job_id
from app.repositories.analysis_steps import get_analysis_step_by_step_id, list_analysis_steps
from app.repositories.document_chunks import create_document_chunks, count_document_chunks
from app.repositories.documents import create_document, get_document
from app.repositories.policies import create_policy
from app.repositories.policy_sections import create_policy_sections
from app.repositories.policy_versions import create_policy_version
from app.repositories.projects import create_project
from app.research.plan_builder import build_research_plan
from app.research.plan_executor import execute_research_plan
from app.schemas.common import AnalysisJobRequest


def create_research_document(db_session, project_id, *, parse_status: str = "parsed", storage_key: str | None = None):
    storage_key_value = storage_key if storage_key is not None else (
        "documents/demo/article.txt" if parse_status == "parsed" else None
    )
    document = create_document(
        db_session,
        {
            "project_id": project_id,
            "document_role": "research_article",
            "title": "Clean energy market note",
            "file_name": "article.txt",
            "file_type": ".txt",
            "file_size": 128,
            "storage_key": storage_key_value,
            "parse_status": parse_status,
            "metadata": {"content_type": "text/plain"},
        },
    )
    if parse_status == "parsed":
        create_document_chunks(
            db_session,
            [
                {
                    "document_id": document.id,
                    "project_id": project_id,
                    "chunk_index": 0,
                    "content": "China clean energy policy in 2025 supports storage and market reform.",
                    "content_type": "paragraph",
                    "token_count": 20,
                }
            ],
        )
    return document


def create_policy_candidate(db_session) -> None:
    policy = create_policy(
        db_session,
        {
            "title": "Clean Energy Storage Policy",
            "normalized_title": "clean energy storage policy",
            "issuer": "Energy Agency",
            "jurisdiction": "China",
            "policy_type": "notice",
            "status": "active",
        },
    )
    version = create_policy_version(
        db_session,
        {
            "policy_id": policy.id,
            "normalized_text": "Clean energy storage and market reform policy text.",
            "sha256": "policy-sha",
            "is_current": True,
        },
    )
    create_policy_sections(
        db_session,
        [
            {
                "policy_id": policy.id,
                "version_id": version.id,
                "content": "Support clean energy storage and market reform in 2025.",
                "order_index": 0,
                "token_count": 16,
                "metadata": {},
            }
        ],
    )


def build_job_and_plan(db_session, project_id, document_id):
    job = create_analysis_job(
        db_session,
        {
            "project_id": project_id,
            "document_id": document_id,
            "mode": "policy_deep_dive",
            "status": "queued",
            "model_profile": "china_balanced",
        },
    )
    plan = build_research_plan(
        AnalysisJobRequest(
            project_id=str(project_id),
            document_ids=[str(document_id)],
            analysis_types=["policy_deep_dive"],
            model_profile="china_balanced",
        )
    )
    return job, plan


def test_research_plan_executor_runs_parsed_document_without_reparsing(db_session) -> None:
    project = create_project(db_session, {"name": "Executor project"})
    document = create_research_document(db_session, project.id, parse_status="parsed")
    create_policy_candidate(db_session)
    job, plan = build_job_and_plan(db_session, project.id, document.id)

    result = execute_research_plan(db_session, job.id, plan)

    job_after = get_analysis_job(db_session, job.id)
    parse_step = get_analysis_step_by_step_id(db_session, job.id, "parse_document_if_needed")
    steps = list_analysis_steps(db_session, job.id)

    assert job_after.status == "completed"
    assert float(job_after.progress) == 1.0
    assert result.related_policies
    assert parse_step.status == "skipped"
    assert [step.step_id for step in steps][0] == "research_plan"
    assert get_analysis_result_by_job_id(db_session, job.id).id == result.id
    assert result.report_json["fact_boundaries"]["model_reasoning"] == []


def test_research_plan_executor_parses_pending_document(tmp_path, monkeypatch, db_session) -> None:
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    project = create_project(db_session, {"name": "Pending executor project"})
    storage_path = tmp_path / "documents" / str(project.id) / "article.txt"
    storage_path.parent.mkdir(parents=True)
    storage_path.write_text("Policy notice supports clean energy storage in 2025.", encoding="utf-8")
    document = create_research_document(
        db_session,
        project.id,
        parse_status="pending",
        storage_key=f"documents/{project.id}/article.txt",
    )
    job, plan = build_job_and_plan(db_session, project.id, document.id)

    execute_research_plan(db_session, job.id, plan)

    assert get_document(db_session, document.id).parse_status == "parsed"
    assert count_document_chunks(db_session, document.id) > 0
    assert get_analysis_job(db_session, job.id).status == "completed"


def test_research_plan_executor_marks_job_failed_on_step_error(db_session) -> None:
    project = create_project(db_session, {"name": "Failing executor project"})
    document = create_research_document(db_session, project.id, parse_status="pending", storage_key=None)
    job, plan = build_job_and_plan(db_session, project.id, document.id)

    with pytest.raises(Exception):
        execute_research_plan(db_session, job.id, plan)

    failed_job = get_analysis_job(db_session, job.id)
    parse_step = get_analysis_step_by_step_id(db_session, job.id, "parse_document_if_needed")
    assert failed_job.status == "failed"
    assert failed_job.error_message
    assert parse_step.status == "failed"


def test_research_plan_executor_marks_job_failed_when_result_persistence_fails(db_session, monkeypatch) -> None:
    project = create_project(db_session, {"name": "Persist failure project"})
    document = create_research_document(db_session, project.id, parse_status="parsed")
    job, plan = build_job_and_plan(db_session, project.id, document.id)

    def fail_persist(*args, **kwargs):
        raise RuntimeError("persist failed")

    monkeypatch.setattr("app.research.plan_executor._persist_result", fail_persist)

    with pytest.raises(RuntimeError, match="persist failed"):
        execute_research_plan(db_session, job.id, plan)

    failed_job = get_analysis_job(db_session, job.id)
    assert failed_job.status == "failed"
    assert "persist failed" in failed_job.error_message
    assert failed_job.finished_at is not None
