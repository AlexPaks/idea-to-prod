from asyncio import to_thread
from datetime import datetime, timezone

from app.models.jira_connection import (
    JiraConnectionConfig,
    JiraConnectionPayload,
    JiraConnectionTestResult,
)
from app.repositories.jira_connection_repository import JiraConnectionRepository
from app.services.integrations.jira_mcp_client import JiraMcpClient, JiraMcpError


class JiraConnectionService:
    def __init__(
        self,
        repository: JiraConnectionRepository,
        default_payload: JiraConnectionPayload,
    ) -> None:
        self._repository = repository
        self._default_payload = default_payload

    async def get_connection(self) -> JiraConnectionConfig:
        saved = await self._repository.get()
        if saved is not None:
            return saved
        return JiraConnectionConfig(**self._default_payload.model_dump(), updated_at=None)

    async def save_connection(self, payload: JiraConnectionPayload) -> JiraConnectionConfig:
        if payload.enabled:
            self._build_client(payload)

        config = JiraConnectionConfig(
            **payload.model_dump(),
            updated_at=datetime.now(timezone.utc),
        )
        return await self._repository.upsert(config)

    async def test_connection(self, payload: JiraConnectionPayload) -> JiraConnectionTestResult:
        if not payload.enabled:
            return JiraConnectionTestResult(
                ok=True,
                message="Connection is disabled. Enable it to run connectivity checks.",
            )

        try:
            client = self._build_client(payload)
            probe = await to_thread(client.probe_connection, payload.project_key)
        except JiraMcpError as error:
            return JiraConnectionTestResult(
                ok=False,
                message=str(error),
            )

        return JiraConnectionTestResult(
            ok=True,
            message="Connected to Jira MCP server successfully.",
            tool_name=str(probe.get("tool_name") or payload.tool_name),
            argument_keys=[
                str(item)
                for item in probe.get("argument_keys", [])
                if isinstance(item, str)
            ],
            available_tools=[
                str(item)
                for item in probe.get("available_tools", [])
                if isinstance(item, str)
            ],
        )

    def _build_client(self, payload: JiraConnectionPayload | JiraConnectionConfig) -> JiraMcpClient:
        return JiraMcpClient(
            server_url=payload.server_url,
            tool_name=payload.tool_name,
            timeout_seconds=payload.timeout_seconds,
            arguments_template_json=payload.arguments_template_json,
        )
