from asyncio import to_thread
from datetime import datetime, timezone

from app.models.github_connection import (
    GitHubConnectionConfig,
    GitHubConnectionPayload,
    GitHubConnectionTestResult,
)
from app.repositories.github_connection_repository import GitHubConnectionRepository
from app.services.integrations.github_mcp_client import GitHubMcpClient, GitHubMcpError


class GitHubConnectionService:
    def __init__(
        self,
        repository: GitHubConnectionRepository,
        default_payload: GitHubConnectionPayload,
    ) -> None:
        self._repository = repository
        self._default_payload = default_payload

    async def get_connection(self) -> GitHubConnectionConfig:
        saved = await self._repository.get()
        if saved is not None:
            return saved
        return GitHubConnectionConfig(**self._default_payload.model_dump(), updated_at=None)

    async def save_connection(self, payload: GitHubConnectionPayload) -> GitHubConnectionConfig:
        if payload.enabled:
            self._build_client(payload)

        config = GitHubConnectionConfig(
            **payload.model_dump(),
            updated_at=datetime.now(timezone.utc),
        )
        return await self._repository.upsert(config)

    async def test_connection(
        self, payload: GitHubConnectionPayload
    ) -> GitHubConnectionTestResult:
        if not payload.enabled:
            return GitHubConnectionTestResult(
                ok=True,
                message="Connection is disabled. Enable it to run connectivity checks.",
            )

        try:
            client = self._build_client(payload)
            probe = await to_thread(
                client.probe_connection,
                payload.owner,
                payload.repository,
            )
        except GitHubMcpError as error:
            return GitHubConnectionTestResult(
                ok=False,
                message=str(error),
            )

        return GitHubConnectionTestResult(
            ok=True,
            message="Connected to GitHub MCP server successfully.",
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

    def _build_client(
        self, payload: GitHubConnectionPayload | GitHubConnectionConfig
    ) -> GitHubMcpClient:
        return GitHubMcpClient(
            server_url=payload.server_url,
            tool_name=payload.tool_name,
            timeout_seconds=payload.timeout_seconds,
            arguments_template_json=payload.arguments_template_json,
        )
