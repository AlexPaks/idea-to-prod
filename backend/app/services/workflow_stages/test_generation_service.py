import logging

from app.services.workflow_stage_models import StageExecutionContext, StageExecutionResult

logger = logging.getLogger(__name__)


class TestGenerationService:
    step_name = "test_generation"

    async def execute(self, context: StageExecutionContext) -> StageExecutionResult:
        logger.info(
            "Running stage '%s' for run '%s' and project '%s'",
            self.step_name,
            context.run.id,
            context.project.id,
        )

        return StageExecutionResult(
            step=self.step_name,
            summary="Prepared mocked test plan and scenarios",
            logs=[
                "Derived critical path scenarios from design and code summaries.",
                "Prepared smoke and regression test sets for execution stage.",
            ],
            artifacts=[],
            metadata={"artifact_count": 0, "planned_cases": 6},
        )
