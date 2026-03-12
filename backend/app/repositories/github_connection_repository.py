from typing import Protocol

from app.models.github_connection import GitHubConnectionConfig


class GitHubConnectionRepository(Protocol):
    async def get(self) -> GitHubConnectionConfig | None: ...

    async def upsert(
        self, config: GitHubConnectionConfig
    ) -> GitHubConnectionConfig: ...
