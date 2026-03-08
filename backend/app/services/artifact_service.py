from app.models.artifact import Artifact
from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.workflow_run_repository import WorkflowRunRepository
from app.services.errors import EntityNotFoundError


class ArtifactService:
    def __init__(
        self,
        artifact_repository: ArtifactRepository,
        run_repository: WorkflowRunRepository,
    ) -> None:
        self._artifact_repository = artifact_repository
        self._run_repository = run_repository

    async def list_run_artifacts(self, run_id: str) -> list[Artifact]:
        run = await self._run_repository.get_by_id(run_id)
        if run is None:
            raise EntityNotFoundError(f"Run '{run_id}' not found")

        return await self._artifact_repository.list_by_run_id(run_id)

    async def get_artifact(self, artifact_id: str) -> Artifact | None:
        return await self._artifact_repository.get_by_id(artifact_id)
