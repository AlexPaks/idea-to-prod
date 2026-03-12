import logging

from app.services.agents._common import (
    build_agent,
    build_prompt,
    execute_agent,
    parse_model_result,
)
from app.services.schemas.architecture_result import ArchitectureResult
from app.services.schemas.code_generation_result import CodeGenerationResult
from app.services.schemas.design_result import DesignResult

logger = logging.getLogger(__name__)


class TestGenerationAgent:
    def __init__(self) -> None:
        binding = build_agent(
            name="test-generation",
            prompt_file="test_generation_prompt.md",
        )
        self.agent = binding.agent
        self.prompt_template = binding.prompt_template

    async def run(
        self,
        idea: str,
        architecture: ArchitectureResult,
        detailed_design: DesignResult,
        code_generation: CodeGenerationResult,
    ) -> CodeGenerationResult:
        logger.info("stage=test_generation event=start")
        payload = {
            "user_idea": idea,
            "architecture": architecture.model_dump(),
            "detailed_design": detailed_design.model_dump(),
            "code_generation": code_generation.model_dump(),
        }
        prompt = build_prompt(self.prompt_template, payload)

        try:
            logger.info("stage=test_generation event=llm_call_start")
            result = await execute_agent(self.agent, prompt)
            logger.info("stage=test_generation event=llm_call_complete")
            typed = parse_model_result("test_generation", result, CodeGenerationResult)
            logger.info("stage=test_generation event=validation_success")
            logger.info("stage=test_generation event=complete")
            return typed
        except Exception:
            logger.exception("stage=test_generation event=error")
            raise
