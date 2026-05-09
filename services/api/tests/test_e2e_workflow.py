import zipfile

from fastapi.testclient import TestClient

from app.db.config import settings
from app.main import app


client = TestClient(app)


POLICY_TEXT = """【示例数据】本文件为 PolicyLens 本地演示用虚构政策文本，不代表真实政策文件。

# 示例：关于促进新型储能参与电力市场的通知

发布机构：示例能源主管部门

一、适用范围
本通知适用于中国新能源、储能、电力现货市场和绿电交易相关主体。

二、电价机制
鼓励新型储能参与电力现货市场，完善电价机制和容量补偿机制，支持新能源消纳。

三、并网消纳
电网企业应优化并网服务，提升储能调节能力，促进绿电交易和绿证使用。

四、监管要求
市场主体应按要求披露交易信息，防范投资风险和价格异常波动。
"""


ARTICLE_TEXT = """中国新能源行业在2026年预计继续提升储能投资强度。
电力现货市场和绿电交易扩容后，电价机制将影响储能项目收益。
如果并网消纳能力改善，新能源发电企业可能获得更稳定的市场需求。
但储能成本、监管要求和价格波动仍然带来投资风险，需要持续跟踪政策执行强度。
"""


def test_v0_1_demo_workflow_through_backend_api(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))

    project_response = client.post(
        "/api/projects",
        json={
            "name": "PolicyLens v0.1 demo",
            "description": "End-to-end demo workflow",
            "industry": "energy",
            "jurisdictions": ["China"],
        },
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    policy_upload = client.post(
        "/api/documents/upload",
        data={"project_id": project_id, "document_role": "policy", "title": "示例储能政策"},
        files={"file": ("demo-policy-notice.txt", POLICY_TEXT.encode(), "text/plain")},
    )
    assert policy_upload.status_code == 201
    policy_document_id = policy_upload.json()["id"]

    policy_parse = client.post(f"/api/documents/{policy_document_id}/parse")
    assert policy_parse.status_code == 200

    policy_ingest = client.post(
        "/api/policies/from-document",
        json={
            "document_id": policy_document_id,
            "title": "示例：关于促进新型储能参与电力市场的通知",
            "issuer": "示例能源主管部门",
            "jurisdiction": "China",
            "policy_type": "notice",
            "status": "active",
            "version_label": "demo-v1",
        },
    )
    assert policy_ingest.status_code == 201
    policy_id = policy_ingest.json()["policy_id"]

    article_upload = client.post(
        "/api/documents/upload",
        data={"project_id": project_id, "document_role": "research_article", "title": "新能源储能市场研究"},
        files={"file": ("demo-research-article.txt", ARTICLE_TEXT.encode(), "text/plain")},
    )
    assert article_upload.status_code == 201
    article_document_id = article_upload.json()["id"]

    article_parse = client.post(f"/api/documents/{article_document_id}/parse")
    assert article_parse.status_code == 200

    analysis_response = client.post(
        "/api/analysis/jobs",
        json={
            "project_id": project_id,
            "document_ids": [article_document_id],
            "analysis_types": ["policy_deep_dive"],
            "model_profile": "china_balanced",
        },
    )
    assert analysis_response.status_code == 201
    analysis_payload = analysis_response.json()
    assert analysis_payload["status"] == "completed"
    job_id = analysis_payload["id"]

    evidence_response = client.get(f"/api/analysis/jobs/{job_id}/evidence")
    assert evidence_response.status_code == 200
    assert evidence_response.json()["claim_policy_map"]

    impact_response = client.get(f"/api/analysis/jobs/{job_id}/impact-matrix")
    assert impact_response.status_code == 200
    assert impact_response.json()["items"]

    report_response = client.get(f"/api/analysis/jobs/{job_id}/report")
    assert report_response.status_code == 200
    assert "# 政策与市场研究解析报告" in report_response.json()["report_markdown"]

    result_response = client.get(f"/api/analysis/jobs/{job_id}/result")
    assert result_response.status_code == 200
    result_payload = result_response.json()
    assert result_payload["claims"]
    assert result_payload["impact_matrix"]

    matches_response = client.get(f"/api/analysis/jobs/{job_id}/policy-matches")
    assert matches_response.status_code == 200
    assert matches_response.json()["items"]

    report_export = client.post(
        "/api/exports/report",
        json={"job_id": job_id, "formats": ["markdown", "json", "html"]},
    )
    assert report_export.status_code == 202
    report_export_payload = report_export.json()
    assert report_export_payload["status"] == "completed"

    policy_export = client.post(
        "/api/exports/policy-originals",
        json={"project_id": project_id, "policy_ids": [policy_id], "mode": "single_policy_full_text"},
    )
    assert policy_export.status_code == 202
    policy_export_payload = policy_export.json()
    assert policy_export_payload["status"] == "completed"

    report_zip = tmp_path / report_export_payload["bundle_path"]
    policy_zip = tmp_path / policy_export_payload["bundle_path"]
    assert report_zip.is_file()
    assert policy_zip.is_file()

    with zipfile.ZipFile(report_zip) as bundle:
        assert "manifest.json" in bundle.namelist()
        assert "reports/report.md" in bundle.namelist()
    with zipfile.ZipFile(policy_zip) as bundle:
        assert "manifest.json" in bundle.namelist()
