from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class GoogleDriveConnectionPayload(BaseModel):
    enabled: bool = False
    server_url: str = ""
    tool_name: str = "create_document"
    read_tool_name: str = "get_document"
    folder_id: str = ""
    timeout_seconds: float = Field(default=30.0, gt=0)
    arguments_template_json: str = ""
    read_arguments_template_json: str = ""

    @model_validator(mode="after")
    def validate_enabled_configuration(self) -> "GoogleDriveConnectionPayload":
        if self.enabled and not self.server_url.strip():
            raise ValueError("server_url is required when Google Drive connection is enabled")
        if self.enabled and not self.tool_name.strip():
            raise ValueError("tool_name is required when Google Drive connection is enabled")
        if self.enabled and not self.read_tool_name.strip():
            raise ValueError(
                "read_tool_name is required when Google Drive connection is enabled"
            )
        return self


class GoogleDriveConnectionConfig(GoogleDriveConnectionPayload):
    updated_at: datetime | None = None


class GoogleDriveConnectionTestResult(BaseModel):
    ok: bool
    message: str
    create_tool_name: str | None = None
    create_argument_keys: list[str] = Field(default_factory=list)
    read_tool_name: str | None = None
    read_argument_keys: list[str] = Field(default_factory=list)
