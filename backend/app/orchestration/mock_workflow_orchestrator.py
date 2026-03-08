import asyncio
import logging
from datetime import datetime, timezone

from app.models.workflow_run import WorkflowRun
from app.repositories.errors import RepositoryError
from app.repositories.workflow_run_repository import WorkflowRunRepository

logger = logging.getLogger(__name__)


class MockWorkflowOrchestrator:
    """Mock workflow progression that simulates staged agent execution."""

    def __init__(
        self,
        run_repository: WorkflowRunRepository,
        step_delay_seconds: float = 2.5,
    ) -> None:
        self._run_repository = run_repository
        self._step_delay_seconds = step_delay_seconds
        self._tasks: dict[str, asyncio.Task[None]] = {}

    def schedule_run(self, run_id: str) -> None:
        active_task = self._tasks.get(run_id)
        if active_task and not active_task.done():
            return

        task = asyncio.create_task(self._progress_run(run_id), name=f"workflow-run-{run_id}")
        self._tasks[run_id] = task
        task.add_done_callback(lambda _: self._tasks.pop(run_id, None))

    async def shutdown(self) -> None:
        if not self._tasks:
            return

        for task in self._tasks.values():
            task.cancel()

        await asyncio.gather(*self._tasks.values(), return_exceptions=True)
        self._tasks.clear()

    async def _progress_run(self, run_id: str) -> None:
        try:
            while True:
                await asyncio.sleep(self._step_delay_seconds)

                run = await self._run_repository.get_by_id(run_id)
                if run is None:
                    logger.warning("Workflow run '%s' disappeared during orchestration", run_id)
                    return

                if run.status in {"completed", "failed"}:
                    return

                next_run = _advance_run(run)
                await self._run_repository.update(next_run)

                if next_run.status == "completed":
                    return
        except asyncio.CancelledError:
            logger.info("Cancelled mock orchestration for run '%s'", run_id)
            raise
        except RepositoryError:
            logger.exception("Repository failure while orchestrating run '%s'", run_id)
        except Exception:
            logger.exception("Unexpected failure while orchestrating run '%s'", run_id)


def _advance_run(run: WorkflowRun) -> WorkflowRun:
    now = datetime.now(timezone.utc)
    next_state = run.model_copy(deep=True)
    next_state.updated_at = now

    if not next_state.current_step:
        return next_state

    current_index = next(
        (index for index, step in enumerate(next_state.steps) if step.name == next_state.current_step),
        -1,
    )
    if current_index < 0:
        return next_state

    current = next_state.steps[current_index]
    current.status = "completed"
    current.completed_at = now

    if current_index == len(next_state.steps) - 1:
        next_state.status = "completed"
        next_state.current_step = current.name
        return next_state

    following = next_state.steps[current_index + 1]
    following.status = "in_progress"
    following.started_at = now
    next_state.current_step = following.name
    next_state.status = "running"
    return next_state
