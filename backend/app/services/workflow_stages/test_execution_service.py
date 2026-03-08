import logging
from textwrap import dedent

from app.services.local_test_runner_service import LocalTestRunnerService
from app.services.run_workspace_service import RunWorkspaceService
from app.services.workflow_stage_models import (
    StageArtifactDraft,
    StageExecutionContext,
    StageExecutionResult,
)

logger = logging.getLogger(__name__)


class TestExecutionService:
    step_name = "test_execution"

    def __init__(
        self,
        test_runner: LocalTestRunnerService,
        workspace_service: RunWorkspaceService,
    ) -> None:
        self._test_runner = test_runner
        self._workspace_service = workspace_service

    async def execute(self, context: StageExecutionContext) -> StageExecutionResult:
        logger.info(
            "Running stage '%s' for run '%s' and project '%s'",
            self.step_name,
            context.run.id,
            context.project.id,
        )

        workspace_path = self._workspace_service.get_run_workspace_path(context.run.id)
        test_result = await self._test_runner.run_pytest(workspace_path)

        status = "completed" if test_result.status == "passed" else "failed"
        summary = (
            f"Pytest passed ({test_result.summary})"
            if test_result.status == "passed"
            else f"Pytest failed ({test_result.summary})"
        )

        summary_artifact = StageArtifactDraft(
            artifact_type="test_summary",
            title="Test Execution Summary",
            content=dedent(
                f"""
                # Test Execution Summary

                Project: {context.project.name}

                ## Outcome
                - Status: {test_result.status}
                - Exit code: {test_result.exit_code}
                - Summary: {test_result.summary}
                """
            ).strip(),
            metadata={
                "mock_source": "test_execution_service",
                "exit_code": test_result.exit_code,
            },
        )

        result_artifact = StageArtifactDraft(
            artifact_type="test_result",
            title="Pytest Raw Output",
            content=dedent(
                f"""
                # Pytest Raw Output

                ## Exit Code
                {test_result.exit_code}

                ## Summary
                {test_result.summary}

                ## STDOUT
                {test_result.stdout or "(empty)"}

                ## STDERR
                {test_result.stderr or "(empty)"}
                """
            ).strip(),
            metadata={
                "exit_code": test_result.exit_code,
                "status": test_result.status,
            },
        )

        return StageExecutionResult(
            step=self.step_name,
            status=status,
            summary=summary,
            logs=[
                f"Pytest exit code: {test_result.exit_code}",
                f"Pytest summary: {test_result.summary}",
            ],
            artifacts=[summary_artifact, result_artifact],
            test_result=test_result,
            metadata={"artifact_count": 2, "test_status": test_result.status},
        )
