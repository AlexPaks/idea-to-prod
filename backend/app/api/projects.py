from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.models.project import Project, ProjectCreate
from app.services.project_service import ProjectService

router = APIRouter(prefix="/api/projects", tags=["projects"])


def get_project_service(request: Request) -> ProjectService:
    return request.app.state.project_service


@router.post("", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> Project:
    return await project_service.create_project(payload)


@router.get("", response_model=list[Project])
async def list_projects(
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> list[Project]:
    return await project_service.list_projects()


@router.get("/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> Project:
    project = await project_service.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
