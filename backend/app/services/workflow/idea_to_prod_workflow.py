import logging
from typing import Any

from app.services.agents.architecture_selector_agent import ArchitectureSelectorAgent
from app.services.agents.code_generation_agent import CodeGenerationAgent
from app.services.agents.detailed_design_agent import DetailedDesignAgent
from app.services.agents.hl_design_agent import HighLevelDesignAgent
from app.services.agents.idea_classifier_agent import IdeaClassifierAgent
from app.services.agents.repair_agent import RepairAgent
from app.services.agents.test_generation_agent import TestGenerationAgent
from app.services.schemas.code_generation_result import CodeGenerationResult
from app.services.schemas.repair_result import RepairResult
from app.services.workflow.workflow_state import WorkflowState

logger = logging.getLogger(__name__)


class IdeaToProdWorkflow:
    def __init__(
        self,
        idea_classifier: IdeaClassifierAgent | None = None,
        architecture_selector: ArchitectureSelectorAgent | None = None,
        hl_design_agent: HighLevelDesignAgent | None = None,
        detailed_design_agent: DetailedDesignAgent | None = None,
        code_generation_agent: CodeGenerationAgent | None = None,
        test_generation_agent: TestGenerationAgent | None = None,
        repair_agent: RepairAgent | None = None,
    ) -> None:
        self.idea_classifier = idea_classifier or IdeaClassifierAgent()
        self.architecture_selector = architecture_selector or ArchitectureSelectorAgent()
        self.hl_design_agent = hl_design_agent or HighLevelDesignAgent()
        self.detailed_design_agent = detailed_design_agent or DetailedDesignAgent()
        self.code_generation_agent = code_generation_agent or CodeGenerationAgent()
        self.test_generation_agent = test_generation_agent or TestGenerationAgent()
        self.repair_agent = repair_agent or RepairAgent()

    async def run(self, state: WorkflowState) -> WorkflowState:
        logger.info("workflow=idea_to_prod event=start run_id=%s", state.run_id)
        state.status = "running"

        try:
            state.current_step = "idea_classification"
            state.classification = await self.idea_classifier.run(state.idea)

            state.current_step = "architecture_selection"
            state.architecture = await self.architecture_selector.run(
                idea=state.idea,
                classification=state.classification,
            )

            state.current_step = "high_level_design"
            state.hl_design = await self.hl_design_agent.run(
                idea=state.idea,
                classification=state.classification,
                architecture=state.architecture,
            )

            state.current_step = "detailed_design"
            state.detailed_design = await self.detailed_design_agent.run(
                idea=state.idea,
                classification=state.classification,
                architecture=state.architecture,
                hl_design=state.hl_design,
            )

            state.current_step = "code_generation"
            state.code_generation_result = await self.code_generation_agent.run(
                idea=state.idea,
                architecture=state.architecture,
                detailed_design=state.detailed_design,
            )
            await self.write_generated_files(state.run_id, state.code_generation_result)

            state.current_step = "test_generation"
            state.test_generation_result = await self.test_generation_agent.run(
                idea=state.idea,
                architecture=state.architecture,
                detailed_design=state.detailed_design,
                code_generation=state.code_generation_result,
            )

            state.current_step = "completed"
            state.status = "completed"
            logger.info("workflow=idea_to_prod event=complete run_id=%s", state.run_id)
            return state
        except Exception as exc:
            state.status = "failed"
            state.errors.append(str(exc))
            logger.exception("workflow=idea_to_prod event=error run_id=%s", state.run_id)
            return state

    async def write_generated_files(
        self,
        run_id: str,
        generated: CodeGenerationResult,
    ) -> None:
        """Hook for workspace writer integration."""
        logger.info(
            "workflow=idea_to_prod event=hook_write_generated_files run_id=%s file_count=%s",
            run_id,
            len(generated.files),
        )

    async def execute_tests(self, run_id: str) -> dict[str, Any]:
        """Hook for local/remote test execution integration."""
        logger.info(
            "workflow=idea_to_prod event=hook_execute_tests run_id=%s",
            run_id,
        )
        return {"status": "not_implemented"}

    async def apply_repair(self, run_id: str, repair: RepairResult) -> None:
        """Hook for applying repair changes to workspace."""
        logger.info(
            "workflow=idea_to_prod event=hook_apply_repair run_id=%s change_count=%s",
            run_id,
            len(repair.changes),
        )
