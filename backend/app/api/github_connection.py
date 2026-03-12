from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.models.github_connection import (
    GitHubConnectionConfig,
    GitHubConnectionPayload,
    GitHubConnectionTestResult,
)
from app.services.github_connection_service import GitHubConnectionService

router = APIRouter(prefix="/api/settings/github", tags=["github-settings"])


def get_github_connection_service(request: Request) -> GitHubConnectionService:
    return request.app.state.github_connection_service


@router.get("", response_model=GitHubConnectionConfig)
async def get_github_connection(
    service: Annotated[
        GitHubConnectionService, Depends(get_github_connection_service)
    ],
) -> GitHubConnectionConfig:
    return await service.get_connection()


@router.put("", response_model=GitHubConnectionConfig)
async def save_github_connection(
    payload: GitHubConnectionPayload,
    service: Annotated[
        GitHubConnectionService, Depends(get_github_connection_service)
    ],
) -> GitHubConnectionConfig:
    try:
        return await service.save_connection(payload)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.post("/test", response_model=GitHubConnectionTestResult)
async def test_github_connection(
    payload: GitHubConnectionPayload,
    service: Annotated[
        GitHubConnectionService, Depends(get_github_connection_service)
    ],
) -> GitHubConnectionTestResult:
    try:
        return await service.test_connection(payload)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
