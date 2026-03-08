import logging

from app.services.workflow.idea_to_prod_workflow import IdeaToProdWorkflow
from app.services.workflow.workflow_state import WorkflowState

logger = logging.getLogger(__name__)


class WorkflowRunner:
    def __init__(self, workflow: IdeaToProdWorkflow | None = None) -> None:
        self.workflow = workflow or IdeaToProdWorkflow()

    async def run(self, run_id: str, project_id: str, idea: str) -> WorkflowState:
        logger.info(
            "workflow_runner event=start run_id=%s project_id=%s",
            run_id,
            project_id,
        )
        initial_state = WorkflowState(
            run_id=run_id,
            project_id=project_id,
            idea=idea,
            status="pending",
            current_step=None,
        )
        final_state = await self.workflow.run(initial_state)
        logger.info(
            "workflow_runner event=complete run_id=%s status=%s",
            final_state.run_id,
            final_state.status,
        )
        return final_state
