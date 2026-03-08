from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.models.artifact import Artifact
from app.services.artifact_service import ArtifactService
from app.services.errors import EntityNotFoundError

router = APIRouter(prefix="/api", tags=["artifacts"])


def get_artifact_service(request: Request) -> ArtifactService:
    return request.app.state.artifact_service


@router.get("/runs/{run_id}/artifacts", response_model=list[Artifact])
async def list_run_artifacts(
    run_id: str,
    artifact_service: Annotated[ArtifactService, Depends(get_artifact_service)],
) -> list[Artifact]:
    try:
        return await artifact_service.list_run_artifacts(run_id)
    except EntityNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/artifacts/{artifact_id}", response_model=Artifact)
async def get_artifact(
    artifact_id: str,
    artifact_service: Annotated[ArtifactService, Depends(get_artifact_service)],
) -> Artifact:
    artifact = await artifact_service.get_artifact(artifact_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact
