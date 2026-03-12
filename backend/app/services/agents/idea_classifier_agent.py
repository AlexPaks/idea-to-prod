import logging

from app.services.agents._common import (
    build_agent,
    build_prompt,
    execute_agent,
    parse_model_result,
)
from app.services.schemas.idea_classification_result import IdeaClassificationResult

logger = logging.getLogger(__name__)


class IdeaClassifierAgent:
    def __init__(self) -> None:
        binding = build_agent(
            name="idea-classifier",
            prompt_file="idea_classifier_prompt.md",
        )
        self.agent = binding.agent
        self.prompt_template = binding.prompt_template

    async def run(self, idea: str) -> IdeaClassificationResult:
        logger.info("stage=idea_classification event=start")
        payload = {"user_idea": idea}
        prompt = build_prompt(self.prompt_template, payload)

        try:
            logger.info("stage=idea_classification event=llm_call_start")
            result = await execute_agent(self.agent, prompt)
            logger.info("stage=idea_classification event=llm_call_complete")
            typed = parse_model_result("idea_classification", result, IdeaClassificationResult)
            logger.info("stage=idea_classification event=validation_success")
            logger.info("stage=idea_classification event=complete")
            return typed
        except Exception:
            logger.exception("stage=idea_classification event=error")
            raise
