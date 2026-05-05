from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_provider_presets_include_china_and_custom_options() -> None:
    response = client.get("/api/llm/providers")
    assert response.status_code == 200
    provider_ids = {item["id"] for item in response.json()["items"]}
    assert "dashscope" in provider_ids
    assert "qianfan" in provider_ids
    assert "hunyuan" in provider_ids
    assert "volcark" in provider_ids
    assert "zhipu" in provider_ids
    assert "deepseek" in provider_ids
    assert "kimi" in provider_ids
    assert "minimax" in provider_ids
    assert "spark" in provider_ids
    assert "openai_compatible_custom" in provider_ids
    assert "local" in provider_ids


def test_policy_original_export_returns_manifest() -> None:
    response = client.post(
        "/api/exports/policy-originals",
        json={
            "project_id": "project_demo_001",
            "policy_ids": ["policy_demo_001"],
            "mode": "related_policy_bundle",
        },
    )
    assert response.status_code == 202
    payload = response.json()
    assert payload["manifest"]["bundle_structure"] == [
        "manifest.json",
        "policies/",
        "cited_sections/",
        "snapshots/",
        "mappings/",
        "checksums/",
    ]
