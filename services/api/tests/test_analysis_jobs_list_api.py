from fastapi.testclient import TestClient

from app.main import app
from app.repositories.analysis_jobs import create_analysis_job
from app.repositories.analysis_results import create_analysis_result
from app.repositories.projects import create_project


client = TestClient(app)


def test_list_analysis_jobs_with_project_filter_and_result_id(db_session) -> None:
    project = create_project(db_session, {"name": "Analysis jobs list project"})
    job = create_analysis_job(
        db_session,
        {"project_id": project.id, "mode": "policy_deep_dive", "status": "completed", "progress": 1},
    )
    result = create_analysis_result(
        db_session,
        {
            "project_id": project.id,
            "job_id": job.id,
            "summary": {},
            "claims": [],
            "related_policies": [],
            "impact_matrix": [],
            "report_json": {},
        },
    )

    response = client.get(f"/api/analysis/jobs?project_id={project.id}")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    assert payload["items"][0]["id"] == str(job.id)
    assert payload["items"][0]["result_id"] == str(result.id)


def test_list_analysis_jobs_without_project_filter(db_session) -> None:
    project = create_project(db_session, {"name": "Analysis jobs global list"})
    create_analysis_job(db_session, {"project_id": project.id, "mode": "policy_deep_dive", "status": "queued"})

    response = client.get("/api/analysis/jobs")

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


def test_list_analysis_jobs_validates_project_id(db_session) -> None:
    assert client.get("/api/analysis/jobs?project_id=not-a-uuid").status_code == 422

    missing_project_id = "11111111-1111-4111-8111-111111111111"
    assert client.get(f"/api/analysis/jobs?project_id={missing_project_id}").status_code == 404
