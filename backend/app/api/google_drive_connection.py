from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.models.google_drive_connection import (
    GoogleDriveConnectionConfig,
    GoogleDriveConnectionPayload,
    GoogleDriveConnectionTestResult,
)
from app.services.google_drive_connection_service import GoogleDriveConnectionService
from app.services.integrations.google_drive_mcp_client import GoogleDriveMcpError

router = APIRouter(prefix="/api/settings/google-drive", tags=["google-drive-settings"])


def get_google_drive_connection_service(request: Request) -> GoogleDriveConnectionService:
    return request.app.state.google_drive_connection_service


@router.get("", response_model=GoogleDriveConnectionConfig)
async def get_google_drive_connection(
    service: Annotated[
        GoogleDriveConnectionService, Depends(get_google_drive_connection_service)
    ],
) -> GoogleDriveConnectionConfig:
    return await service.get_connection()


@router.put("", response_model=GoogleDriveConnectionConfig)
async def save_google_drive_connection(
    payload: GoogleDriveConnectionPayload,
    service: Annotated[
        GoogleDriveConnectionService, Depends(get_google_drive_connection_service)
    ],
) -> GoogleDriveConnectionConfig:
    try:
        return await service.save_connection(payload)
    except (ValueError, GoogleDriveMcpError) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.post("/test", response_model=GoogleDriveConnectionTestResult)
async def test_google_drive_connection(
    payload: GoogleDriveConnectionPayload,
    service: Annotated[
        GoogleDriveConnectionService, Depends(get_google_drive_connection_service)
    ],
) -> GoogleDriveConnectionTestResult:
    try:
        return await service.test_connection(payload)
    except (ValueError, GoogleDriveMcpError) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
