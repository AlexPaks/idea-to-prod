import logging

from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import ValidationError
from pymongo.errors import PyMongoError

from app.models.google_drive_connection import GoogleDriveConnectionConfig
from app.repositories.errors import RepositoryError
from app.repositories.google_drive_connection_repository import (
    GoogleDriveConnectionRepository,
)

logger = logging.getLogger(__name__)

_DOCUMENT_ID = "google_drive_connection"


class MongoGoogleDriveConnectionRepository(GoogleDriveConnectionRepository):
    def __init__(self, database: AsyncIOMotorDatabase, collection_name: str) -> None:
        self._collection = database[collection_name]

    async def get(self) -> GoogleDriveConnectionConfig | None:
        try:
            document = await self._collection.find_one({"_id": _DOCUMENT_ID})
            if document is None:
                return None
            payload = dict(document)
            payload.pop("_id", None)
            return GoogleDriveConnectionConfig.model_validate(payload)
        except (PyMongoError, ValidationError, TypeError, ValueError) as error:
            logger.exception("Failed to load Google Drive connection settings")
            raise RepositoryError("Failed to load Google Drive connection settings") from error

    async def upsert(
        self, config: GoogleDriveConnectionConfig
    ) -> GoogleDriveConnectionConfig:
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
            logger.exception("Failed to save Google Drive connection settings")
            raise RepositoryError("Failed to save Google Drive connection settings") from error
