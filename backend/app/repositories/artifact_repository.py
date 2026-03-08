from typing import Protocol

from app.models.artifact import Artifact


class ArtifactRepository(Protocol):
    async def create(self, artifact: Artifact) -> Artifact: ...

    async def get_by_id(self, artifact_id: str) -> Artifact | None: ...

    async def list_by_run_id(self, run_id: str) -> list[Artifact]: ...
