from typing import Protocol

from app.models.workflow_run import WorkflowRun


class RunUpdatePublisher(Protocol):
    async def publish_run_update(self, run: WorkflowRun) -> None:
        ...
