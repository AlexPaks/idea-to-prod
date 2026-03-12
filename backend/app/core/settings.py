import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    frontend_origins: list[str]
    mongodb_uri: str
    mongodb_db_name: str
    projects_collection: str
    workflow_runs_collection: str
    artifacts_collection: str
    execution_events_collection: str
    google_drive_connections_collection: str
    github_connections_collection: str
    jira_connections_collection: str
    mock_workflow_step_delay_seconds: float
    test_runner_timeout_seconds: float
    generated_runs_root_dir: str
    llm_provider: str
    openai_api_key: str
    gemini_api_key: str
    google_drive_mcp_enabled: bool
    google_drive_mcp_url: str
    google_drive_mcp_tool_name: str
    google_drive_mcp_read_tool_name: str
    google_drive_mcp_folder_id: str
    google_drive_mcp_timeout_seconds: float
    google_drive_mcp_arguments_template_json: str
    google_drive_mcp_read_arguments_template_json: str
    github_mcp_enabled: bool
    github_mcp_url: str
    github_mcp_tool_name: str
    github_mcp_timeout_seconds: float
    github_mcp_arguments_template_json: str
    github_owner: str
    github_repository: str
    jira_mcp_enabled: bool
    jira_mcp_url: str
    jira_mcp_tool_name: str
    jira_mcp_timeout_seconds: float
    jira_mcp_arguments_template_json: str
    jira_project_key: str


def _load_backend_env_file() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists() or not env_path.is_file():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue

        if (
            (value.startswith('"') and value.endswith('"'))
            or (value.startswith("'") and value.endswith("'"))
        ) and len(value) >= 2:
            value = value[1:-1]

        os.environ.setdefault(key, value)


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _read_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default

    try:
        return float(raw)
    except ValueError:
        return default


def _read_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return default


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    _load_backend_env_file()
    frontend_origins = _split_csv(
        os.getenv("FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    )
    google_drive_mcp_url = os.getenv("GOOGLE_DRIVE_MCP_URL", "").strip()
    google_drive_mcp_enabled = _read_bool(
        "GOOGLE_DRIVE_MCP_ENABLED",
        bool(google_drive_mcp_url),
    )
    github_mcp_url = os.getenv("GITHUB_MCP_URL", "").strip()
    github_mcp_enabled = _read_bool(
        "GITHUB_MCP_ENABLED",
        bool(github_mcp_url),
    )
    jira_mcp_url = os.getenv("JIRA_MCP_URL", "").strip()
    jira_mcp_enabled = _read_bool(
        "JIRA_MCP_ENABLED",
        bool(jira_mcp_url),
    )

    return Settings(
        frontend_origins=frontend_origins,
        mongodb_uri=os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
        mongodb_db_name=os.getenv("MONGODB_DB_NAME", "ideatoprod"),
        projects_collection=os.getenv("MONGODB_COLLECTION_PROJECTS", "projects"),
        workflow_runs_collection=os.getenv(
            "MONGODB_COLLECTION_WORKFLOW_RUNS", "workflow_runs"
        ),
        artifacts_collection=os.getenv("MONGODB_COLLECTION_ARTIFACTS", "artifacts"),
        execution_events_collection=os.getenv(
            "MONGODB_COLLECTION_EXECUTION_EVENTS", "execution_events"
        ),
        google_drive_connections_collection=os.getenv(
            "MONGODB_COLLECTION_GOOGLE_DRIVE_CONNECTIONS",
            "google_drive_connections",
        ),
        github_connections_collection=os.getenv(
            "MONGODB_COLLECTION_GITHUB_CONNECTIONS",
            "github_connections",
        ),
        jira_connections_collection=os.getenv(
            "MONGODB_COLLECTION_JIRA_CONNECTIONS",
            "jira_connections",
        ),
        mock_workflow_step_delay_seconds=_read_float(
            "MOCK_WORKFLOW_STEP_DELAY_SECONDS", 2.5
        ),
        test_runner_timeout_seconds=_read_float("TEST_RUNNER_TIMEOUT_SECONDS", 60.0),
        generated_runs_root_dir=os.getenv("GENERATED_RUNS_ROOT_DIR", "generated_runs"),
        llm_provider=os.getenv("LLM_PROVIDER", "openai"),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        google_drive_mcp_enabled=google_drive_mcp_enabled,
        google_drive_mcp_url=google_drive_mcp_url,
        google_drive_mcp_tool_name=os.getenv(
            "GOOGLE_DRIVE_MCP_TOOL_NAME", "create_document"
        ),
        google_drive_mcp_read_tool_name=os.getenv(
            "GOOGLE_DRIVE_MCP_READ_TOOL_NAME", "get_document"
        ),
        google_drive_mcp_folder_id=os.getenv("GOOGLE_DRIVE_MCP_FOLDER_ID", ""),
        google_drive_mcp_timeout_seconds=_read_float(
            "GOOGLE_DRIVE_MCP_TIMEOUT_SECONDS", 30.0
        ),
        google_drive_mcp_arguments_template_json=os.getenv(
            "GOOGLE_DRIVE_MCP_ARGUMENTS_TEMPLATE_JSON", ""
        ),
        google_drive_mcp_read_arguments_template_json=os.getenv(
            "GOOGLE_DRIVE_MCP_READ_ARGUMENTS_TEMPLATE_JSON", ""
        ),
        github_mcp_enabled=github_mcp_enabled,
        github_mcp_url=github_mcp_url,
        github_mcp_tool_name=os.getenv("GITHUB_MCP_TOOL_NAME", "github"),
        github_mcp_timeout_seconds=_read_float("GITHUB_MCP_TIMEOUT_SECONDS", 30.0),
        github_mcp_arguments_template_json=os.getenv(
            "GITHUB_MCP_ARGUMENTS_TEMPLATE_JSON", ""
        ),
        github_owner=os.getenv("GITHUB_OWNER", ""),
        github_repository=os.getenv("GITHUB_REPOSITORY", ""),
        jira_mcp_enabled=jira_mcp_enabled,
        jira_mcp_url=jira_mcp_url,
        jira_mcp_tool_name=os.getenv("JIRA_MCP_TOOL_NAME", "jira"),
        jira_mcp_timeout_seconds=_read_float("JIRA_MCP_TIMEOUT_SECONDS", 30.0),
        jira_mcp_arguments_template_json=os.getenv(
            "JIRA_MCP_ARGUMENTS_TEMPLATE_JSON", ""
        ),
        jira_project_key=os.getenv("JIRA_PROJECT_KEY", ""),
    )
