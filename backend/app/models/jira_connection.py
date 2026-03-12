from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class JiraConnectionPayload(BaseModel):
    enabled: bool = False
    server_url: str = ""
    tool_name: str = "jira"
    timeout_seconds: float = Field(default=30.0, gt=0)
    arguments_template_json: str = ""
    project_key: str = ""

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_fields(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data

        migrated = dict(data)
        if not migrated.get("server_url") and migrated.get("base_url"):
            migrated["server_url"] = migrated["base_url"]
        return migrated

    @model_validator(mode="after")
    def validate_enabled_configuration(self) -> "JiraConnectionPayload":
        if self.enabled and not self.server_url.strip():
            raise ValueError("server_url is required when Jira connection is enabled")
        if self.enabled and not self.tool_name.strip():
            raise ValueError("tool_name is required when Jira connection is enabled")
        return self


class JiraConnectionConfig(JiraConnectionPayload):
    updated_at: datetime | None = None


class JiraConnectionTestResult(BaseModel):
    ok: bool
    message: str
    tool_name: str | None = None
    argument_keys: list[str] = Field(default_factory=list)
    available_tools: list[str] = Field(default_factory=list)
