from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.models.generated_file import GeneratedFileContent, GeneratedFileMetadata
from app.services.errors import EntityNotFoundError, InvalidRequestError
from app.services.generated_file_service import GeneratedFileService

router = APIRouter(prefix="/api", tags=["generated-files"])


def get_generated_file_service(request: Request) -> GeneratedFileService:
    return request.app.state.generated_file_service


@router.get("/runs/{run_id}/files", response_model=list[GeneratedFileMetadata])
async def list_generated_files(
    run_id: str,
    generated_file_service: Annotated[
        GeneratedFileService, Depends(get_generated_file_service)
    ],
) -> list[GeneratedFileMetadata]:
    try:
        return await generated_file_service.list_generated_files(run_id)
    except EntityNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/runs/{run_id}/files/content", response_model=GeneratedFileContent)
async def get_generated_file_content(
    run_id: str,
    path: Annotated[str, Query(min_length=1)],
    generated_file_service: Annotated[
        GeneratedFileService, Depends(get_generated_file_service)
    ],
) -> GeneratedFileContent:
    try:
        return await generated_file_service.get_generated_file_content(run_id, path)
    except EntityNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidRequestError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
