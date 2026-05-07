from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.services.provider_registry import get_provider_config


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


@dataclass(frozen=True)
class LLMChatRequest:
    provider_key: str
    model: str
    messages: list[ChatMessage]
    temperature: float = 0.2
    max_tokens: int | None = None
    timeout_seconds: int = 60


@dataclass(frozen=True)
class LLMChatResponse:
    provider_key: str
    model: str
    content: str
    raw_response: dict[str, Any]
    token_usage: dict[str, Any]
    latency_ms: int


class LLMGatewayError(Exception):
    """Base class for LLM gateway failures safe to expose as summaries."""


class LLMProviderNotFoundError(LLMGatewayError):
    pass


class LLMProviderNotConfiguredError(LLMGatewayError):
    pass


class LLMMissingAPIKeyError(LLMGatewayError):
    pass


class LLMHTTPError(LLMGatewayError):
    pass


class LLMResponseParseError(LLMGatewayError):
    pass


def chat_completion(
    session: Session,
    request: LLMChatRequest,
    *,
    transport: httpx.BaseTransport | None = None,
) -> LLMChatResponse:
    provider = get_provider_config(session, request.provider_key)
    if provider is None:
        raise LLMProviderNotFoundError(f"Provider '{request.provider_key}' was not found.")
    if not provider.openai_compatible:
        raise LLMProviderNotConfiguredError("Provider is not marked as OpenAI-compatible.")
    if not provider.base_url:
        raise LLMProviderNotConfiguredError("Provider base_url is not configured.")

    api_key = _resolve_api_key(provider.api_key_env, provider.local_provider)
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload: dict[str, Any] = {
        "model": request.model,
        "messages": [{"role": message.role, "content": message.content} for message in request.messages],
        "temperature": request.temperature,
    }
    if request.max_tokens is not None:
        payload["max_tokens"] = request.max_tokens

    url = f"{provider.base_url.rstrip('/')}/chat/completions"
    started = time.perf_counter()
    try:
        with httpx.Client(timeout=request.timeout_seconds, transport=transport) as client:
            response = client.post(url, headers=headers, json=payload)
    except httpx.HTTPError as exc:
        raise LLMHTTPError(f"LLM provider request failed: {exc.__class__.__name__}") from exc
    latency_ms = max(0, int((time.perf_counter() - started) * 1000))

    if response.status_code >= 400:
        raise LLMHTTPError(_upstream_error_message(response))

    try:
        response_data = response.json()
    except ValueError as exc:
        raise LLMResponseParseError("LLM provider returned non-JSON response.") from exc

    content = _extract_content(response_data)
    token_usage = response_data.get("usage") or {}
    if not isinstance(token_usage, dict):
        token_usage = {}

    return LLMChatResponse(
        provider_key=request.provider_key,
        model=request.model,
        content=content,
        raw_response=response_data,
        token_usage=token_usage,
        latency_ms=latency_ms,
    )


def _resolve_api_key(api_key_env: str | None, local_provider: bool) -> str | None:
    if local_provider:
        return os.environ.get(api_key_env) if api_key_env else None
    if not api_key_env:
        raise LLMMissingAPIKeyError("Provider api_key_env is not configured.")
    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise LLMMissingAPIKeyError(f"API key environment variable '{api_key_env}' is not set.")
    return api_key


def _extract_content(response_data: dict[str, Any]) -> str:
    try:
        choices = response_data["choices"]
        first_choice = choices[0]
        message = first_choice["message"]
        content = message["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMResponseParseError("LLM provider response did not include choices[0].message.content.") from exc
    if not isinstance(content, str):
        raise LLMResponseParseError("LLM provider message content was not a string.")
    return content


def _upstream_error_message(response: httpx.Response) -> str:
    detail: str | dict[str, Any] = response.text[:500]
    try:
        data = response.json()
        if isinstance(data, dict):
            detail = data.get("error", data.get("message", detail))
    except ValueError:
        pass
    return f"LLM provider returned HTTP {response.status_code}: {detail}"
