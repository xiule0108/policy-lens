from app.db.base import utc_now
from app.repositories.analysis_jobs import create_analysis_job, list_analysis_jobs, update_analysis_job_status
from app.repositories.analysis_results import create_analysis_result, get_analysis_result, get_analysis_result_by_job_id
from app.repositories.analysis_steps import (
    create_analysis_step,
    get_analysis_step_by_db_id,
    get_analysis_step_by_step_id,
    list_analysis_steps,
    update_analysis_step,
)
from app.repositories.projects import create_project


def test_analysis_job_step_and_result_repositories(db_session) -> None:
    project = create_project(db_session, {"name": "Analysis repo project"})
    job = create_analysis_job(
        db_session,
        {
            "project_id": project.id,
            "mode": "policy_deep_dive",
            "status": "queued",
            "model_profile": "china_balanced",
        },
    )

    started_at = utc_now()
    updated_job = update_analysis_job_status(
        db_session,
        job.id,
        status="running",
        progress=0.5,
        started_at=started_at,
    )

    assert updated_job is not None
    assert updated_job.status == "running"
    assert float(updated_job.progress) == 0.5
    assert list_analysis_jobs(db_session, project_id=project.id)[0].id == job.id

    step = create_analysis_step(
        db_session,
        {
            "job_id": job.id,
            "step_id": "collect_document_context",
            "tool_name": "collect_document_context",
            "status": "running",
            "input_ref": {"document_id": "doc"},
        },
    )
    updated_step = update_analysis_step(
        db_session,
        step.id,
        status="done",
        output_ref={"chunk_count": 2},
        token_usage={"total_tokens": 0},
        latency_ms=12,
    )

    assert get_analysis_step_by_db_id(db_session, step.id).id == step.id
    assert get_analysis_step_by_step_id(db_session, job.id, "collect_document_context").id == step.id
    assert list_analysis_steps(db_session, job.id)[0].status == "done"
    assert updated_step.output_ref == {"chunk_count": 2}

    result = create_analysis_result(
        db_session,
        {
            "project_id": project.id,
            "job_id": job.id,
            "summary": {"document_title": "Demo"},
            "claims": [{"claim_text": "Demo signal", "claim_type": "signal"}],
            "related_policies": [],
            "impact_matrix": [],
            "report_json": {"research_plan": {"plan_id": "plan_demo"}},
        },
    )

    assert get_analysis_result(db_session, result.id).id == result.id
    assert get_analysis_result_by_job_id(db_session, job.id).id == result.id
