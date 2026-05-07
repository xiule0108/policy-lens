from app.repositories.model_profiles import (
    create_model_profile,
    get_model_profile,
    list_model_profiles,
    set_default_model_profile,
    upsert_model_profile,
)


def test_model_profile_repository_create_upsert_list_and_default(db_session) -> None:
    profile = create_model_profile(
        db_session,
        {
            "name": "china_balanced",
            "description": "Balanced China provider profile",
            "profile_config": {"provider_key": "deepseek", "model": "user-configured"},
            "is_default": True,
        },
    )

    assert get_model_profile(db_session, "china_balanced").id == profile.id

    updated = upsert_model_profile(
        db_session,
        {
            "name": "china_balanced",
            "description": "Updated profile",
            "profile_config": {"provider_key": "kimi", "model": "user-configured"},
            "is_default": False,
        },
    )

    assert updated.id == profile.id
    assert updated.description == "Updated profile"
    assert updated.profile_config["provider_key"] == "kimi"
    assert [item.name for item in list_model_profiles(db_session)] == ["china_balanced"]

    create_model_profile(
        db_session,
        {
            "name": "global_fast",
            "profile_config": {"provider_key": "openai_compatible_custom"},
            "is_default": False,
        },
    )

    default_profile = set_default_model_profile(db_session, "global_fast")

    assert default_profile is not None
    assert default_profile.is_default is True
    assert get_model_profile(db_session, "china_balanced").is_default is False
