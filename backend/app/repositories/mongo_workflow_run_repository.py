import logging

from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import ValidationError
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import PyMongoError

from app.models.workflow_run import WorkflowRun
from app.repositories.errors import RepositoryError
from app.repositories.mappers.workflow_run_document_mapper import (
    document_to_workflow_run,
    workflow_run_to_document,
)
from app.repositories.workflow_run_repository import WorkflowRunRepository

logger = logging.getLogger(__name__)


class MongoWorkflowRunRepository(WorkflowRunRepository):
    def __init__(self, database: AsyncIOMotorDatabase, collection_name: str) -> None:
        self._collection = database[collection_name]

    async def ensure_indexes(self) -> None:
        try:
            await self._collection.create_index(
                [("project_id", ASCENDING), ("created_at", DESCENDING)]
            )
        except PyMongoError as error:
            logger.exception("Failed to create workflow run indexes")
            raise RepositoryError("Failed to initialize workflow run indexes") from error

    async def create(self, run: WorkflowRun) -> WorkflowRun:
        try:
            await self._collection.insert_one(workflow_run_to_document(run))
            return run
        except PyMongoError as error:
            logger.exception("Failed to create workflow run in MongoDB")
            raise RepositoryError("Failed to create workflow run") from error

    async def update(self, run: WorkflowRun) -> WorkflowRun:
        try:
            result = await self._collection.replace_one(
                {"_id": run.id},
                workflow_run_to_document(run),
            )
            if result.matched_count == 0:
                raise RepositoryError("Workflow run not found")
            return run
        except RepositoryError:
            raise
        except PyMongoError as error:
            logger.exception("Failed to update workflow run '%s'", run.id)
            raise RepositoryError("Failed to update workflow run") from error

    async def get_by_id(self, run_id: str) -> WorkflowRun | None:
        try:
            document = await self._collection.find_one({"_id": run_id})
            if document is None:
                return None
            return document_to_workflow_run(document)
        except (PyMongoError, ValidationError, KeyError, TypeError) as error:
            logger.exception("Failed to load workflow run '%s'", run_id)
            raise RepositoryError("Failed to load workflow run") from error

    async def list_by_project_id(self, project_id: str) -> list[WorkflowRun]:
        try:
            runs: list[WorkflowRun] = []
            cursor = self._collection.find({"project_id": project_id}).sort(
                "created_at", DESCENDING
            )
            async for document in cursor:
                runs.append(document_to_workflow_run(document))
            return runs
        except (PyMongoError, ValidationError, KeyError, TypeError) as error:
            logger.exception("Failed to list workflow runs for project '%s'", project_id)
            raise RepositoryError("Failed to list workflow runs") from error

    async def delete(self, run_id: str) -> bool:
        try:
            result = await self._collection.delete_one({"_id": run_id})
            return result.deleted_count > 0
        except PyMongoError as error:
            logger.exception("Failed to delete workflow run '%s'", run_id)
            raise RepositoryError("Failed to delete workflow run") from error
