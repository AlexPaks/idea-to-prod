from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

WorkflowRunStatus = Literal["queued", "running", "completed", "failed"]
WorkflowStepStatus = Literal["pending", "in_progress", "completed", "failed"]
WorkflowStepName = Literal[
    "intake",
    "high_level_design",
    "detailed_design",
    "code_generation",
    "test_generation",
    "test_execution",
    "completed",
]

WORKFLOW_STEP_SEQUENCE: tuple[WorkflowStepName, ...] = (
    "intake",
    "high_level_design",
    "detailed_design",
    "code_generation",
    "test_generation",
    "test_execution",
    "completed",
)


class WorkflowStep(BaseModel):
    name: WorkflowStepName
    status: WorkflowStepStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None


class WorkflowRun(BaseModel):
    id: str
    project_id: str
    status: WorkflowRunStatus
    current_step: WorkflowStepName | None
    steps: list[WorkflowStep]
    created_at: datetime
    updated_at: datetime
    artifacts: list[str] = Field(default_factory=list)
    execution_event_ids: list[str] = Field(default_factory=list)
