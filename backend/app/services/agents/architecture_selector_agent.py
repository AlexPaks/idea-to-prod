import logging

from app.services.agents._common import (
    build_agent,
    build_prompt,
    execute_agent,
    parse_model_result,
)
from app.services.schemas.architecture_result import ArchitectureResult
from app.services.schemas.idea_classification_result import IdeaClassificationResult

logger = logging.getLogger(__name__)


class ArchitectureSelectorAgent:
    def __init__(self) -> None:
        binding = build_agent(
            name="architecture-selector",
            prompt_file="architecture_selection_prompt.md",
        )
        self.agent = binding.agent
        self.prompt_template = binding.prompt_template

    async def run(
        self, idea: str, classification: IdeaClassificationResult
    ) -> ArchitectureResult:
        logger.info("stage=architecture_selection event=start")
        payload = {
            "user_idea": idea,
            "classification": classification.model_dump(),
        }
        prompt = build_prompt(self.prompt_template, payload)

        try:
            logger.info("stage=architecture_selection event=llm_call_start")
            result = await execute_agent(self.agent, prompt)
            logger.info("stage=architecture_selection event=llm_call_complete")
            typed = parse_model_result("architecture_selection", result, ArchitectureResult)
            logger.info("stage=architecture_selection event=validation_success")
            logger.info("stage=architecture_selection event=complete")
            return typed
        except Exception:
            logger.exception("stage=architecture_selection event=error")
            raise
