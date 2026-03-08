from typing import Any, Literal

from pydantic import BaseModel, Field

from app.services.schemas.architecture_result import ArchitectureResult
from app.services.schemas.code_generation_result import CodeGenerationResult
from app.services.schemas.design_result import DesignResult
from app.services.schemas.idea_classification_result import IdeaClassificationResult

WorkflowStatus = Literal["pending", "running", "completed", "failed"]
WorkflowStep = Literal[
    "idea_classification",
    "architecture_selection",
    "high_level_design",
    "detailed_design",
    "code_generation",
    "test_generation",
    "repair",
    "completed",
]


class WorkflowState(BaseModel):
    run_id: str
    project_id: str
    idea: str
    classification: IdeaClassificationResult | None = None
    architecture: ArchitectureResult | None = None
    hl_design: DesignResult | None = None
    detailed_design: DesignResult | None = None
    code_generation_result: CodeGenerationResult | None = None
    test_generation_result: CodeGenerationResult | None = None
    test_results: dict[str, Any] | None = None
    repair_attempts: int = 0
    status: WorkflowStatus = "pending"
    current_step: WorkflowStep | None = None
    errors: list[str] = Field(default_factory=list)
