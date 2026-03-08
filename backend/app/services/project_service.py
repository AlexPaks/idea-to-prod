from datetime import datetime, timezone
from uuid import uuid4

from app.models.project import Project, ProjectCreate
from app.repositories.project_repository import ProjectRepository


class ProjectService:
    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

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

    def _generate_project_name(self, idea: str) -> str:
        words = idea.split()
        if not words:
            return "Untitled Project"

        preview = " ".join(words[:6]).capitalize()
        if len(words) > 6:
            preview = f"{preview}..."
        return preview
