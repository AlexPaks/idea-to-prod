import logging

from app.services.agents._common import build_agent, execute_agent, parse_model_result
from app.services.schemas.code_generation_result import CodeGenerationResult
from app.services.schemas.repair_result import RepairResult

logger = logging.getLogger(__name__)


class RepairAgent:
    def __init__(self) -> None:
        self.agent = build_agent(
            name="repair-agent",
            prompt_file="repair_prompt.md",
        )

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

        try:
            result = await execute_agent(self.agent, payload)
            typed = parse_model_result(
                "repair",
                result,
                RepairResult,
                fallback=RepairResult(
                    repair_summary="No-op placeholder repair plan.",
                    failure_type=failure_type,
                    root_cause="unknown",
                    changes=[],
                ),
            )
            logger.info("stage=repair event=complete")
            return typed
        except Exception:
            logger.exception("stage=repair event=error")
            raise
