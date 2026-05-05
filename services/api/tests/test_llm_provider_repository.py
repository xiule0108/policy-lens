from app.repositories.llm_providers import get_provider, list_providers, upsert_provider


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
