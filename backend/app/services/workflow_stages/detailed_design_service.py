import logging
from asyncio import to_thread

from app.repositories.artifact_repository import ArtifactRepository
from app.services.integrations.google_drive_mcp_client import (
    GoogleDriveMcpClient,
    GoogleDriveMcpError,
)
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

    def __init__(
        self,
        llm_client: LLMClient,
        prompt_loader: PromptLoader,
        artifact_repository: ArtifactRepository,
        google_drive_client: GoogleDriveMcpClient | None = None,
        require_google_drive_read: bool = False,
    ) -> None:
        self._llm_client = llm_client
        self._prompt_loader = prompt_loader
        self._artifact_repository = artifact_repository
        self._google_drive_client = google_drive_client
        self._require_google_drive_read = require_google_drive_read

    def configure_google_drive(
        self,
        google_drive_client: GoogleDriveMcpClient | None,
        require_google_drive_read: bool,
    ) -> None:
        self._google_drive_client = google_drive_client
        self._require_google_drive_read = require_google_drive_read

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

        high_level_context = ""
        high_level_context_source = "none"
        try:
            high_level_context, high_level_context_source = await self._load_high_level_context(
                context.run.id,
                context.project.id,
            )
            prompt = self._prompt_loader.render(
                "detailed_design.md",
                {
                    "project_name": context.project.name,
                    "project_idea": context.project.idea,
                },
            )
            if high_level_context:
                prompt = (
                    f"{prompt}\n\n"
                    "## High-Level Design Context\n"
                    f"{high_level_context}\n"
                )
                logs.append(
                    f"Loaded High-Level Design context from '{high_level_context_source}'."
                )
            else:
                logs.append("No High-Level Design context found; generated from project idea only.")
            design_content = await to_thread(self._llm_client.generate, prompt)
        except GoogleDriveMcpError as exc:
            logger.error(
                "Failed to read high-level design from Google Drive for run '%s': %s",
                context.run.id,
                exc,
            )
            return StageExecutionResult(
                step=self.step_name,
                status="failed",
                summary="Failed to load High-Level Design from Google Drive",
                logs=[str(exc)],
                metadata={"error_type": "google_drive_read"},
            )
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
            metadata={
                "source": design_source,
                "stage": self.step_name,
                "high_level_context_source": high_level_context_source,
            },
        )

        return StageExecutionResult(
            step=self.step_name,
            summary="Generated detailed technical design artifact",
            logs=logs,
            artifacts=[artifact],
            metadata={"artifact_count": 1},
        )

    async def _load_high_level_context(self, run_id: str, project_id: str) -> tuple[str, str]:
        artifacts = await self._artifact_repository.list_by_run_id(run_id)
        high_level_artifacts = [
            artifact for artifact in artifacts if artifact.artifact_type == "high_level_design"
        ]
        if not high_level_artifacts:
            return "", "none"

        latest = high_level_artifacts[-1]
        metadata = latest.metadata if isinstance(latest.metadata, dict) else {}
        document_id = metadata.get("google_drive_document_id")
        document_url = metadata.get("google_drive_document_url")

        if self._google_drive_client is not None:
            has_document_ref = isinstance(document_id, str) or isinstance(document_url, str)
            if not has_document_ref and self._require_google_drive_read:
                raise GoogleDriveMcpError(
                    "High-Level Design artifact is missing Google Drive document metadata"
                )
            if has_document_ref:
                try:
                    content = await to_thread(
                        self._google_drive_client.read_document_content,
                        document_id if isinstance(document_id, str) else None,
                        document_url if isinstance(document_url, str) else None,
                        project_id,
                        run_id,
                    )
                except GoogleDriveMcpError:
                    if self._require_google_drive_read:
                        raise
                else:
                    if content.strip():
                        return content.strip(), "google_drive"

        if latest.content.strip():
            return latest.content.strip(), "artifact_fallback"

        return "", "none"
