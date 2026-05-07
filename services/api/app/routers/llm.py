from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.repositories.analysis_jobs import get_analysis_job
from app.repositories.analysis_steps import create_analysis_step
from app.repositories.llm_providers import upsert_provider
from app.schemas.common import (
    LLMChatCompletionRequest,
    LLMChatCompletionResponse,
    LLMProvider,
    LLMProviderCreate,
    LLMProviderListResponse,
    LLMProviderTestRequest,
    LLMProviderTestResponse,
)
from app.services.llm_gateway import (
    ChatMessage,
    LLMChatRequest,
    LLMChatResponse,
    LLMHTTPError,
    LLMMissingAPIKeyError,
    LLMProviderNotConfiguredError,
    LLMProviderNotFoundError,
    LLMResponseParseError,
    chat_completion,
)
from app.services.provider_registry import get_provider_config, list_provider_configs

router = APIRouter()


@router.get("/providers", response_model=LLMProviderListResponse)
def list_providers(session: Session = Depends(get_session)) -> LLMProviderListResponse:
    return LLMProviderListResponse(items=list_provider_configs(session))


@router.post("/providers", response_model=LLMProvider, status_code=201)
def create_provider(payload: LLMProviderCreate, session: Session = Depends(get_session)) -> LLMProvider:
    provider_key = payload.provider_id or f"provider_{uuid4().hex[:8]}"
    config = {
        "aliases": payload.aliases,
        "model_name": payload.model_name,
    }
    if "openai_compatible" in payload.model_fields_set:
        config["openai_compatible"] = payload.openai_compatible
    if "local_provider" in payload.model_fields_set:
        config["local_provider"] = payload.local_provider
    upsert_provider(
        session,
        {
            "provider_key": provider_key,
            "display_name": payload.display_name,
            "provider_type": payload.provider_family,
            "base_url": payload.base_url,
            "api_key_env": payload.api_key_env,
            "enabled": payload.enabled,
            "config": config,
        },
    )
    provider = get_provider_config(session, provider_key)
    if provider is None:
        raise HTTPException(status_code=500, detail="Provider could not be loaded after save.")
    return provider


@router.post("/providers/{provider_id}/test", response_model=LLMProviderTestResponse)
def test_provider(
    provider_id: str,
    payload: LLMProviderTestRequest | None = None,
    session: Session = Depends(get_session),
) -> LLMProviderTestResponse:
    payload = payload or LLMProviderTestRequest()
    provider = get_provider_config(session, provider_id)
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider not found.")
    model = payload.model or provider.model_name
    if not model:
        raise HTTPException(status_code=422, detail="Provider test requires a model name.")

    request = LLMChatRequest(
        provider_key=provider_id,
        model=model,
        messages=[ChatMessage(role="user", content=payload.prompt)],
        temperature=0.2,
        max_tokens=128,
        timeout_seconds=payload.timeout_seconds,
    )
    try:
        response = chat_completion(session, request)
    except (LLMProviderNotConfiguredError, LLMMissingAPIKeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LLMProviderNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (LLMHTTPError, LLMResponseParseError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return LLMProviderTestResponse(
        provider_id=provider_id,
        status="passed",
        latency_ms=response.latency_ms,
        message=response.content,
        model=response.model,
        token_usage=response.token_usage,
        evidence=[
            {
                "id": f"provider_test_{provider_id}",
                "source_type": "llm_gateway",
                "summary": "Provider responded through an OpenAI-compatible chat completion call.",
                "confidence": 1.0,
            }
        ],
    )


@router.post("/chat", response_model=LLMChatCompletionResponse)
def create_chat_completion(
    payload: LLMChatCompletionRequest,
    session: Session = Depends(get_session),
) -> LLMChatCompletionResponse:
    provider = get_provider_config(session, payload.provider_id)
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider not found.")
    model = payload.model or provider.model_name
    if not model:
        raise HTTPException(status_code=422, detail="Chat completion requires a model name.")
    if payload.log_step and payload.job_id and get_analysis_job(session, payload.job_id) is None:
        raise HTTPException(status_code=404, detail="Analysis job not found.")

    request = LLMChatRequest(
        provider_key=payload.provider_id,
        model=model,
        messages=[ChatMessage(role=message.role, content=message.content) for message in payload.messages],
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
        timeout_seconds=payload.timeout_seconds,
    )
    try:
        response = chat_completion(session, request)
    except (LLMProviderNotConfiguredError, LLMMissingAPIKeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LLMProviderNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (LLMHTTPError, LLMResponseParseError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    step_id = _log_analysis_step(session, payload, response) if payload.log_step and payload.job_id else None
    return LLMChatCompletionResponse(
        provider_id=payload.provider_id,
        model=response.model,
        content=response.content,
        token_usage=response.token_usage,
        latency_ms=response.latency_ms,
        step_id=step_id,
    )


def _log_analysis_step(
    session: Session,
    payload: LLMChatCompletionRequest,
    response: LLMChatResponse,
) -> str:
    step_id = f"llm_chat_{uuid4().hex[:12]}"
    step = create_analysis_step(
        session,
        {
            "job_id": payload.job_id,
            "step_id": step_id,
            "tool_name": "llm_gateway.chat",
            "status": "completed",
            "model_provider": payload.provider_id,
            "model_name": response.model,
            "input_ref": {
                "message_count": len(payload.messages),
                "temperature": payload.temperature,
                "max_tokens": payload.max_tokens,
            },
            "output_ref": {
                "content_preview": response.content[:200],
            },
            "token_usage": response.token_usage,
            "latency_ms": response.latency_ms,
        },
    )
    return step.step_id
