from uuid import uuid4

from fastapi import APIRouter

from app.schemas.common import (
    LLMProvider,
    LLMProviderCreate,
    LLMProviderListResponse,
    LLMProviderTestResponse,
)
from app.services.provider_registry import get_provider_presets

router = APIRouter()


@router.get("/providers", response_model=LLMProviderListResponse)
def list_providers() -> LLMProviderListResponse:
    return LLMProviderListResponse(items=get_provider_presets())


@router.post("/providers", response_model=LLMProvider, status_code=201)
def create_provider(payload: LLMProviderCreate) -> LLMProvider:
    return LLMProvider(
        id=payload.provider_id or f"provider_{uuid4().hex[:8]}",
        display_name=payload.display_name,
        provider_family=payload.provider_family,
        aliases=payload.aliases,
        api_key_env=payload.api_key_env,
        base_url=payload.base_url,
        model_name=payload.model_name,
        enabled=payload.enabled,
        openai_compatible=payload.openai_compatible,
        local_provider=payload.local_provider,
        notes="User-created provider config. Secrets are referenced by env var only.",
    )


@router.post("/providers/{provider_id}/test", response_model=LLMProviderTestResponse)
def test_provider(provider_id: str) -> LLMProviderTestResponse:
    return LLMProviderTestResponse(
        provider_id=provider_id,
        status="mock_passed",
        latency_ms=0,
        message="v0.1 only validates provider configuration shape. No external model call was made.",
        evidence=[
            {
                "id": f"provider_test_{provider_id}",
                "source_type": "llm_gateway_mock",
                "summary": "Provider test avoided real API calls and secrets.",
                "confidence": 1.0,
            }
        ],
    )
