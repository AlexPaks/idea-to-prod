import logging
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from app.services.errors import InvalidRequestError
from app.services.workflow_stage_models import StageGeneratedFileDraft

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WorkspaceFileWriteResult:
    relative_path: str
    language: str | None
    size_bytes: int
    updated_at: datetime


class RunWorkspaceService:
    """Manages local output workspace files scoped by workflow run id."""

    def __init__(self, base_directory: str) -> None:
        self._base_path = Path(base_directory).resolve()
        self._base_path.mkdir(parents=True, exist_ok=True)

    def initialize_run_workspace(self, run_id: str) -> Path:
        run_path = self._run_path(run_id)
        run_path.mkdir(parents=True, exist_ok=True)
        return run_path

    def get_run_workspace_path(self, run_id: str) -> Path:
        return self._run_path(run_id)

    def write_files(
        self,
        run_id: str,
        files: list[StageGeneratedFileDraft],
    ) -> list[WorkspaceFileWriteResult]:
        run_path = self.initialize_run_workspace(run_id)
        write_results: list[WorkspaceFileWriteResult] = []

        for item in files:
            target_path, normalized_relative = self._resolve_run_relative_path(
                run_path,
                item.relative_path,
            )
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(item.content, encoding="utf-8")

            write_results.append(
                WorkspaceFileWriteResult(
                    relative_path=normalized_relative,
                    language=item.language,
                    size_bytes=target_path.stat().st_size,
                    updated_at=datetime.now(timezone.utc),
                )
            )

            logger.info("Generated file for run '%s': %s", run_id, normalized_relative)

        return write_results

    def read_file(self, run_id: str, relative_path: str) -> str:
        run_path = self._run_path(run_id)
        if not run_path.exists():
            raise InvalidRequestError(f"Workspace for run '{run_id}' does not exist")

        target_path, _ = self._resolve_run_relative_path(run_path, relative_path)
        if not target_path.exists() or not target_path.is_file():
            raise InvalidRequestError(f"Generated file '{relative_path}' does not exist")

        return target_path.read_text(encoding="utf-8")

    def delete_run_workspace(self, run_id: str) -> None:
        run_path = self._run_path(run_id)
        if run_path.exists():
            shutil.rmtree(run_path, ignore_errors=True)
            logger.info("Deleted workspace for run '%s'", run_id)

    def _run_path(self, run_id: str) -> Path:
        self._validate_run_id(run_id)
        return (self._base_path / run_id).resolve()

    def _resolve_run_relative_path(
        self,
        run_path: Path,
        relative_path: str,
    ) -> tuple[Path, str]:
        normalized = self._normalize_relative_path(relative_path)
        target_path = (run_path / Path(*normalized.parts)).resolve()
        if not self._is_within_root(target_path, run_path):
            raise InvalidRequestError("Path escapes run workspace")
        return target_path, normalized.as_posix()

    @staticmethod
    def _normalize_relative_path(relative_path: str) -> PurePosixPath:
        normalized = PurePosixPath(relative_path.replace("\\", "/"))
        if normalized.is_absolute() or not normalized.parts:
            raise InvalidRequestError("Generated file path must be a relative path")
        if any(part in {"", ".", ".."} for part in normalized.parts):
            raise InvalidRequestError("Generated file path contains unsafe segments")
        return normalized

    @staticmethod
    def _validate_run_id(run_id: str) -> None:
        if not run_id or "/" in run_id or "\\" in run_id or ".." in run_id:
            raise InvalidRequestError("Invalid run id")

    @staticmethod
    def _is_within_root(candidate: Path, root: Path) -> bool:
        try:
            candidate.relative_to(root)
            return True
        except ValueError:
            return False
