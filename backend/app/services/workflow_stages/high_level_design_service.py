import logging
from asyncio import to_thread
from textwrap import dedent

from app.services.llm.llm_client import (
    LLMConfigurationError,
    LLMInvalidResponseError,
    LLMNetworkError,
    LLMRateLimitError,
    LLMClient,
)
from app.services.llm.prompt_loader import PromptLoader
from app.services.workflow_stage_models import (
    StageArtifactDraft,
    StageExecutionContext,
    StageExecutionResult,
    StageGeneratedFileDraft,
)

logger = logging.getLogger(__name__)


class HighLevelDesignService:
    step_name = "high_level_design"

    def __init__(self, llm_client: LLMClient, prompt_loader: PromptLoader) -> None:
        self._llm_client = llm_client
        self._prompt_loader = prompt_loader

    async def execute(self, context: StageExecutionContext) -> StageExecutionResult:
        logger.info(
            "Running stage '%s' for run '%s' and project '%s'",
            self.step_name,
            context.run.id,
            context.project.id,
        )

        design_source = "llm"
        logs = [
            "Rendered high-level design prompt template.",
            "Generated high-level architecture with LLM.",
        ]

        try:
            prompt = self._prompt_loader.render(
                "hl_design.md",
                {
                    "project_name": context.project.name,
                    "project_idea": context.project.idea,
                },
            )
            design_content = await to_thread(self._llm_client.generate, prompt)
        except LLMConfigurationError as exc:
            logger.warning(
                "LLM configuration unavailable for high-level design on run '%s': %s",
                context.run.id,
                exc,
            )
            design_content = dedent(
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
            ).strip()
            design_source = "fallback_mock"
            logs = [
                "LLM configuration unavailable; used fallback high-level design.",
                str(exc),
            ]
        except LLMRateLimitError as exc:
            logger.warning(
                "Rate-limited while generating high-level design for run '%s': %s",
                context.run.id,
                exc,
            )
            return StageExecutionResult(
                step=self.step_name,
                status="failed",
                summary="LLM rate limit reached during high-level design generation",
                logs=[str(exc)],
                metadata={"error_type": "rate_limit"},
            )
        except LLMNetworkError as exc:
            logger.error(
                "Network error while generating high-level design for run '%s'",
                context.run.id,
                exc_info=exc,
            )
            return StageExecutionResult(
                step=self.step_name,
                status="failed",
                summary="Network error during high-level design generation",
                logs=[str(exc)],
                metadata={"error_type": "network"},
            )
        except (LLMInvalidResponseError, FileNotFoundError, KeyError) as exc:
            logger.error(
                "Invalid high-level design generation for run '%s'",
                context.run.id,
                exc_info=exc,
            )
            return StageExecutionResult(
                step=self.step_name,
                status="failed",
                summary="Invalid response while generating high-level design",
                logs=[str(exc)],
                metadata={"error_type": "invalid_response"},
            )
        except Exception as exc:
            logger.exception(
                "Unexpected error during high-level design generation for run '%s'",
                context.run.id,
            )
            return StageExecutionResult(
                step=self.step_name,
                status="failed",
                summary="Unexpected error during high-level design generation",
                logs=[str(exc)],
                metadata={"error_type": "unexpected"},
            )

        artifact = StageArtifactDraft(
            artifact_type="high_level_design",
            title="High-Level Design",
            content=design_content.strip(),
            metadata={"source": design_source, "stage": self.step_name},
        )

        return StageExecutionResult(
            step=self.step_name,
            summary="Generated high-level design artifact",
            logs=logs,
            artifacts=[artifact],
            generated_files=[
                StageGeneratedFileDraft(
                    relative_path="README.md",
                    language="markdown",
                    description="Generated package overview",
                    content=dedent(
                        f"""
                        # {context.project.name}

                        ## Idea
                        {context.project.idea}

                        ## Generated Package
                        This package was generated by IdeaToProd mocked workflow.

                        ## Structure
                        - frontend/src/App.tsx
                        - backend/main.py
                        - tests/test_basic.py
                        """
                    ).strip(),
                )
            ],
            metadata={"artifact_count": 1, "generated_file_count": 1},
        )
