import logging
from textwrap import dedent

from app.services.workflow_stage_models import (
    StageExecutionContext,
    StageExecutionResult,
    StageGeneratedFileDraft,
)

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
            generated_files=[
                StageGeneratedFileDraft(
                    relative_path="tests/test_basic.py",
                    language="python",
                    description="Generated smoke test placeholder",
                    content=dedent(
                        """
                        def test_sanity() -> None:
                            assert True
                        """
                    ).strip(),
                )
            ],
            metadata={
                "artifact_count": 0,
                "planned_cases": 6,
                "generated_file_count": 1,
            },
        )
