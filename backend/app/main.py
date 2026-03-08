import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.artifacts import router as artifacts_router
from app.api.projects import router as projects_router
from app.api.workflow_runs import router as workflow_runs_router
from app.core.logging_config import configure_logging
from app.core.settings import get_settings
from app.db.mongo import MongoResources, connect_to_mongo, disconnect_from_mongo
from app.orchestration.mock_artifact_generator import MockArtifactGenerator
from app.repositories.errors import RepositoryError
from app.repositories.mongo_artifact_repository import MongoArtifactRepository
from app.repositories.mongo_project_repository import MongoProjectRepository
from app.repositories.mongo_workflow_run_repository import MongoWorkflowRunRepository
from app.orchestration.mock_workflow_orchestrator import MockWorkflowOrchestrator
from app.services.artifact_service import ArtifactService
from app.services.project_service import ProjectService
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
        orchestrator = MockWorkflowOrchestrator(
            workflow_run_repository,
            project_repository,
            artifact_repository,
            MockArtifactGenerator(),
            step_delay_seconds=settings.mock_workflow_step_delay_seconds,
        )

        app.state.mongo = resources
        app.state.project_service = ProjectService(project_repository)
        app.state.workflow_run_service = WorkflowRunService(
            run_repository=workflow_run_repository,
            project_repository=project_repository,
            orchestrator=orchestrator,
        )
        app.state.artifact_service = ArtifactService(
            artifact_repository=artifact_repository,
            run_repository=workflow_run_repository,
        )
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


@app.exception_handler(RepositoryError)
async def repository_error_handler(
    request: Request, error: RepositoryError
) -> JSONResponse:
    logger.error("Repository error on %s %s: %s", request.method, request.url.path, error)
    return JSONResponse(status_code=503, content={"detail": "Storage service unavailable"})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "backend"}
