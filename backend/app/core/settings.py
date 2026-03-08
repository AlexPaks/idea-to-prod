import os
from dataclasses import dataclass
from functools import lru_cache


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
    )
