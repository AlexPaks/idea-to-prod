import logging
from textwrap import dedent

from app.services.workflow_stage_models import (
    StageArtifactDraft,
    StageExecutionContext,
    StageExecutionResult,
)

logger = logging.getLogger(__name__)


class HighLevelDesignService:
    step_name = "high_level_design"

    async def execute(self, context: StageExecutionContext) -> StageExecutionResult:
        logger.info(
            "Running stage '%s' for run '%s' and project '%s'",
            self.step_name,
            context.run.id,
            context.project.id,
        )

        artifact = StageArtifactDraft(
            artifact_type="high_level_design",
            title="High-Level Design",
            content=dedent(
                f"""
                # High-Level Design

                Product: {context.project.name}

                ## Objective
                Deliver an end-to-end experience for the idea: "{context.project.idea}".

                ## Core Components
                - Frontend SPA for user interactions and orchestration visibility.
                - Backend API for project, workflow, and artifact lifecycle.
                - MongoDB persistence for projects, runs, and generated outputs.

                ## Main Flow
                1. User creates a project.
                2. User starts generation run.
                3. Workflow advances through design/code/test stages.
                4. Generated artifacts are attached to the run and rendered in UI.
                """
            ).strip(),
            metadata={"mock_source": "high_level_design_service"},
        )

        return StageExecutionResult(
            step=self.step_name,
            summary="Generated high-level design artifact",
            logs=[
                "Converted product idea into system-level architecture view.",
                "Outlined primary components and handoff boundaries.",
            ],
            artifacts=[artifact],
            metadata={"artifact_count": 1},
        )
