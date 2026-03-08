from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.models.workflow_run import WorkflowRun
from app.services.errors import EntityNotFoundError
from app.services.workflow_run_service import WorkflowRunService

router = APIRouter(prefix="/api", tags=["workflow-runs"])


def get_workflow_run_service(request: Request) -> WorkflowRunService:
    return request.app.state.workflow_run_service


@router.post("/projects/{project_id}/runs", response_model=WorkflowRun, status_code=status.HTTP_201_CREATED)
async def start_run(
    project_id: str,
    run_service: Annotated[WorkflowRunService, Depends(get_workflow_run_service)],
) -> WorkflowRun:
    try:
        return await run_service.start_run(project_id)
    except EntityNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/runs/{run_id}", response_model=WorkflowRun)
async def get_run(
    run_id: str,
    run_service: Annotated[WorkflowRunService, Depends(get_workflow_run_service)],
) -> WorkflowRun:
    run = await run_service.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/projects/{project_id}/runs", response_model=list[WorkflowRun])
async def list_project_runs(
    project_id: str,
    run_service: Annotated[WorkflowRunService, Depends(get_workflow_run_service)],
) -> list[WorkflowRun]:
    try:
        return await run_service.list_project_runs(project_id)
    except EntityNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.delete("/runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_run(
    run_id: str,
    run_service: Annotated[WorkflowRunService, Depends(get_workflow_run_service)],
) -> None:
    try:
        await run_service.delete_run(run_id)
    except EntityNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
