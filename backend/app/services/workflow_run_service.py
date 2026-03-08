from datetime import datetime, timezone
from uuid import uuid4

from app.models.workflow_run import WORKFLOW_STEP_SEQUENCE, WorkflowRun, WorkflowStep
from app.orchestration.mock_workflow_orchestrator import MockWorkflowOrchestrator
from app.repositories.project_repository import ProjectRepository
from app.repositories.workflow_run_repository import WorkflowRunRepository
from app.services.errors import EntityNotFoundError


class WorkflowRunService:
    def __init__(
        self,
        run_repository: WorkflowRunRepository,
        project_repository: ProjectRepository,
        orchestrator: MockWorkflowOrchestrator,
    ) -> None:
        self._run_repository = run_repository
        self._project_repository = project_repository
        self._orchestrator = orchestrator

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

        created = await self._run_repository.create(run)
        self._orchestrator.schedule_run(created.id)
        return created

    async def get_run(self, run_id: str) -> WorkflowRun | None:
        return await self._run_repository.get_by_id(run_id)

    async def list_project_runs(self, project_id: str) -> list[WorkflowRun]:
        project = await self._project_repository.get_by_id(project_id)
        if project is None:
            raise EntityNotFoundError(f"Project '{project_id}' not found")
        return await self._run_repository.list_by_project_id(project_id)
