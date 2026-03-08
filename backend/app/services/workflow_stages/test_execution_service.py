import logging
from textwrap import dedent

from app.services.workflow_stage_models import (
    StageArtifactDraft,
    StageExecutionContext,
    StageExecutionResult,
)

logger = logging.getLogger(__name__)


class TestExecutionService:
    step_name = "test_execution"

    async def execute(self, context: StageExecutionContext) -> StageExecutionResult:
        logger.info(
            "Running stage '%s' for run '%s' and project '%s'",
            self.step_name,
            context.run.id,
            context.project.id,
        )

        artifact = StageArtifactDraft(
            artifact_type="test_summary",
            title="Test Execution Summary",
            content=dedent(
                f"""
                # Test Summary

                Project: {context.project.name}

                ## Smoke Checks
                - API startup and MongoDB connectivity: passed.
                - Workflow progression from intake to completed: passed.
                - Artifact generation and retrieval endpoints: passed.
                - Frontend build with run polling and artifact rendering: passed.

                ## Observations
                - Polling interval provides near-real-time UI updates without heavy load.
                - Artifact retrieval remains stable while run is still progressing.
                """
            ).strip(),
            metadata={"mock_source": "test_execution_service"},
        )

        return StageExecutionResult(
            step=self.step_name,
            summary="Generated test execution summary artifact",
            logs=[
                "Executed mocked smoke checks across API, orchestration, and UI.",
                "Recorded verification notes for artifact and run visibility.",
            ],
            artifacts=[artifact],
            metadata={"artifact_count": 1, "passed_checks": 4},
        )
