from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models import Project as ProjectModel
from app.db.session import get_session
from app.repositories.projects import create_project as repo_create_project
from app.repositories.projects import list_projects as repo_list_projects
from app.schemas.common import Project, ProjectCreate, ProjectListResponse

router = APIRouter()


@router.get("", response_model=ProjectListResponse)
def list_projects(session: Session = Depends(get_session)) -> ProjectListResponse:
    return ProjectListResponse(items=[_to_project_schema(project) for project in repo_list_projects(session)])


@router.post("", response_model=Project, status_code=201)
def create_project(payload: ProjectCreate, session: Session = Depends(get_session)) -> Project:
    project = repo_create_project(
        session,
        {
            "name": payload.name,
            "description": payload.description,
            "industry": payload.industry or (payload.industry_focus[0] if payload.industry_focus else None),
            "jurisdictions": payload.jurisdictions or payload.jurisdiction_focus,
            "default_model_profile": payload.default_model_profile,
        },
    )
    return _to_project_schema(project)


def _to_project_schema(project: ProjectModel) -> Project:
    industry_focus = [project.industry] if project.industry else []
    return Project(
        id=str(project.id),
        name=project.name,
        description=project.description,
        industry=project.industry,
        jurisdictions=project.jurisdictions,
        default_model_profile=project.default_model_profile,
        jurisdiction_focus=project.jurisdictions,
        industry_focus=industry_focus,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
        evidence=[],
    )
