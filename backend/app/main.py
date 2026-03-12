import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.artifacts import router as artifacts_router
from app.api.generated_files import router as generated_files_router
from app.api.projects import router as projects_router
from app.api.run_updates_ws import router as run_updates_ws_router
from app.api.workflow_runs import router as workflow_runs_router
from app.core.logging_config import configure_logging
from app.core.settings import get_settings
from app.db.mongo import MongoResources, connect_to_mongo, disconnect_from_mongo
from app.repositories.errors import RepositoryError
from app.repositories.mongo_artifact_repository import MongoArtifactRepository
from app.repositories.mongo_project_repository import MongoProjectRepository
from app.repositories.mongo_workflow_run_repository import MongoWorkflowRunRepository
from app.orchestration.mock_workflow_orchestrator import MockWorkflowOrchestrator
from app.realtime.run_updates_hub import RunUpdatesHub
from app.services.artifact_service import ArtifactService
from app.services.generated_file_service import GeneratedFileService
from app.services.llm.llm_client import LLMClient
from app.services.llm.prompt_loader import PromptLoader
from app.services.local_test_runner_service import LocalTestRunnerService
from app.services.project_service import ProjectService
from app.services.run_workspace_service import RunWorkspaceService
from app.services.workflow_stages import (
    CodeGenerationService,
    DetailedDesignService,
    HighLevelDesignService,
    TestExecutionService,
    TestGenerationService,
)
from app.services.workflow_run_service import WorkflowRunService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    settings = get_settings()
    resources: MongoResources | None = None
    orchestrator: MockWorkflowOrchestrator | None = None

    try:
        resources = await connect_to_mongo(settings)
        project_repository = MongoProjectRepository(
            resources.database,
            resources.collections.projects,
        )
        workflow_run_repository = MongoWorkflowRunRepository(
            resources.database,
            resources.collections.workflow_runs,
        )
        artifact_repository = MongoArtifactRepository(
            resources.database,
            resources.collections.artifacts,
        )
        await workflow_run_repository.ensure_indexes()
        await artifact_repository.ensure_indexes()
        run_updates_hub = RunUpdatesHub()
        workspace_service = RunWorkspaceService(settings.generated_runs_root_dir)
        llm_client = LLMClient(
            provider=settings.llm_provider,
            openai_api_key=settings.openai_api_key,
            gemini_api_key=settings.gemini_api_key,
        )
        prompt_loader = PromptLoader()
        test_runner_service = LocalTestRunnerService(
            timeout_seconds=settings.test_runner_timeout_seconds
        )
        orchestrator = MockWorkflowOrchestrator(
            workflow_run_repository,
            project_repository,
            artifact_repository,
            stage_services=[
                HighLevelDesignService(llm_client, prompt_loader),
                DetailedDesignService(llm_client, prompt_loader),
                CodeGenerationService(),
                TestGenerationService(),
                TestExecutionService(test_runner_service, workspace_service),
            ],
            workspace_service=workspace_service,
            run_update_publisher=run_updates_hub,
            step_delay_seconds=settings.mock_workflow_step_delay_seconds,
        )

        app.state.mongo = resources
        app.state.run_updates_hub = run_updates_hub
        app.state.workspace_service = workspace_service
        app.state.project_service = ProjectService(
            repository=project_repository,
            run_repository=workflow_run_repository,
            artifact_repository=artifact_repository,
            workspace_service=workspace_service,
        )
        app.state.workflow_run_service = WorkflowRunService(
            run_repository=workflow_run_repository,
            project_repository=project_repository,
            artifact_repository=artifact_repository,
            orchestrator=orchestrator,
            run_update_publisher=run_updates_hub,
            workspace_service=workspace_service,
        )
        app.state.artifact_service = ArtifactService(
            artifact_repository=artifact_repository,
            run_repository=workflow_run_repository,
        )
        app.state.generated_file_service = GeneratedFileService(
            artifact_repository=artifact_repository,
            run_repository=workflow_run_repository,
            workspace_service=workspace_service,
        )
        await app.state.workflow_run_service.resume_incomplete_runs()
        app.state.orchestrator = orchestrator
        app.state.settings = settings
        logger.info("Backend startup complete")
        yield
    finally:
        if orchestrator is not None:
            await orchestrator.shutdown()
        await disconnect_from_mongo(resources)
        logger.info("Backend shutdown complete")


app = FastAPI(title="IdeaToProd Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects_router)
app.include_router(workflow_runs_router)
app.include_router(artifacts_router)
app.include_router(generated_files_router)
app.include_router(run_updates_ws_router)


@app.exception_handler(RepositoryError)
async def repository_error_handler(
    request: Request, error: RepositoryError
) -> JSONResponse:
    logger.error("Repository error on %s %s: %s", request.method, request.url.path, error)
    return JSONResponse(status_code=503, content={"detail": "Storage service unavailable"})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "backend"}
