import logging
from asyncio import to_thread

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
)

logger = logging.getLogger(__name__)


class DetailedDesignService:
    step_name = "detailed_design"

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
            "Rendered detailed design prompt template.",
            "Generated implementation-level technical plan with LLM.",
        ]

        try:
            prompt = self._prompt_loader.render(
                "detailed_design.md",
                {
                    "project_name": context.project.name,
                    "project_idea": context.project.idea,
                },
            )
            design_content = await to_thread(self._llm_client.generate, prompt)
        except LLMConfigurationError as exc:
            logger.warning(
                "LLM configuration unavailable for detailed design on run '%s': %s",
                context.run.id,
                exc,
            )
            design_content = (
                f"# Detailed Technical Design\n\n"
                f"Project: {context.project.name}\n\n"
                "## API Boundaries\n"
                "- `/api/projects` for project creation and retrieval.\n"
                "- `/api/projects/{project_id}/runs` for run orchestration start/listing.\n"
                "- `/api/runs/{run_id}/artifacts` for run-scoped output retrieval.\n\n"
                "## Data Contracts\n"
                "- Project document stores core business intent and metadata.\n"
                "- WorkflowRun document tracks progression, current step, and artifact IDs.\n"
                "- Artifact document stores output payloads for design/code/test stages.\n\n"
                "## Execution Strategy\n"
                "- Background orchestrator advances one step at a fixed delay.\n"
                "- Step completion triggers deterministic mocked artifact generation.\n"
                "- Run details page polls for status and artifacts.\n"
            )
            design_source = "fallback_mock"
            logs = [
                "LLM configuration unavailable; used fallback detailed design.",
                str(exc),
            ]
        except LLMRateLimitError as exc:
            logger.warning(
                "Rate-limited while generating detailed design for run '%s': %s",
                context.run.id,
                exc,
            )
            return StageExecutionResult(
                step=self.step_name,
                status="failed",
                summary="LLM rate limit reached during detailed design generation",
                logs=[str(exc)],
                metadata={"error_type": "rate_limit"},
            )
        except LLMNetworkError as exc:
            logger.error(
                "Network error while generating detailed design for run '%s'",
                context.run.id,
                exc_info=exc,
            )
            return StageExecutionResult(
                step=self.step_name,
                status="failed",
                summary="Network error during detailed design generation",
                logs=[str(exc)],
                metadata={"error_type": "network"},
            )
        except (LLMInvalidResponseError, FileNotFoundError, KeyError) as exc:
            logger.error(
                "Invalid detailed design generation for run '%s'",
                context.run.id,
                exc_info=exc,
            )
            return StageExecutionResult(
                step=self.step_name,
                status="failed",
                summary="Invalid response while generating detailed design",
                logs=[str(exc)],
                metadata={"error_type": "invalid_response"},
            )
        except Exception as exc:
            logger.exception(
                "Unexpected error during detailed design generation for run '%s'",
                context.run.id,
            )
            return StageExecutionResult(
                step=self.step_name,
                status="failed",
                summary="Unexpected error during detailed design generation",
                logs=[str(exc)],
                metadata={"error_type": "unexpected"},
            )

        artifact = StageArtifactDraft(
            artifact_type="detailed_design",
            title="Detailed Technical Design",
            content=design_content.strip(),
            metadata={"source": design_source, "stage": self.step_name},
        )

        return StageExecutionResult(
            step=self.step_name,
            summary="Generated detailed technical design artifact",
            logs=logs,
            artifacts=[artifact],
            metadata={"artifact_count": 1},
        )
