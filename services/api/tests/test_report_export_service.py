import json
import zipfile

import pytest

from app.db.config import settings
from app.repositories.analysis_jobs import create_analysis_job
from app.repositories.analysis_results import create_analysis_result
from app.repositories.exports import get_export
from app.repositories.projects import create_project
from app.schemas.common import ReportExportRequest
from app.services.report_export_service import (
    ReportExportNotFoundError,
    ReportExportValidationError,
    create_report_export,
)


def create_analysis_result_fixture(db_session, *, report_markdown: str | None = "# Report"):
    project = create_project(db_session, {"name": "Report export service project"})
    job = create_analysis_job(
        db_session,
        {
            "project_id": project.id,
            "mode": "policy_deep_dive",
            "status": "completed",
            "progress": 1,
        },
    )
    result = create_analysis_result(
        db_session,
        {
            "project_id": project.id,
            "job_id": job.id,
            "summary": {"document_title": "Energy report"},
            "claims": [{"claim_id": "claim-1", "claim_text": "储能需求增长"}],
            "related_policies": [{"policy_id": "policy-1", "title": "储能政策"}],
            "impact_matrix": [{"impact_subject": "grid", "impact_direction": "positive"}],
            "report_markdown": report_markdown,
            "report_json": {
                "claim_policy_map": [{"claim_id": "claim-1", "matches": []}],
                "fact_boundaries": {"original_facts": [], "retrieved_facts": [], "model_reasoning": []},
                "report_outline": {"generation_method": "deterministic_rule_based", "llm_used": False},
            },
        },
    )
    return project, job, result


def test_report_export_creates_zip_bundle(tmp_path, monkeypatch, db_session) -> None:
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    _project, job, result = create_analysis_result_fixture(db_session)

    response = create_report_export(
        db_session,
        ReportExportRequest(job_id=job.id, formats=["markdown", "json", "html"]),
    )

    assert response.status == "completed"
    assert response.bundle_path == f"exports/{response.export_id}/report_export_bundle.zip"
    assert not response.bundle_path.startswith(str(tmp_path))
    db_export = get_export(db_session, response.export_id)
    assert db_export.status == "completed"
    assert db_export.storage_key == response.bundle_path
    assert db_export.analysis_id == result.id

    with zipfile.ZipFile(tmp_path / response.bundle_path) as bundle:
        names = set(bundle.namelist())
        assert "manifest.json" in names
        assert "reports/report.md" in names
        assert "reports/report.json" in names
        assert "reports/report.html" in names
        assert "evidence/evidence.json" in names
        assert "impact_matrix/impact_matrix.json" in names
        assert "policy_matches/policy_matches.json" in names
        assert "checksums/sha256.txt" in names
        manifest = json.loads(bundle.read("manifest.json"))
        report_json = json.loads(bundle.read("reports/report.json"))

    assert manifest["export_type"] == "report"
    assert manifest["analysis_id"] == str(result.id)
    assert manifest["paths"]["markdown"] == "reports/report.md"
    assert manifest["generation_method"] == "deterministic_rule_based"
    assert manifest["llm_used"] is False
    assert report_json["summary"]["document_title"] == "Energy report"


def test_report_export_validates_source_and_report(tmp_path, monkeypatch, db_session) -> None:
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    _project, job, result = create_analysis_result_fixture(db_session, report_markdown=None)

    with pytest.raises(ReportExportValidationError, match="job_id or analysis_id"):
        create_report_export(db_session, ReportExportRequest())

    with pytest.raises(ReportExportNotFoundError, match="Analysis job not found"):
        create_report_export(
            db_session,
            ReportExportRequest(job_id="11111111-1111-4111-8111-111111111111"),
        )

    with pytest.raises(ReportExportValidationError, match="report_markdown"):
        create_report_export(db_session, ReportExportRequest(analysis_id=result.id))

    assert job.id
