from datetime import datetime

from app.models.generated_file import GeneratedFileContent, GeneratedFileMetadata
from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.workflow_run_repository import WorkflowRunRepository
from app.services.errors import EntityNotFoundError, InvalidRequestError
from app.services.run_workspace_service import RunWorkspaceService


class GeneratedFileService:
    def __init__(
        self,
        artifact_repository: ArtifactRepository,
        run_repository: WorkflowRunRepository,
        workspace_service: RunWorkspaceService,
    ) -> None:
        self._artifact_repository = artifact_repository
        self._run_repository = run_repository
        self._workspace_service = workspace_service

    async def list_generated_files(self, run_id: str) -> list[GeneratedFileMetadata]:
        run = await self._run_repository.get_by_id(run_id)
        if run is None:
            raise EntityNotFoundError(f"Run '{run_id}' not found")

        artifacts = await self._artifact_repository.list_by_run_id(run_id)
        generated: list[GeneratedFileMetadata] = []

        for artifact in artifacts:
            if artifact.artifact_type != "generated_file":
                continue

            path = str(artifact.metadata.get("path", artifact.title))
            size_bytes = int(artifact.metadata.get("size_bytes", 0))
            language = artifact.metadata.get("language")
            updated_at = artifact.created_at
            metadata_updated = artifact.metadata.get("updated_at")
            if metadata_updated and isinstance(metadata_updated, str):
                # let pydantic parse timestamp strings if present
                updated_at = GeneratedFileMetadata.model_validate(
                    {
                        "path": path,
                        "artifact_id": artifact.id,
                        "size_bytes": size_bytes,
                        "language": language,
                        "updated_at": metadata_updated,
                    }
                ).updated_at
            elif isinstance(metadata_updated, datetime):
                updated_at = metadata_updated

            generated.append(
                GeneratedFileMetadata(
                    path=path,
                    artifact_id=artifact.id,
                    size_bytes=size_bytes,
                    language=language if isinstance(language, str) else None,
                    updated_at=updated_at,
                )
            )

        generated.sort(key=lambda item: item.path)
        return generated

    async def get_generated_file_content(
        self,
        run_id: str,
        path: str,
    ) -> GeneratedFileContent:
        run = await self._run_repository.get_by_id(run_id)
        if run is None:
            raise EntityNotFoundError(f"Run '{run_id}' not found")

        generated_files = await self.list_generated_files(run_id)
        if not any(item.path == path for item in generated_files):
            raise EntityNotFoundError(f"Generated file '{path}' not found for run '{run_id}'")

        try:
            content = self._workspace_service.read_file(run_id, path)
        except InvalidRequestError:
            raise

        matched = next((item for item in generated_files if item.path == path), None)
        return GeneratedFileContent(
            path=path,
            content=content,
            language=matched.language if matched else None,
        )
