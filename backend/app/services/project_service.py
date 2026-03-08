from datetime import datetime, timezone
from uuid import uuid4

from app.models.project import Project, ProjectCreate
from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.workflow_run_repository import WorkflowRunRepository
from app.services.errors import EntityNotFoundError


class ProjectService:
    def __init__(
        self,
        repository: ProjectRepository,
        run_repository: WorkflowRunRepository,
        artifact_repository: ArtifactRepository,
    ) -> None:
        self._repository = repository
        self._run_repository = run_repository
        self._artifact_repository = artifact_repository

    async def create_project(self, payload: ProjectCreate) -> Project:
        project = Project(
            id=str(uuid4()),
            name=payload.name or self._generate_project_name(payload.idea),
            idea=payload.idea,
            status="draft",
            created_at=datetime.now(timezone.utc),
        )
        return await self._repository.create(project)

    async def list_projects(self) -> list[Project]:
        return await self._repository.list()

    async def get_project(self, project_id: str) -> Project | None:
        return await self._repository.get_by_id(project_id)

    async def delete_project(self, project_id: str) -> None:
        project = await self._repository.get_by_id(project_id)
        if project is None:
            raise EntityNotFoundError(f"Project '{project_id}' not found")

        runs = await self._run_repository.list_by_project_id(project_id)
        for run in runs:
            await self._artifact_repository.delete_by_run_id(run.id)
            await self._run_repository.delete(run.id)

        await self._repository.delete(project_id)

    def _generate_project_name(self, idea: str) -> str:
        words = idea.split()
        if not words:
            return "Untitled Project"

        preview = " ".join(words[:6]).capitalize()
        if len(words) > 6:
            preview = f"{preview}..."
        return preview
