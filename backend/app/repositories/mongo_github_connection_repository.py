import logging

from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import ValidationError
from pymongo.errors import PyMongoError

from app.models.github_connection import GitHubConnectionConfig
from app.repositories.errors import RepositoryError
from app.repositories.github_connection_repository import GitHubConnectionRepository

logger = logging.getLogger(__name__)

_DOCUMENT_ID = "github_connection"


class MongoGitHubConnectionRepository(GitHubConnectionRepository):
    def __init__(self, database: AsyncIOMotorDatabase, collection_name: str) -> None:
        self._collection = database[collection_name]

    async def get(self) -> GitHubConnectionConfig | None:
        try:
            document = await self._collection.find_one({"_id": _DOCUMENT_ID})
            if document is None:
                return None
            payload = dict(document)
            payload.pop("_id", None)
            return GitHubConnectionConfig.model_validate(payload)
        except (PyMongoError, ValidationError, TypeError, ValueError) as error:
            logger.exception("Failed to load GitHub connection settings")
            raise RepositoryError("Failed to load GitHub connection settings") from error

    async def upsert(self, config: GitHubConnectionConfig) -> GitHubConnectionConfig:
        try:
            document = config.model_dump(mode="python")
            document["_id"] = _DOCUMENT_ID
            await self._collection.replace_one(
                {"_id": _DOCUMENT_ID},
                document,
                upsert=True,
            )
            return config
        except PyMongoError as error:
            logger.exception("Failed to save GitHub connection settings")
            raise RepositoryError("Failed to save GitHub connection settings") from error
