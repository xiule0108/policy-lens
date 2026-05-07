from fastapi.testclient import TestClient

from app.main import app
from app.services.llm_gateway import LLMChatResponse


client = TestClient(app)


def test_llm_provider_list_returns_presets_without_secret_values(monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "real-secret-value")

    response = client.get("/api/llm/providers")

    assert response.status_code == 200
    providers = {item["id"]: item for item in response.json()["items"]}
    assert "dashscope" in providers
    assert "qianfan" in providers
    assert "hunyuan" in providers
    assert "volcark" in providers
    assert "zhipu" in providers
    assert "deepseek" in providers
    assert "kimi" in providers
    assert "minimax" in providers
    assert "spark" in providers
    assert "openai_compatible_custom" in providers
    assert "local" in providers
    assert providers["deepseek"]["api_key_configured"] is True
    assert "real-secret-value" not in response.text


def test_llm_provider_upsert_user_provider_and_merge_with_presets(monkeypatch) -> None:
    monkeypatch.setenv("CUSTOM_LLM_API_KEY", "secret-value")

    response = client.post(
        "/api/llm/providers",
        json={
            "provider_id": "openai_compatible_custom",
            "display_name": "Custom Gateway",
            "provider_family": "openai_compatible",
            "aliases": ["custom"],
            "api_key_env": "CUSTOM_LLM_API_KEY",
            "base_url": "https://models.example.com/v1",
            "model_name": "configured-by-user",
            "enabled": True,
            "openai_compatible": True,
            "local_provider": False,
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == "openai_compatible_custom"
    assert response.json()["api_key_configured"] is True
    assert "secret-value" not in response.text

    list_response = client.get("/api/llm/providers")
    assert list_response.status_code == 200
    custom = {item["id"]: item for item in list_response.json()["items"]}["openai_compatible_custom"]
    assert custom["display_name"] == "Custom Gateway"
    assert custom["model_name"] == "configured-by-user"
    assert custom["api_key_configured"] is True


def test_llm_provider_preset_api_key_env_falls_back_when_user_omits_it(monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "deepseek-secret-value")
    monkeypatch.setenv("CUSTOM_LLM_API_KEY", "custom-secret-value")

    deepseek_response = client.post(
        "/api/llm/providers",
        json={
            "provider_id": "deepseek",
            "display_name": "DeepSeek Configured",
            "provider_family": "deepseek",
            "base_url": "https://models.example.com/v1",
            "model_name": "configured-by-user",
            "enabled": True,
        },
    )
    assert deepseek_response.status_code == 201
    assert deepseek_response.json()["api_key_env"] == "DEEPSEEK_API_KEY"
    assert deepseek_response.json()["api_key_configured"] is True
    assert "deepseek-secret-value" not in deepseek_response.text

    custom_response = client.post(
        "/api/llm/providers",
        json={
            "provider_id": "openai_compatible_custom",
            "display_name": "Custom Configured",
            "provider_family": "openai_compatible",
            "base_url": "https://custom.example.com/v1",
            "model_name": "configured-by-user",
            "enabled": True,
        },
    )
    assert custom_response.status_code == 201
    assert custom_response.json()["api_key_env"] == "CUSTOM_LLM_API_KEY"
    assert custom_response.json()["api_key_configured"] is True
    assert "custom-secret-value" not in custom_response.text


def test_llm_provider_test_requires_model_and_api_key(monkeypatch) -> None:
    monkeypatch.delenv("CUSTOM_LLM_API_KEY", raising=False)
    create_response = client.post(
        "/api/llm/providers",
        json={
            "provider_id": "needs_model",
            "display_name": "Needs Model",
            "provider_family": "openai_compatible",
            "api_key_env": "CUSTOM_LLM_API_KEY",
            "base_url": "https://models.example.com/v1",
            "model_name": "",
            "enabled": True,
        },
    )
    assert create_response.status_code == 201

    missing_model = client.post("/api/llm/providers/needs_model/test", json={})
    assert missing_model.status_code == 422

    missing_key = client.post(
        "/api/llm/providers/needs_model/test",
        json={"model": "configured-by-user"},
    )
    assert missing_key.status_code == 422


def test_llm_provider_test_success_uses_gateway(monkeypatch) -> None:
    client.post(
        "/api/llm/providers",
        json={
            "provider_id": "testable",
            "display_name": "Testable Provider",
            "provider_family": "openai_compatible",
            "api_key_env": None,
            "base_url": "http://localhost:11434/v1",
            "model_name": "local-model",
            "enabled": True,
            "local_provider": True,
        },
    )

    def fake_chat_completion(session, request, transport=None):
        assert request.provider_key == "testable"
        assert request.model == "local-model"
        return LLMChatResponse(
            provider_key=request.provider_key,
            model=request.model,
            content="provider ok",
            raw_response={"choices": [{"message": {"content": "provider ok"}}]},
            token_usage={"total_tokens": 3},
            latency_ms=12,
        )

    monkeypatch.setattr("app.routers.llm.chat_completion", fake_chat_completion)

    response = client.post("/api/llm/providers/testable/test", json={})

    assert response.status_code == 200
    assert response.json()["status"] == "passed"
    assert response.json()["message"] == "provider ok"
    assert response.json()["token_usage"] == {"total_tokens": 3}


def test_llm_chat_success_uses_gateway(monkeypatch) -> None:
    client.post(
        "/api/llm/providers",
        json={
            "provider_id": "chat_provider",
            "display_name": "Chat Provider",
            "provider_family": "openai_compatible",
            "api_key_env": None,
            "base_url": "http://localhost:11434/v1",
            "model_name": "local-model",
            "enabled": True,
            "local_provider": True,
        },
    )

    def fake_chat_completion(session, request, transport=None):
        assert request.provider_key == "chat_provider"
        assert request.messages[0].content == "hello"
        return LLMChatResponse(
            provider_key=request.provider_key,
            model=request.model,
            content="chat ok",
            raw_response={},
            token_usage={"total_tokens": 5},
            latency_ms=20,
        )

    monkeypatch.setattr("app.routers.llm.chat_completion", fake_chat_completion)

    response = client.post(
        "/api/llm/chat",
        json={
            "provider_id": "chat_provider",
            "messages": [{"role": "user", "content": "hello"}],
        },
    )

    assert response.status_code == 200
    assert response.json()["content"] == "chat ok"
    assert response.json()["token_usage"] == {"total_tokens": 5}
    assert response.json()["step_id"] is None


def test_llm_chat_rejects_missing_job_id_before_gateway_call(monkeypatch) -> None:
    client.post(
        "/api/llm/providers",
        json={
            "provider_id": "job_checked_provider",
            "display_name": "Job Checked Provider",
            "provider_family": "openai_compatible",
            "api_key_env": None,
            "base_url": "http://localhost:11434/v1",
            "model_name": "local-model",
            "enabled": True,
            "local_provider": True,
        },
    )
    called = False

    def fake_chat_completion(session, request, transport=None):
        nonlocal called
        called = True
        return LLMChatResponse(
            provider_key=request.provider_key,
            model=request.model,
            content="should not be called",
            raw_response={},
            token_usage={},
            latency_ms=1,
        )

    monkeypatch.setattr("app.routers.llm.chat_completion", fake_chat_completion)

    response = client.post(
        "/api/llm/chat",
        json={
            "provider_id": "job_checked_provider",
            "job_id": "11111111-1111-4111-8111-111111111111",
            "messages": [{"role": "user", "content": "hello"}],
        },
    )

    assert response.status_code == 404
    assert called is False


def test_llm_chat_skips_job_validation_when_log_step_is_false(monkeypatch) -> None:
    client.post(
        "/api/llm/providers",
        json={
            "provider_id": "no_log_provider",
            "display_name": "No Log Provider",
            "provider_family": "openai_compatible",
            "api_key_env": None,
            "base_url": "http://localhost:11434/v1",
            "model_name": "local-model",
            "enabled": True,
            "local_provider": True,
        },
    )

    def fake_chat_completion(session, request, transport=None):
        return LLMChatResponse(
            provider_key=request.provider_key,
            model=request.model,
            content="chat ok",
            raw_response={},
            token_usage={"total_tokens": 1},
            latency_ms=5,
        )

    monkeypatch.setattr("app.routers.llm.chat_completion", fake_chat_completion)

    response = client.post(
        "/api/llm/chat",
        json={
            "provider_id": "no_log_provider",
            "job_id": "11111111-1111-4111-8111-111111111111",
            "log_step": False,
            "messages": [{"role": "user", "content": "hello"}],
        },
    )

    assert response.status_code == 200
    assert response.json()["content"] == "chat ok"
    assert response.json()["step_id"] is None


def test_llm_chat_provider_not_found_returns_404() -> None:
    response = client.post(
        "/api/llm/chat",
        json={
            "provider_id": "missing_provider",
            "model": "any-model",
            "messages": [{"role": "user", "content": "hello"}],
        },
    )

    assert response.status_code == 404
