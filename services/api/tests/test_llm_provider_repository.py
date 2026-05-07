from app.repositories.llm_providers import delete_provider, get_provider, list_providers, upsert_provider
from app.services.provider_registry import get_provider_config


def test_llm_provider_repository_upserts_by_provider_key(db_session) -> None:
    provider = upsert_provider(
        db_session,
        {
            "provider_key": "custom",
            "display_name": "Custom Provider",
            "provider_type": "openai_compatible",
            "base_url": "https://models.example.com/v1",
            "api_key_env": "CUSTOM_API_KEY",
            "enabled": True,
            "config": {"model_name": "user-configured"},
        },
    )

    assert get_provider(db_session, "custom").id == provider.id

    updated = upsert_provider(
        db_session,
        {
            "provider_key": "custom",
            "display_name": "Custom Provider Updated",
            "provider_type": "openai_compatible",
            "enabled": False,
        },
    )

    assert updated.id == provider.id
    assert updated.display_name == "Custom Provider Updated"
    assert updated.enabled is False
    assert [item.provider_key for item in list_providers(db_session)] == ["custom"]

    assert delete_provider(db_session, "custom") is True
    assert get_provider(db_session, "custom") is None
    assert delete_provider(db_session, "custom") is False


def test_db_only_provider_without_api_key_env_does_not_inherit_preset(db_session) -> None:
    upsert_provider(
        db_session,
        {
            "provider_key": "db_only_custom",
            "display_name": "DB Only Custom",
            "provider_type": "openai_compatible",
            "base_url": "https://models.example.com/v1",
            "api_key_env": None,
            "enabled": True,
            "config": {"model_name": "user-configured", "openai_compatible": True},
        },
    )

    provider = get_provider_config(db_session, "db_only_custom")

    assert provider is not None
    assert provider.api_key_env is None
    assert provider.api_key_configured is False
