from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field

from app.models.artifact import ArtifactType
from app.models.project import Project
from app.models.workflow_run import WorkflowRun, WorkflowStepName


@dataclass(frozen=True)
class StageExecutionContext:
    run: WorkflowRun
    project: Project
    step: WorkflowStepName
    triggered_at: datetime


class StageArtifactDraft(BaseModel):
    artifact_type: ArtifactType
    title: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class StageExecutionResult(BaseModel):
    step: WorkflowStepName
    status: Literal["completed", "failed"] = "completed"
    summary: str
    logs: list[str] = Field(default_factory=list)
    artifacts: list[StageArtifactDraft] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowStageService(Protocol):
    step_name: WorkflowStepName

    async def execute(self, context: StageExecutionContext) -> StageExecutionResult:
        ...
