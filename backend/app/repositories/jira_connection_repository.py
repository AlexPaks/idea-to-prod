from typing import Protocol

from app.models.jira_connection import JiraConnectionConfig


class JiraConnectionRepository(Protocol):
    async def get(self) -> JiraConnectionConfig | None: ...

    async def upsert(self, config: JiraConnectionConfig) -> JiraConnectionConfig: ...
