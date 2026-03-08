import logging

from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import ValidationError
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import PyMongoError

from app.models.artifact import Artifact
from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.errors import RepositoryError
from app.repositories.mappers.artifact_document_mapper import (
    artifact_to_document,
    document_to_artifact,
)

logger = logging.getLogger(__name__)


class MongoArtifactRepository(ArtifactRepository):
    def __init__(self, database: AsyncIOMotorDatabase, collection_name: str) -> None:
        self._collection = database[collection_name]

    async def ensure_indexes(self) -> None:
        try:
            await self._collection.create_index(
                [("run_id", ASCENDING), ("created_at", DESCENDING)]
            )
            await self._collection.create_index([("project_id", ASCENDING)])
        except PyMongoError as error:
            logger.exception("Failed to create artifact indexes")
            raise RepositoryError("Failed to initialize artifact indexes") from error

    async def create(self, artifact: Artifact) -> Artifact:
        try:
            await self._collection.insert_one(artifact_to_document(artifact))
            return artifact
        except PyMongoError as error:
            logger.exception("Failed to create artifact in MongoDB")
            raise RepositoryError("Failed to create artifact") from error

    async def get_by_id(self, artifact_id: str) -> Artifact | None:
        try:
            document = await self._collection.find_one({"_id": artifact_id})
            if document is None:
                return None
            return document_to_artifact(document)
        except (PyMongoError, ValidationError, KeyError, TypeError) as error:
            logger.exception("Failed to load artifact '%s'", artifact_id)
            raise RepositoryError("Failed to load artifact") from error

    async def list_by_run_id(self, run_id: str) -> list[Artifact]:
        try:
            artifacts: list[Artifact] = []
            cursor = self._collection.find({"run_id": run_id}).sort("created_at", ASCENDING)
            async for document in cursor:
                artifacts.append(document_to_artifact(document))
            return artifacts
        except (PyMongoError, ValidationError, KeyError, TypeError) as error:
            logger.exception("Failed to list artifacts for run '%s'", run_id)
            raise RepositoryError("Failed to list artifacts") from error

    async def delete_by_run_id(self, run_id: str) -> int:
        try:
            result = await self._collection.delete_many({"run_id": run_id})
            return result.deleted_count
        except PyMongoError as error:
            logger.exception("Failed to delete artifacts for run '%s'", run_id)
            raise RepositoryError("Failed to delete artifacts") from error
