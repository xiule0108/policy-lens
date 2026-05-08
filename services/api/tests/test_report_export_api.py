import json
import zipfile

from fastapi.testclient import TestClient

from app.db.config import settings
from app.main import app
from app.repositories.analysis_jobs import create_analysis_job
from app.repositories.analysis_results import create_analysis_result
from app.repositories.projects import create_project


client = TestClient(app)


def create_report_result(db_session, *, report_markdown: str | None = "# Report"):
    project = create_project(db_session, {"name": "Report export API project"})
    job = create_analysis_job(
        db_session,
        {"project_id": project.id, "mode": "policy_deep_dive", "status": "completed", "progress": 1},
    )
    result = create_analysis_result(
        db_session,
        {
            "project_id": project.id,
            "job_id": job.id,
            "summary": {"document_title": "API report"},
            "claims": [{"claim_id": "claim-1", "claim_text": "政策支持储能"}],
            "related_policies": [{"policy_id": "policy-1", "title": "储能政策"}],
            "impact_matrix": [{"impact_subject": "grid"}],
            "report_markdown": report_markdown,
            "report_json": {
                "claim_policy_map": [{"claim_id": "claim-1"}],
                "fact_boundaries": {"original_facts": [], "retrieved_facts": [], "model_reasoning": []},
                "report_outline": {"generation_method": "deterministic_rule_based", "llm_used": False},
            },
        },
    )
    return project, job, result


def test_report_export_api_create_detail_and_download(tmp_path, monkeypatch, db_session) -> None:
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    _project, job, _result = create_report_result(db_session)

    create_response = client.post(
        "/api/exports/report",
        json={"job_id": str(job.id), "formats": ["markdown", "json", "html"]},
    )

    assert create_response.status_code == 202
    payload = create_response.json()
    assert payload["status"] == "completed"
    assert payload["bundle_path"] == f"exports/{payload['export_id']}/report_export_bundle.zip"

    detail_response = client.get(f"/api/exports/{payload['export_id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["export_type"] == "report"

    download_response = client.get(f"/api/exports/{payload['export_id']}/download")
    assert download_response.status_code == 200
    assert download_response.headers["content-type"] == "application/zip"
    assert f"report_export_{payload['export_id']}.zip" in download_response.headers["content-disposition"]

    with zipfile.ZipFile(tmp_path / payload["bundle_path"]) as bundle:
        assert "manifest.json" in bundle.namelist()
        assert "reports/report.md" in bundle.namelist()
        manifest = json.loads(bundle.read("manifest.json"))
    assert manifest["job_id"] == str(job.id)


def test_report_export_api_validation_errors(tmp_path, monkeypatch, db_session) -> None:
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    _project, job, result = create_report_result(db_session, report_markdown=None)

    assert client.post("/api/exports/report", json={}).status_code == 422
    assert client.post("/api/exports/report", json={"job_id": "not-a-uuid"}).status_code == 422
    assert client.post("/api/exports/report", json={"formats": ["docx"], "job_id": str(job.id)}).status_code == 422
    assert client.post("/api/exports/report", json={"report_format": "pdf", "job_id": str(job.id)}).status_code == 422

    missing_job_response = client.post(
        "/api/exports/report",
        json={"job_id": "11111111-1111-4111-8111-111111111111"},
    )
    assert missing_job_response.status_code == 404

    empty_report_response = client.post("/api/exports/report", json={"analysis_id": str(result.id)})
    assert empty_report_response.status_code == 422
