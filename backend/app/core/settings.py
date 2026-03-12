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
    mock_workflow_step_delay_seconds: float
    test_runner_timeout_seconds: float
    generated_runs_root_dir: str
    llm_provider: str
    openai_api_key: str
    gemini_api_key: str


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


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    _load_backend_env_file()
    frontend_origins = _split_csv(
        os.getenv("FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
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
        mock_workflow_step_delay_seconds=_read_float(
            "MOCK_WORKFLOW_STEP_DELAY_SECONDS", 2.5
        ),
        test_runner_timeout_seconds=_read_float("TEST_RUNNER_TIMEOUT_SECONDS", 60.0),
        generated_runs_root_dir=os.getenv("GENERATED_RUNS_ROOT_DIR", "generated_runs"),
        llm_provider=os.getenv("LLM_PROVIDER", "openai"),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
    )
