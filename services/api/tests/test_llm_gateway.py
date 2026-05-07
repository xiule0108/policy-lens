import httpx
import pytest

from app.repositories.llm_providers import upsert_provider
from app.services.llm_gateway import (
    ChatMessage,
    LLMChatRequest,
    LLMHTTPError,
    LLMMissingAPIKeyError,
    LLMResponseParseError,
    chat_completion,
)


def upsert_test_provider(db_session, **overrides):
    data = {
        "provider_key": "custom",
        "display_name": "Custom Provider",
        "provider_type": "openai_compatible",
        "base_url": "https://models.example.com/v1/",
        "api_key_env": "CUSTOM_LLM_API_KEY",
        "enabled": True,
        "config": {
            "aliases": ["custom"],
            "model_name": "user-model",
            "openai_compatible": True,
            "local_provider": False,
        },
    }
    data.update(overrides)
    return upsert_provider(db_session, data)


def make_chat_request(provider_key: str = "custom", max_tokens: int | None = None) -> LLMChatRequest:
    return LLMChatRequest(
        provider_key=provider_key,
        model="user-model",
        messages=[ChatMessage(role="user", content="hello")],
        temperature=0.3,
        max_tokens=max_tokens,
        timeout_seconds=10,
    )


def test_openai_compatible_chat_success_sends_expected_request(db_session, monkeypatch) -> None:
    upsert_test_provider(db_session)
    monkeypatch.setenv("CUSTOM_LLM_API_KEY", "secret-value")
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["authorization"] = request.headers.get("authorization")
        seen["payload"] = request.read().decode("utf-8")
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "gateway ok"}}],
                "usage": {"prompt_tokens": 2, "completion_tokens": 3, "total_tokens": 5},
            },
        )

    response = chat_completion(db_session, make_chat_request(), transport=httpx.MockTransport(handler))

    assert response.content == "gateway ok"
    assert response.token_usage["total_tokens"] == 5
    assert seen["url"] == "https://models.example.com/v1/chat/completions"
    assert seen["authorization"] == "Bearer secret-value"
    assert '"max_tokens"' not in str(seen["payload"])


def test_openai_compatible_chat_includes_max_tokens_when_set(db_session, monkeypatch) -> None:
    upsert_test_provider(db_session)
    monkeypatch.setenv("CUSTOM_LLM_API_KEY", "secret-value")

    def handler(request: httpx.Request) -> httpx.Response:
        assert '"max_tokens":1024' in request.read().decode("utf-8").replace(" ", "")
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}], "usage": {}})

    response = chat_completion(
        db_session,
        make_chat_request(max_tokens=1024),
        transport=httpx.MockTransport(handler),
    )

    assert response.content == "ok"


def test_local_provider_does_not_require_authorization_header(db_session) -> None:
    upsert_test_provider(
        db_session,
        provider_key="local",
        provider_type="local",
        api_key_env=None,
        config={"model_name": "local-model", "openai_compatible": True, "local_provider": True},
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("authorization") is None
        return httpx.Response(200, json={"choices": [{"message": {"content": "local ok"}}], "usage": {}})

    response = chat_completion(
        db_session,
        make_chat_request(provider_key="local"),
        transport=httpx.MockTransport(handler),
    )

    assert response.content == "local ok"


def test_missing_api_key_raises_clear_error(db_session, monkeypatch) -> None:
    upsert_test_provider(db_session)
    monkeypatch.delenv("CUSTOM_LLM_API_KEY", raising=False)

    with pytest.raises(LLMMissingAPIKeyError):
        chat_completion(db_session, make_chat_request(), transport=httpx.MockTransport(lambda request: None))


def test_http_error_raises_gateway_error(db_session, monkeypatch) -> None:
    upsert_test_provider(db_session)
    monkeypatch.setenv("CUSTOM_LLM_API_KEY", "secret-value")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "upstream failed"})

    with pytest.raises(LLMHTTPError):
        chat_completion(db_session, make_chat_request(), transport=httpx.MockTransport(handler))


def test_non_openai_response_raises_parse_error(db_session, monkeypatch) -> None:
    upsert_test_provider(db_session)
    monkeypatch.setenv("CUSTOM_LLM_API_KEY", "secret-value")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"message": "not openai compatible"})

    with pytest.raises(LLMResponseParseError):
        chat_completion(db_session, make_chat_request(), transport=httpx.MockTransport(handler))
