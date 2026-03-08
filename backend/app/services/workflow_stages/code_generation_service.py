import logging
from textwrap import dedent

from app.services.workflow_stage_models import (
    StageArtifactDraft,
    StageExecutionContext,
    StageExecutionResult,
)

logger = logging.getLogger(__name__)


class CodeGenerationService:
    step_name = "code_generation"

    async def execute(self, context: StageExecutionContext) -> StageExecutionResult:
        logger.info(
            "Running stage '%s' for run '%s' and project '%s'",
            self.step_name,
            context.run.id,
            context.project.id,
        )

        artifact = StageArtifactDraft(
            artifact_type="code_summary",
            title="Code Generation Summary",
            content=dedent(
                f"""
                # Code Summary

                Project: {context.project.name}

                ## Implemented Modules
                - Domain models for project/run/artifact entities.
                - Repository layer with MongoDB persistence.
                - Mock orchestration engine with timed step transitions.
                - Frontend run dashboard with timeline and artifact browser.

                ## Notable Decisions
                - Async repository contracts to keep storage adapter-agnostic.
                - Artifact model designed for future AI-generated content replacement.
                - Minimal API surface with typed schemas for stable frontend integration.
                """
            ).strip(),
            metadata={"mock_source": "code_generation_service"},
        )

        return StageExecutionResult(
            step=self.step_name,
            summary="Generated code summary artifact",
            logs=[
                "Built mocked implementation summary for current workflow iteration.",
                "Captured architectural decisions that preserve adapter flexibility.",
            ],
            artifacts=[artifact],
            metadata={"artifact_count": 1},
        )
