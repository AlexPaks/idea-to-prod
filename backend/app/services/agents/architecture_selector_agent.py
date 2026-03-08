import logging

from app.services.agents._common import build_agent, execute_agent, parse_model_result
from app.services.schemas.architecture_result import ArchitectureResult
from app.services.schemas.idea_classification_result import IdeaClassificationResult

logger = logging.getLogger(__name__)


class ArchitectureSelectorAgent:
    def __init__(self) -> None:
        self.agent = build_agent(
            name="architecture-selector",
            prompt_file="architecture_selector_prompt.md",
        )

    async def run(
        self, idea: str, classification: IdeaClassificationResult
    ) -> ArchitectureResult:
        logger.info("stage=architecture_selection event=start")
        payload = {
            "user_idea": idea,
            "classification": classification.model_dump(),
        }

        try:
            result = await execute_agent(self.agent, payload)
            typed = parse_model_result(
                "architecture_selection",
                result,
                ArchitectureResult,
                fallback=ArchitectureResult(
                    frontend_stack="React + Vite + TypeScript",
                    backend_stack="FastAPI (Python)",
                    database="MongoDB",
                    auth_strategy="none_yet",
                    deployment_shape="local_first_monorepo",
                    background_jobs=["async workflow orchestration"],
                    recommended_modules=[
                        "projects",
                        "workflow_runs",
                        "artifacts",
                        "generated_files",
                    ],
                    recommended_entities=[
                        "Project",
                        "WorkflowRun",
                        "Artifact",
                        "GeneratedFile",
                    ],
                    api_groups=["projects", "runs", "artifacts", "files"],
                    frontend_pages=[
                        "projects_list",
                        "project_details",
                        "run_details",
                    ],
                    testing_strategy=["pytest for generated backend code"],
                    notes=["Fallback architecture used due to placeholder output."],
                ),
            )
            logger.info("stage=architecture_selection event=complete")
            return typed
        except Exception:
            logger.exception("stage=architecture_selection event=error")
            raise
