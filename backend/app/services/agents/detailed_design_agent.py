import logging

from app.services.agents._common import build_agent, execute_agent, parse_model_result
from app.services.schemas.architecture_result import ArchitectureResult
from app.services.schemas.design_result import DesignResult
from app.services.schemas.idea_classification_result import IdeaClassificationResult

logger = logging.getLogger(__name__)


class DetailedDesignAgent:
    def __init__(self) -> None:
        self.agent = build_agent(
            name="detailed-design",
            prompt_file="detailed_design_prompt.md",
        )

    async def run(
        self,
        idea: str,
        classification: IdeaClassificationResult,
        architecture: ArchitectureResult,
        hl_design: DesignResult,
    ) -> DesignResult:
        logger.info("stage=detailed_design event=start")
        payload = {
            "user_idea": idea,
            "classification": classification.model_dump(),
            "architecture": architecture.model_dump(),
            "hl_design": hl_design.model_dump(),
        }

        try:
            result = await execute_agent(self.agent, payload)
            typed = parse_model_result(
                "detailed_design",
                result,
                DesignResult,
                fallback=DesignResult(
                    title="Detailed Design",
                    summary="Detailed technical specification for implementation.",
                    content=(
                        "# Detailed Design\n\n"
                        "This is a placeholder detailed design output. "
                        "Replace with real LLM generation in the next step."
                    ),
                ),
            )
            logger.info("stage=detailed_design event=complete")
            return typed
        except Exception:
            logger.exception("stage=detailed_design event=error")
            raise
