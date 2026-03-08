import logging
from textwrap import dedent

from app.services.workflow_stage_models import (
    StageArtifactDraft,
    StageExecutionContext,
    StageExecutionResult,
)

logger = logging.getLogger(__name__)


class DetailedDesignService:
    step_name = "detailed_design"

    async def execute(self, context: StageExecutionContext) -> StageExecutionResult:
        logger.info(
            "Running stage '%s' for run '%s' and project '%s'",
            self.step_name,
            context.run.id,
            context.project.id,
        )

        artifact = StageArtifactDraft(
            artifact_type="detailed_design",
            title="Detailed Technical Design",
            content=dedent(
                f"""
                # Detailed Technical Design

                Project: {context.project.name}

                ## API Boundaries
                - `/api/projects` for project creation and retrieval.
                - `/api/projects/{{project_id}}/runs` for run orchestration start/listing.
                - `/api/runs/{{run_id}}/artifacts` for run-scoped output retrieval.

                ## Data Contracts
                - Project document stores core business intent and metadata.
                - WorkflowRun document tracks progression, current step, and artifact IDs.
                - Artifact document stores output payloads for design/code/test stages.

                ## Execution Strategy
                - Background orchestrator advances one step at a fixed delay.
                - Step completion triggers deterministic mocked artifact generation.
                - Run details page polls every 2.5 seconds for status and artifacts.
                """
            ).strip(),
            metadata={"mock_source": "detailed_design_service"},
        )

        return StageExecutionResult(
            step=self.step_name,
            summary="Generated detailed technical design artifact",
            logs=[
                "Mapped API boundaries and persistence responsibilities.",
                "Captured run/artifact data lifecycle and polling strategy.",
            ],
            artifacts=[artifact],
            metadata={"artifact_count": 1},
        )
