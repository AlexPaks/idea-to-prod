import asyncio
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from app.models.workflow_run import WorkflowTestResult

SUMMARY_PATTERN = re.compile(
    r"(?:(?P<passed>\d+)\s+passed)?(?:,\s*)?"
    r"(?:(?P<failed>\d+)\s+failed)?(?:,\s*)?"
    r"(?:(?P<errors>\d+)\s+error(?:s)?)?(?:,\s*)?"
    r"(?:(?P<skipped>\d+)\s+skipped)?",
    re.IGNORECASE,
)


class LocalTestRunnerService:
    """Executes local pytest runs in generated workspace directories."""

    def __init__(self, timeout_seconds: float = 60.0) -> None:
        self._timeout_seconds = timeout_seconds

    async def run_pytest(self, workspace_path: Path) -> WorkflowTestResult:
        try:
            completed = await asyncio.to_thread(
                subprocess.run,
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                ],
                cwd=str(workspace_path),
                capture_output=True,
                text=True,
                env={**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"},
                timeout=self._timeout_seconds,
            )
        except subprocess.TimeoutExpired as error:
            stdout = _ensure_text(error.stdout)
            stderr = _ensure_text(error.stderr)
            return WorkflowTestResult(
                exit_code=-1,
                stdout=stdout,
                stderr=f"{stderr}\nTimed out after {self._timeout_seconds:.0f}s".strip(),
                status="failed",
                summary=f"Timed out after {self._timeout_seconds:.0f}s",
                executed_at=datetime.now(timezone.utc),
            )

        stdout = _ensure_text(completed.stdout)
        stderr = _ensure_text(completed.stderr)
        exit_code = completed.returncode if completed.returncode is not None else 1
        status = "passed" if exit_code == 0 else "failed"
        summary = _extract_summary(stdout, stderr, exit_code)

        return WorkflowTestResult(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            status=status,
            summary=summary,
            executed_at=datetime.now(timezone.utc),
        )


def _extract_summary(stdout: str, stderr: str, exit_code: int) -> str:
    for line in reversed(stdout.splitlines()):
        parsed = SUMMARY_PATTERN.search(line)
        if parsed and parsed.group(0).strip():
            return parsed.group(0).strip()

    for line in reversed(stderr.splitlines()):
        parsed = SUMMARY_PATTERN.search(line)
        if parsed and parsed.group(0).strip():
            return parsed.group(0).strip()

    return "Tests passed" if exit_code == 0 else "Tests failed"


def _ensure_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return value.decode("utf-8", errors="replace")
