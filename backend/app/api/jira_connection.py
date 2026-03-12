from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.models.jira_connection import (
    JiraConnectionConfig,
    JiraConnectionPayload,
    JiraConnectionTestResult,
)
from app.services.jira_connection_service import JiraConnectionService

router = APIRouter(prefix="/api/settings/jira", tags=["jira-settings"])


def get_jira_connection_service(request: Request) -> JiraConnectionService:
    return request.app.state.jira_connection_service


@router.get("", response_model=JiraConnectionConfig)
async def get_jira_connection(
    service: Annotated[JiraConnectionService, Depends(get_jira_connection_service)],
) -> JiraConnectionConfig:
    return await service.get_connection()


@router.put("", response_model=JiraConnectionConfig)
async def save_jira_connection(
    payload: JiraConnectionPayload,
    service: Annotated[JiraConnectionService, Depends(get_jira_connection_service)],
) -> JiraConnectionConfig:
    try:
        return await service.save_connection(payload)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.post("/test", response_model=JiraConnectionTestResult)
async def test_jira_connection(
    payload: JiraConnectionPayload,
    service: Annotated[JiraConnectionService, Depends(get_jira_connection_service)],
) -> JiraConnectionTestResult:
    try:
        return await service.test_connection(payload)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
