import asyncio
import logging
from datetime import datetime, timezone
from uuid import uuid4

from app.models.artifact import Artifact, ArtifactType
from app.models.project import Project
from app.models.workflow_run import WorkflowRun, WorkflowStepName
from app.orchestration.mock_artifact_generator import MockArtifactGenerator
from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.errors import RepositoryError
from app.repositories.project_repository import ProjectRepository
from app.repositories.workflow_run_repository import WorkflowRunRepository

logger = logging.getLogger(__name__)


class MockWorkflowOrchestrator:
    """Mock workflow progression that simulates staged agent execution."""

    def __init__(
        self,
        run_repository: WorkflowRunRepository,
        project_repository: ProjectRepository,
        artifact_repository: ArtifactRepository,
        artifact_generator: MockArtifactGenerator,
        step_delay_seconds: float = 2.5,
    ) -> None:
        self._run_repository = run_repository
        self._project_repository = project_repository
        self._artifact_repository = artifact_repository
        self._artifact_generator = artifact_generator
        self._step_delay_seconds = step_delay_seconds
        self._tasks: dict[str, asyncio.Task[None]] = {}

    def schedule_run(self, run_id: str) -> None:
        active_task = self._tasks.get(run_id)
        if active_task and not active_task.done():
            return

        task = asyncio.create_task(
            self._progress_run(run_id),
            name=f"workflow-run-{run_id}",
        )
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

                next_run, completed_step = _advance_run(run)
                if completed_step is not None:
                    await self._create_artifact_for_step(next_run, completed_step)

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

    async def _create_artifact_for_step(
        self,
        run: WorkflowRun,
        completed_step: WorkflowStepName,
    ) -> None:
        project = await self._project_repository.get_by_id(run.project_id)
        if project is None:
            logger.warning(
                "Skipping artifact generation for run '%s': project '%s' missing",
                run.id,
                run.project_id,
            )
            return

        draft = self._artifact_generator.generate(completed_step, project)
        if draft is None:
            return

        artifact = _build_artifact(run, project, draft.artifact_type, draft.title, draft.content)
        created = await self._artifact_repository.create(artifact)
        run.artifacts.append(created.id)
        run.updated_at = datetime.now(timezone.utc)


def _build_artifact(
    run: WorkflowRun,
    project: Project,
    artifact_type: ArtifactType,
    title: str,
    content: str,
) -> Artifact:
    return Artifact(
        id=str(uuid4()),
        run_id=run.id,
        project_id=project.id,
        artifact_type=artifact_type,
        title=title,
        content=content,
        created_at=datetime.now(timezone.utc),
    )


def _advance_run(run: WorkflowRun) -> tuple[WorkflowRun, WorkflowStepName | None]:
    now = datetime.now(timezone.utc)
    next_state = run.model_copy(deep=True)
    next_state.updated_at = now

    if not next_state.current_step:
        return next_state, None

    current_index = next(
        (
            index
            for index, step in enumerate(next_state.steps)
            if step.name == next_state.current_step
        ),
        -1,
    )
    if current_index < 0:
        return next_state, None

    current = next_state.steps[current_index]
    current.status = "completed"
    current.completed_at = now

    if current_index == len(next_state.steps) - 1:
        next_state.status = "completed"
        next_state.current_step = current.name
        return next_state, current.name

    following = next_state.steps[current_index + 1]
    following.status = "in_progress"
    following.started_at = now
    next_state.current_step = following.name
    next_state.status = "running"
    return next_state, current.name
