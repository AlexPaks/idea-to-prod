import logging

from app.services.agents._common import (
    build_agent,
    build_prompt,
    execute_agent,
    parse_model_result,
)
from app.services.schemas.code_generation_result import CodeGenerationResult
from app.services.schemas.repair_result import RepairResult

logger = logging.getLogger(__name__)


class RepairAgent:
    def __init__(self) -> None:
        binding = build_agent(
            name="repair-agent",
            prompt_file="failure_repair_prompt.md",
        )
        self.agent = binding.agent
        self.prompt_template = binding.prompt_template

    async def run(
        self,
        failure_type: str,
        failure_context: str,
        code_generation: CodeGenerationResult,
    ) -> RepairResult:
        logger.info("stage=repair event=start")
        payload = {
            "failure_type": failure_type,
            "failure_context": failure_context,
            "code_generation": code_generation.model_dump(),
        }
        prompt = build_prompt(self.prompt_template, payload)

        try:
            logger.info("stage=repair event=llm_call_start")
            result = await execute_agent(self.agent, prompt)
            logger.info("stage=repair event=llm_call_complete")
            typed = parse_model_result("repair", result, RepairResult)
            logger.info("stage=repair event=validation_success")
            logger.info("stage=repair event=complete")
            return typed
        except Exception:
            logger.exception("stage=repair event=error")
            raise
