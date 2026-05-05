from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Project
from app.repositories._utils import coerce_uuid


def create_project(session: Session, data: dict) -> Project:
    project = Project(
        name=data["name"],
        description=data.get("description"),
        industry=data.get("industry"),
        jurisdictions=data.get("jurisdictions", []),
        default_model_profile=data.get("default_model_profile"),
        status=data.get("status", "active"),
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def get_project(session: Session, project_id: uuid.UUID | str) -> Project | None:
    return session.get(Project, coerce_uuid(project_id))


def list_projects(session: Session, limit: int = 50, offset: int = 0) -> list[Project]:
    statement = select(Project).order_by(Project.created_at.desc()).limit(limit).offset(offset)
    return list(session.scalars(statement))


def update_project(session: Session, project_id: uuid.UUID | str, data: dict) -> Project | None:
    project = get_project(session, project_id)
    if project is None:
        return None
    for key in (
        "name",
        "description",
        "industry",
        "jurisdictions",
        "default_model_profile",
        "status",
    ):
        if key in data:
            setattr(project, key, data[key])
    session.commit()
    session.refresh(project)
    return project


def delete_project(session: Session, project_id: uuid.UUID | str) -> bool:
    project = get_project(session, project_id)
    if project is None:
        return False
    session.delete(project)
    session.commit()
    return True
