from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def create_project() -> str:
    response = client.post(
        "/api/projects",
        json={"name": "Analysis API project", "industry": "energy", "jurisdictions": ["China"]},
    )
    assert response.status_code == 201
    return response.json()["id"]


def upload_document(project_id: str, *, role: str, title: str, content: bytes) -> str:
    response = client.post(
        "/api/documents/upload",
        data={"project_id": project_id, "document_role": role, "title": title},
        files={"file": (f"{title}.txt", content, "text/plain")},
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_policy_candidate(project_id: str) -> str:
    document_id = upload_document(
        project_id,
        role="policy",
        title="Clean energy policy",
        content=b"Clean energy storage policy supports market reform in 2025.",
    )
    parse_response = client.post(f"/api/documents/{document_id}/parse")
    assert parse_response.status_code == 200
    ingest_response = client.post(
        "/api/policies/from-document",
        json={"document_id": document_id, "jurisdiction": "China", "policy_type": "notice"},
    )
    assert ingest_response.status_code == 201
    return ingest_response.json()["policy_id"]


def test_analysis_api_runs_research_plan_and_returns_steps_plan_and_result(tmp_path, monkeypatch) -> None:
    from app.db.config import settings

    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    project_id = create_project()
    create_policy_candidate(project_id)
    article_id = upload_document(
        project_id,
        role="research_article",
        title="Market article",
        content=b"China clean energy storage market reform signal in 2025.",
    )

    create_response = client.post(
        "/api/analysis/jobs",
        json={
            "project_id": project_id,
            "document_ids": [article_id],
            "analysis_types": ["policy_deep_dive"],
            "model_profile": "china_balanced",
        },
    )

    assert create_response.status_code == 201
    job_payload = create_response.json()
    assert job_payload["status"] == "completed"
    assert job_payload["result_id"]

    job_response = client.get(f"/api/analysis/jobs/{job_payload['id']}")
    assert job_response.status_code == 200
    assert job_response.json()["status"] == "completed"

    steps_response = client.get(f"/api/analysis/jobs/{job_payload['id']}/steps")
    assert steps_response.status_code == 200
    step_ids = [item["step_id"] for item in steps_response.json()["items"]]
    assert "collect_document_context" in step_ids
    assert "extract_article_signals" in step_ids
    assert "retrieve_policy_candidates" in step_ids
    assert "summarize_findings" in step_ids

    plan_response = client.get(f"/api/analysis/jobs/{job_payload['id']}/plan")
    assert plan_response.status_code == 200
    assert plan_response.json()["steps"][0]["step_id"] == "parse_document_if_needed"

    result_response = client.get(f"/api/analysis/jobs/{job_payload['id']}/result")
    assert result_response.status_code == 200
    result_payload = result_response.json()
    assert result_payload["related_policies"]
    assert result_payload["report_json"]["fact_boundaries"]["model_reasoning"] == []


def test_analysis_api_validates_project_document_and_empty_document_ids() -> None:
    project_id = create_project()
    other_project_id = create_project()
    document_id = upload_document(
        other_project_id,
        role="research_article",
        title="Other article",
        content=b"Other project text.",
    )

    empty_response = client.post(
        "/api/analysis/jobs",
        json={"project_id": project_id, "document_ids": [], "analysis_types": ["policy_deep_dive"]},
    )
    assert empty_response.status_code == 422

    missing_project = client.post(
        "/api/analysis/jobs",
        json={
            "project_id": "11111111-1111-4111-8111-111111111111",
            "document_ids": [document_id],
        },
    )
    assert missing_project.status_code == 404

    missing_document = client.post(
        "/api/analysis/jobs",
        json={
            "project_id": project_id,
            "document_ids": ["22222222-2222-4222-8222-222222222222"],
        },
    )
    assert missing_document.status_code == 404

    wrong_project = client.post(
        "/api/analysis/jobs",
        json={"project_id": project_id, "document_ids": [document_id]},
    )
    assert wrong_project.status_code == 409
