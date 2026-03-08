import logging

from app.services.agents._common import (
    build_agent,
    build_prompt,
    execute_agent,
    parse_model_result,
)
from app.services.schemas.architecture_result import ArchitectureResult
from app.services.schemas.design_result import DesignResult
from app.services.schemas.idea_classification_result import IdeaClassificationResult

logger = logging.getLogger(__name__)


class HighLevelDesignAgent:
    def __init__(self) -> None:
        binding = build_agent(
            name="high-level-design",
            prompt_file="hl_design_prompt.md",
        )
        self.agent = binding.agent
        self.prompt_template = binding.prompt_template

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
        prompt = build_prompt(self.prompt_template, payload)

        try:
            logger.info("stage=high_level_design event=llm_call_start")
            result = await execute_agent(self.agent, prompt)
            logger.info("stage=high_level_design event=llm_call_complete")
            typed = parse_model_result("high_level_design", result, DesignResult)
            logger.info("stage=high_level_design event=validation_success")
            logger.info("stage=high_level_design event=complete")
            return typed
        except Exception:
            logger.exception("stage=high_level_design event=error")
            raise
