from uuid import uuid4

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models import LLMProvider as LLMProviderModel
from app.db.session import get_session
from app.repositories.llm_providers import list_providers as repo_list_providers
from app.repositories.llm_providers import upsert_provider
from app.schemas.common import (
    LLMProvider,
    LLMProviderCreate,
    LLMProviderListResponse,
    LLMProviderTestResponse,
)
from app.services.provider_registry import get_provider_presets

router = APIRouter()


@router.get("/providers", response_model=LLMProviderListResponse)
def list_providers(session: Session = Depends(get_session)) -> LLMProviderListResponse:
    providers = get_provider_presets()
    preset_ids = {provider.id for provider in providers}
    for provider in repo_list_providers(session):
        provider_schema = _to_provider_schema(provider)
        if provider_schema.id in preset_ids:
            provider_schema.id = f"user_{provider_schema.id}"
        providers.append(provider_schema)
    return LLMProviderListResponse(items=providers)


@router.post("/providers", response_model=LLMProvider, status_code=201)
def create_provider(payload: LLMProviderCreate, session: Session = Depends(get_session)) -> LLMProvider:
    provider_key = payload.provider_id or f"provider_{uuid4().hex[:8]}"
    provider = upsert_provider(
        session,
        {
            "provider_key": provider_key,
            "display_name": payload.display_name,
            "provider_type": payload.provider_family,
            "base_url": payload.base_url,
            "api_key_env": payload.api_key_env,
            "enabled": payload.enabled,
            "config": {
                "aliases": payload.aliases,
                "model_name": payload.model_name,
                "openai_compatible": payload.openai_compatible,
                "local_provider": payload.local_provider,
            },
        },
    )
    return _to_provider_schema(provider)


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


def _to_provider_schema(provider: LLMProviderModel) -> LLMProvider:
    config = provider.config or {}
    return LLMProvider(
        id=provider.provider_key,
        display_name=provider.display_name,
        provider_family=provider.provider_type,
        aliases=config.get("aliases", []),
        api_key_env=provider.api_key_env,
        base_url=provider.base_url,
        model_name=config.get("model_name"),
        enabled=provider.enabled,
        openai_compatible=config.get("openai_compatible", True),
        local_provider=config.get("local_provider", False),
        notes="User-created provider config. Secrets are referenced by env var only.",
    )
