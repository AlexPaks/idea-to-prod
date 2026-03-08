import logging

from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import ValidationError
from pymongo import DESCENDING
from pymongo.errors import PyMongoError

from app.models.project import Project
from app.repositories.errors import RepositoryError
from app.repositories.mappers.project_document_mapper import (
    document_to_project,
    project_to_document,
)
from app.repositories.project_repository import ProjectRepository

logger = logging.getLogger(__name__)


class MongoProjectRepository(ProjectRepository):
    def __init__(self, database: AsyncIOMotorDatabase, collection_name: str) -> None:
        self._collection = database[collection_name]

    async def create(self, project: Project) -> Project:
        try:
            await self._collection.insert_one(project_to_document(project))
            return project
        except PyMongoError as error:
            logger.exception("Failed to create project in MongoDB")
            raise RepositoryError("Failed to create project") from error

    async def list(self) -> list[Project]:
        try:
            projects: list[Project] = []
            cursor = self._collection.find({}).sort("created_at", DESCENDING)
            async for document in cursor:
                projects.append(document_to_project(document))
            return projects
        except (PyMongoError, ValidationError, KeyError, TypeError) as error:
            logger.exception("Failed to list projects from MongoDB")
            raise RepositoryError("Failed to list projects") from error

    async def get_by_id(self, project_id: str) -> Project | None:
        try:
            document = await self._collection.find_one({"_id": project_id})
            if document is None:
                return None
            return document_to_project(document)
        except (PyMongoError, ValidationError, KeyError, TypeError) as error:
            logger.exception("Failed to load project '%s' from MongoDB", project_id)
            raise RepositoryError("Failed to load project") from error

    async def delete(self, project_id: str) -> bool:
        try:
            result = await self._collection.delete_one({"_id": project_id})
            return result.deleted_count > 0
        except PyMongoError as error:
            logger.exception("Failed to delete project '%s' from MongoDB", project_id)
            raise RepositoryError("Failed to delete project") from error
