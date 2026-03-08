from threading import Lock

from app.models.project import Project
from app.repositories.project_repository import ProjectRepository


class InMemoryProjectRepository(ProjectRepository):
    def __init__(self) -> None:
        self._projects: dict[str, Project] = {}
        self._lock = Lock()

    async def create(self, project: Project) -> Project:
        with self._lock:
            self._projects[project.id] = project
        return project

    async def list(self) -> list[Project]:
        with self._lock:
            projects = list(self._projects.values())
        return sorted(projects, key=lambda project: project.created_at, reverse=True)

    async def get_by_id(self, project_id: str) -> Project | None:
        with self._lock:
            return self._projects.get(project_id)
