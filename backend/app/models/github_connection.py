from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class GitHubConnectionPayload(BaseModel):
    enabled: bool = False
    server_url: str = ""
    tool_name: str = "github"
    timeout_seconds: float = Field(default=30.0, gt=0)
    arguments_template_json: str = ""
    owner: str = ""
    repository: str = ""

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_fields(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data

        migrated = dict(data)
        if not migrated.get("server_url") and migrated.get("api_base_url"):
            migrated["server_url"] = migrated["api_base_url"]
        return migrated

    @model_validator(mode="after")
    def validate_enabled_configuration(self) -> "GitHubConnectionPayload":
        if self.enabled and not self.server_url.strip():
            raise ValueError("server_url is required when GitHub connection is enabled")
        if self.enabled and not self.tool_name.strip():
            raise ValueError("tool_name is required when GitHub connection is enabled")
        return self


class GitHubConnectionConfig(GitHubConnectionPayload):
    updated_at: datetime | None = None


class GitHubConnectionTestResult(BaseModel):
    ok: bool
    message: str
    tool_name: str | None = None
    argument_keys: list[str] = Field(default_factory=list)
    available_tools: list[str] = Field(default_factory=list)
