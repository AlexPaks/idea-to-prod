import logging

from app.services.agents._common import build_agent, execute_agent, parse_model_result
from app.services.schemas.architecture_result import ArchitectureResult
from app.services.schemas.design_result import DesignResult
from app.services.schemas.idea_classification_result import IdeaClassificationResult

logger = logging.getLogger(__name__)


class HighLevelDesignAgent:
    def __init__(self) -> None:
        self.agent = build_agent(
            name="high-level-design",
            prompt_file="hl_design_prompt.md",
        )

    async def run(
        self,
        idea: str,
        classification: IdeaClassificationResult,
        architecture: ArchitectureResult,
    ) -> DesignResult:
        logger.info("stage=high_level_design event=start")
        payload = {
            "user_idea": idea,
            "classification": classification.model_dump(),
            "architecture": architecture.model_dump(),
        }

        try:
            result = await execute_agent(self.agent, payload)
            typed = parse_model_result(
                "high_level_design",
                result,
                DesignResult,
                fallback=DesignResult(
                    title="High-Level Design",
                    summary="Top-level architecture and module boundaries.",
                    content=(
                        "# High-Level Design\n\n"
                        "This is a placeholder high-level design output. "
                        "Replace with real LLM generation in the next step."
                    ),
                ),
            )
            logger.info("stage=high_level_design event=complete")
            return typed
        except Exception:
            logger.exception("stage=high_level_design event=error")
            raise
