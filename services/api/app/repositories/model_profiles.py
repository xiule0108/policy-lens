from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ModelProfile


def create_model_profile(session: Session, data: dict) -> ModelProfile:
    profile = ModelProfile(
        name=data["name"],
        description=data.get("description"),
        profile_config=data.get("profile_config", {}),
        is_default=data.get("is_default", False),
    )
    if profile.is_default:
        _clear_default_profiles(session)
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


def upsert_model_profile(session: Session, data: dict) -> ModelProfile:
    profile = get_model_profile(session, data["name"])
    if profile is None:
        return create_model_profile(session, data)
    for key in ("description", "profile_config", "is_default"):
        if key in data:
            setattr(profile, key, data[key])
    if profile.is_default:
        _clear_default_profiles(session, exclude_name=profile.name)
    session.commit()
    session.refresh(profile)
    return profile


def get_model_profile(session: Session, name: str) -> ModelProfile | None:
    statement = select(ModelProfile).where(ModelProfile.name == name)
    return session.scalar(statement)


def list_model_profiles(session: Session) -> list[ModelProfile]:
    statement = select(ModelProfile).order_by(ModelProfile.name.asc())
    return list(session.scalars(statement))


def set_default_model_profile(session: Session, name: str) -> ModelProfile | None:
    profile = get_model_profile(session, name)
    if profile is None:
        return None
    _clear_default_profiles(session, exclude_name=name)
    profile.is_default = True
    session.commit()
    session.refresh(profile)
    return profile


def _clear_default_profiles(session: Session, exclude_name: str | None = None) -> None:
    statement = select(ModelProfile)
    if exclude_name is not None:
        statement = statement.where(ModelProfile.name != exclude_name)
    for profile in session.scalars(statement):
        profile.is_default = False
