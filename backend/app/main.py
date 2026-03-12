import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.artifacts import router as artifacts_router
from app.api.generated_files import router as generated_files_router
from app.api.github_connection import router as github_connection_router
from app.api.google_drive_connection import router as google_drive_connection_router
from app.api.jira_connection import router as jira_connection_router
from app.api.projects import router as projects_router
from app.api.run_updates_ws import router as run_updates_ws_router
from app.api.workflow_runs import router as workflow_runs_router
from app.core.logging_config import configure_logging
from app.core.settings import get_settings
from app.db.mongo import MongoResources, connect_to_mongo, disconnect_from_mongo
from app.models.github_connection import GitHubConnectionPayload
from app.models.google_drive_connection import GoogleDriveConnectionPayload
from app.models.jira_connection import JiraConnectionPayload
from app.repositories.errors import RepositoryError
from app.repositories.mongo_artifact_repository import MongoArtifactRepository
from app.repositories.mongo_github_connection_repository import (
    MongoGitHubConnectionRepository,
)
from app.repositories.mongo_google_drive_connection_repository import (
    MongoGoogleDriveConnectionRepository,
)
from app.repositories.mongo_jira_connection_repository import MongoJiraConnectionRepository
from app.repositories.mongo_project_repository import MongoProjectRepository
from app.repositories.mongo_workflow_run_repository import MongoWorkflowRunRepository
from app.orchestration.mock_workflow_orchestrator import MockWorkflowOrchestrator
from app.realtime.run_updates_hub import RunUpdatesHub
from app.services.artifact_service import ArtifactService
from app.services.generated_file_service import GeneratedFileService
from app.services.github_connection_service import GitHubConnectionService
from app.services.google_drive_connection_service import GoogleDriveConnectionService
from app.services.jira_connection_service import JiraConnectionService
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
        google_drive_connection_repository = MongoGoogleDriveConnectionRepository(
            resources.database,
            resources.collections.google_drive_connections,
        )
        github_connection_repository = MongoGitHubConnectionRepository(
            resources.database,
            resources.collections.github_connections,
        )
        jira_connection_repository = MongoJiraConnectionRepository(
            resources.database,
            resources.collections.jira_connections,
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
        high_level_design_service = HighLevelDesignService(
            llm_client,
            prompt_loader,
        )
        detailed_design_service = DetailedDesignService(
            llm_client,
            prompt_loader,
            artifact_repository,
        )
        google_drive_connection_service = GoogleDriveConnectionService(
            repository=google_drive_connection_repository,
            high_level_design_service=high_level_design_service,
            detailed_design_service=detailed_design_service,
            default_payload=GoogleDriveConnectionPayload(
                enabled=settings.google_drive_mcp_enabled,
                server_url=settings.google_drive_mcp_url,
                tool_name=settings.google_drive_mcp_tool_name,
                read_tool_name=settings.google_drive_mcp_read_tool_name,
                folder_id=settings.google_drive_mcp_folder_id,
                timeout_seconds=settings.google_drive_mcp_timeout_seconds,
                arguments_template_json=settings.google_drive_mcp_arguments_template_json,
                read_arguments_template_json=settings.google_drive_mcp_read_arguments_template_json,
            ),
        )
        github_connection_service = GitHubConnectionService(
            repository=github_connection_repository,
            default_payload=GitHubConnectionPayload(
                enabled=settings.github_mcp_enabled,
                server_url=settings.github_mcp_url,
                tool_name=settings.github_mcp_tool_name,
                timeout_seconds=settings.github_mcp_timeout_seconds,
                arguments_template_json=settings.github_mcp_arguments_template_json,
                owner=settings.github_owner,
                repository=settings.github_repository,
            ),
        )
        jira_connection_service = JiraConnectionService(
            repository=jira_connection_repository,
            default_payload=JiraConnectionPayload(
                enabled=settings.jira_mcp_enabled,
                server_url=settings.jira_mcp_url,
                tool_name=settings.jira_mcp_tool_name,
                timeout_seconds=settings.jira_mcp_timeout_seconds,
                arguments_template_json=settings.jira_mcp_arguments_template_json,
                project_key=settings.jira_project_key,
            ),
        )
        await google_drive_connection_service.initialize_runtime()
        orchestrator = MockWorkflowOrchestrator(
            workflow_run_repository,
            project_repository,
            artifact_repository,
            stage_services=[
                high_level_design_service,
                detailed_design_service,
                CodeGenerationService(artifact_repository),
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
        app.state.high_level_design_service = high_level_design_service
        app.state.detailed_design_service = detailed_design_service
        app.state.google_drive_connection_service = google_drive_connection_service
        app.state.github_connection_service = github_connection_service
        app.state.jira_connection_service = jira_connection_service
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
app.include_router(google_drive_connection_router)
app.include_router(github_connection_router)
app.include_router(jira_connection_router)


@app.exception_handler(RepositoryError)
async def repository_error_handler(
    request: Request, error: RepositoryError
) -> JSONResponse:
    logger.error("Repository error on %s %s: %s", request.method, request.url.path, error)
    return JSONResponse(status_code=503, content={"detail": "Storage service unavailable"})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "backend"}
