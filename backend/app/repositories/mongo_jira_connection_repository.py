import logging

from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import ValidationError
from pymongo.errors import PyMongoError

from app.models.jira_connection import JiraConnectionConfig
from app.repositories.errors import RepositoryError
from app.repositories.jira_connection_repository import JiraConnectionRepository

logger = logging.getLogger(__name__)

_DOCUMENT_ID = "jira_connection"


class MongoJiraConnectionRepository(JiraConnectionRepository):
    def __init__(self, database: AsyncIOMotorDatabase, collection_name: str) -> None:
        self._collection = database[collection_name]

    async def get(self) -> JiraConnectionConfig | None:
        try:
            document = await self._collection.find_one({"_id": _DOCUMENT_ID})
            if document is None:
                return None
            payload = dict(document)
            payload.pop("_id", None)
            return JiraConnectionConfig.model_validate(payload)
        except (PyMongoError, ValidationError, TypeError, ValueError) as error:
            logger.exception("Failed to load Jira connection settings")
            raise RepositoryError("Failed to load Jira connection settings") from error

    async def upsert(self, config: JiraConnectionConfig) -> JiraConnectionConfig:
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
            logger.exception("Failed to save Jira connection settings")
            raise RepositoryError("Failed to save Jira connection settings") from error
