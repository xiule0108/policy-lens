from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import LLMProvider


def upsert_provider(session: Session, data: dict) -> LLMProvider:
    provider = get_provider(session, data["provider_key"])
    if provider is None:
        provider = LLMProvider(
            provider_key=data["provider_key"],
            display_name=data["display_name"],
            provider_type=data["provider_type"],
            base_url=data.get("base_url"),
            api_key_env=data.get("api_key_env"),
            enabled=data.get("enabled", False),
            config=data.get("config", {}),
        )
        session.add(provider)
    else:
        for key in ("display_name", "provider_type", "base_url", "api_key_env", "enabled", "config"):
            if key in data:
                setattr(provider, key, data[key])
    session.commit()
    session.refresh(provider)
    return provider


def get_provider(session: Session, provider_key: str) -> LLMProvider | None:
    statement = select(LLMProvider).where(LLMProvider.provider_key == provider_key)
    return session.scalar(statement)


def list_providers(session: Session) -> list[LLMProvider]:
    statement = select(LLMProvider).order_by(LLMProvider.provider_key.asc())
    return list(session.scalars(statement))


def delete_provider(session: Session, provider_key: str) -> bool:
    provider = get_provider(session, provider_key)
    if provider is None:
        return False
    session.delete(provider)
    session.commit()
    return True
