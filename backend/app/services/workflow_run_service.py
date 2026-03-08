import logging
from datetime import datetime, timezone
from uuid import uuid4

from app.models.workflow_run import WORKFLOW_STEP_SEQUENCE, WorkflowRun, WorkflowStep
from app.orchestration.mock_workflow_orchestrator import MockWorkflowOrchestrator
from app.orchestration.run_update_publisher import RunUpdatePublisher
from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.workflow_run_repository import WorkflowRunRepository
from app.services.errors import EntityNotFoundError
from app.services.run_workspace_service import RunWorkspaceService

logger = logging.getLogger(__name__)


class WorkflowRunService:
    def __init__(
        self,
        run_repository: WorkflowRunRepository,
        project_repository: ProjectRepository,
        artifact_repository: ArtifactRepository,
        orchestrator: MockWorkflowOrchestrator,
        run_update_publisher: RunUpdatePublisher | None = None,
        workspace_service: RunWorkspaceService | None = None,
    ) -> None:
        self._run_repository = run_repository
        self._project_repository = project_repository
        self._artifact_repository = artifact_repository
        self._orchestrator = orchestrator
        self._run_update_publisher = run_update_publisher
        self._workspace_service = workspace_service

    async def start_run(self, project_id: str) -> WorkflowRun:
        project = await self._project_repository.get_by_id(project_id)
        if project is None:
            raise EntityNotFoundError(f"Project '{project_id}' not found")

        now = datetime.now(timezone.utc)
        steps = [
            WorkflowStep(
                name=name,
                status="in_progress" if index == 0 else "pending",
                started_at=now if index == 0 else None,
            )
            for index, name in enumerate(WORKFLOW_STEP_SEQUENCE)
        ]

        run = WorkflowRun(
            id=str(uuid4()),
            project_id=project_id,
            status="running",
            current_step=steps[0].name,
            steps=steps,
            created_at=now,
            updated_at=now,
            artifacts=[],
            execution_event_ids=[],
        )

        if self._workspace_service is not None:
            self._workspace_service.initialize_run_workspace(run.id)

        created = await self._run_repository.create(run)
        await self._publish_run_update(created)
        self._orchestrator.schedule_run(created.id)
        return created

    async def get_run(self, run_id: str) -> WorkflowRun | None:
        return await self._run_repository.get_by_id(run_id)

    async def list_project_runs(self, project_id: str) -> list[WorkflowRun]:
        project = await self._project_repository.get_by_id(project_id)
        if project is None:
            raise EntityNotFoundError(f"Project '{project_id}' not found")
        return await self._run_repository.list_by_project_id(project_id)

    async def delete_run(self, run_id: str) -> None:
        run = await self._run_repository.get_by_id(run_id)
        if run is None:
            raise EntityNotFoundError(f"Run '{run_id}' not found")

        await self._artifact_repository.delete_by_run_id(run_id)
        await self._run_repository.delete(run_id)
        if self._workspace_service is not None:
            self._workspace_service.delete_run_workspace(run_id)

    async def _publish_run_update(self, run: WorkflowRun) -> None:
        if self._run_update_publisher is None:
            return
        try:
            await self._run_update_publisher.publish_run_update(run)
        except Exception:
            logger.exception("Failed to publish websocket run update for '%s'", run.id)
