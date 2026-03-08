import logging

from app.services.agents._common import build_agent, execute_agent, parse_model_result
from app.services.schemas.idea_classification_result import IdeaClassificationResult

logger = logging.getLogger(__name__)


class IdeaClassifierAgent:
    def __init__(self) -> None:
        self.agent = build_agent(
            name="idea-classifier",
            prompt_file="idea_classifier_prompt.md",
        )

    async def run(self, idea: str) -> IdeaClassificationResult:
        logger.info("stage=idea_classification event=start")
        payload = {"user_idea": idea}

        try:
            result = await execute_agent(self.agent, payload)
            typed = parse_model_result(
                "idea_classification",
                result,
                IdeaClassificationResult,
                fallback=IdeaClassificationResult(
                    project_type="web_app",
                    domain="general",
                    target_users=["end users"],
                    primary_interfaces=["web"],
                    core_features=["project creation", "workflow orchestration"],
                    secondary_features=["analytics"],
                    data_complexity="medium",
                    business_logic_complexity="medium",
                    integration_complexity="low",
                    recommended_template="fullstack_spa_api",
                    recommended_architecture_pattern="modular_monolith",
                    notes=["Fallback classification used due to placeholder output."],
                ),
            )
            logger.info("stage=idea_classification event=complete")
            return typed
        except Exception:
            logger.exception("stage=idea_classification event=error")
            raise
