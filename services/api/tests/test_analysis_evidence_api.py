from fastapi.testclient import TestClient

from app.db.config import settings
from app.main import app
from app.repositories.analysis_jobs import create_analysis_job
from app.repositories.documents import create_document
from app.repositories.projects import create_project


client = TestClient(app)


def create_project_via_api() -> str:
    response = client.post(
        "/api/projects",
        json={"name": "Evidence API project", "industry": "energy", "jurisdictions": ["China"]},
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


def create_policy(project_id: str) -> str:
    policy_document_id = upload_document(
        project_id,
        role="policy",
        title="新能源储能电价政策",
        content="鼓励新能源储能投资，完善电价政策和监管规则。".encode(),
    )
    parse_response = client.post(f"/api/documents/{policy_document_id}/parse")
    assert parse_response.status_code == 200
    ingest_response = client.post(
        "/api/policies/from-document",
        json={
            "document_id": policy_document_id,
            "title": "新能源储能电价政策",
            "jurisdiction": "China",
            "policy_type": "notice",
        },
    )
    assert ingest_response.status_code == 201
    return ingest_response.json()["policy_id"]


def test_analysis_evidence_api_full_flow(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    project_id = create_project_via_api()
    create_policy(project_id)
    article_id = upload_document(
        project_id,
        role="research_article",
        title="新能源消纳研究",
        content="中国新能源储能需求预计增长，电价政策和监管规则将影响投资节奏。".encode(),
    )

    job_response = client.post(
        "/api/analysis/jobs",
        json={
            "project_id": project_id,
            "document_ids": [article_id],
            "analysis_types": ["policy_deep_dive"],
        },
    )

    assert job_response.status_code == 201
    job_id = job_response.json()["id"]

    claims_response = client.get(f"/api/analysis/jobs/{job_id}/claims")
    assert claims_response.status_code == 200
    assert claims_response.json()["items"][0]["claim_text"]

    matches_response = client.get(f"/api/analysis/jobs/{job_id}/policy-matches")
    assert matches_response.status_code == 200
    match_payload = matches_response.json()["items"][0]
    assert match_payload["evidence"]["source"] == "deterministic_policy_matcher"
    assert match_payload["analysis_id"] == job_response.json()["result_id"]

    evidence_response = client.get(f"/api/analysis/jobs/{job_id}/evidence")
    assert evidence_response.status_code == 200
    evidence_payload = evidence_response.json()
    assert evidence_payload["job_id"] == job_id
    assert evidence_payload["result_id"] == job_response.json()["result_id"]
    assert evidence_payload["claim_policy_map"]
    assert evidence_payload["fact_boundaries"]["model_reasoning"] == []


def test_analysis_evidence_api_errors(db_session) -> None:
    assert client.get("/api/analysis/jobs/not-a-uuid/claims").status_code == 422
    assert client.get("/api/analysis/jobs/not-a-uuid/policy-matches").status_code == 422
    assert client.get("/api/analysis/jobs/not-a-uuid/evidence").status_code == 422

    missing_job_id = "11111111-1111-4111-8111-111111111111"
    assert client.get(f"/api/analysis/jobs/{missing_job_id}/claims").status_code == 404
    assert client.get(f"/api/analysis/jobs/{missing_job_id}/policy-matches").status_code == 404
    assert client.get(f"/api/analysis/jobs/{missing_job_id}/evidence").status_code == 404

    project = create_project(db_session, {"name": "Job without result"})
    document = create_document(
        db_session,
        {
            "project_id": project.id,
            "document_role": "research_article",
            "title": "Queued article",
            "file_name": "article.txt",
            "file_type": ".txt",
            "parse_status": "pending",
        },
    )
    job = create_analysis_job(
        db_session,
        {
            "project_id": project.id,
            "document_id": document.id,
            "mode": "policy_deep_dive",
            "status": "queued",
        },
    )

    assert client.get(f"/api/analysis/jobs/{job.id}/evidence").status_code == 404
