from asyncio import to_thread
from datetime import datetime, timezone

from app.models.google_drive_connection import (
    GoogleDriveConnectionConfig,
    GoogleDriveConnectionPayload,
    GoogleDriveConnectionTestResult,
)
from app.repositories.google_drive_connection_repository import (
    GoogleDriveConnectionRepository,
)
from app.services.integrations.google_drive_mcp_client import (
    GoogleDriveMcpClient,
    GoogleDriveMcpError,
)
from app.services.workflow_stages.detailed_design_service import DetailedDesignService
from app.services.workflow_stages.high_level_design_service import HighLevelDesignService


class GoogleDriveConnectionService:
    def __init__(
        self,
        repository: GoogleDriveConnectionRepository,
        high_level_design_service: HighLevelDesignService,
        detailed_design_service: DetailedDesignService,
        default_payload: GoogleDriveConnectionPayload,
    ) -> None:
        self._repository = repository
        self._high_level_design_service = high_level_design_service
        self._detailed_design_service = detailed_design_service
        self._default_payload = default_payload

    async def initialize_runtime(self) -> GoogleDriveConnectionConfig:
        config = await self.get_connection()
        self._apply_runtime_configuration(config)
        return config

    async def get_connection(self) -> GoogleDriveConnectionConfig:
        saved = await self._repository.get()
        if saved is not None:
            return saved
        return GoogleDriveConnectionConfig(
            **self._default_payload.model_dump(),
            updated_at=None,
        )

    async def save_connection(
        self, payload: GoogleDriveConnectionPayload
    ) -> GoogleDriveConnectionConfig:
        if payload.enabled:
            # Validate payload shape against client requirements before persisting.
            self._build_client(payload)

        config = GoogleDriveConnectionConfig(
            **payload.model_dump(),
            updated_at=datetime.now(timezone.utc),
        )
        saved = await self._repository.upsert(config)
        self._apply_runtime_configuration(saved)
        return saved

    async def test_connection(
        self, payload: GoogleDriveConnectionPayload
    ) -> GoogleDriveConnectionTestResult:
        if not payload.enabled:
            return GoogleDriveConnectionTestResult(
                ok=True,
                message="Connection is disabled. Enable it to run connectivity checks.",
            )

        try:
            client = self._build_client(payload)
            probe = await to_thread(client.probe_connection)
        except GoogleDriveMcpError as error:
            return GoogleDriveConnectionTestResult(
                ok=False,
                message=str(error),
            )

        create_tool_name = str(probe.get("create_tool_name") or payload.tool_name)
        create_argument_keys = [
            str(item)
            for item in probe.get("create_argument_keys", [])
            if isinstance(item, str)
        ]
        read_tool_name = str(probe.get("read_tool_name") or payload.read_tool_name)
        read_argument_keys = [
            str(item)
            for item in probe.get("read_argument_keys", [])
            if isinstance(item, str)
        ]

        return GoogleDriveConnectionTestResult(
            ok=True,
            message="Connected to Google Drive MCP server successfully.",
            create_tool_name=create_tool_name,
            create_argument_keys=create_argument_keys,
            read_tool_name=read_tool_name,
            read_argument_keys=read_argument_keys,
        )

    def _apply_runtime_configuration(self, config: GoogleDriveConnectionConfig) -> None:
        if not config.enabled:
            self._high_level_design_service.configure_google_drive(
                google_drive_client=None,
                require_drive_save=False,
            )
            self._detailed_design_service.configure_google_drive(
                google_drive_client=None,
                require_google_drive_read=False,
            )
            return

        client = self._build_client(config)
        self._high_level_design_service.configure_google_drive(
            google_drive_client=client,
            require_drive_save=True,
        )
        self._detailed_design_service.configure_google_drive(
            google_drive_client=client,
            require_google_drive_read=True,
        )

    def _build_client(
        self, payload: GoogleDriveConnectionPayload | GoogleDriveConnectionConfig
    ) -> GoogleDriveMcpClient:
        return GoogleDriveMcpClient(
            server_url=payload.server_url,
            tool_name=payload.tool_name,
            read_tool_name=payload.read_tool_name,
            folder_id=payload.folder_id,
            timeout_seconds=payload.timeout_seconds,
            arguments_template_json=payload.arguments_template_json,
            read_arguments_template_json=payload.read_arguments_template_json,
        )
