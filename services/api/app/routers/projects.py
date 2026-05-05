from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter

from app.schemas.common import Project, ProjectCreate, ProjectListResponse
from app.services.mock_data import mock_projects

router = APIRouter()


@router.get("", response_model=ProjectListResponse)
def list_projects() -> ProjectListResponse:
    return ProjectListResponse(items=mock_projects())


@router.post("", response_model=Project, status_code=201)
def create_project(payload: ProjectCreate) -> Project:
    return Project(
        id=f"project_{uuid4().hex[:8]}",
        name=payload.name,
        description=payload.description,
        jurisdiction_focus=payload.jurisdiction_focus,
        industry_focus=payload.industry_focus,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        evidence=[],
    )
