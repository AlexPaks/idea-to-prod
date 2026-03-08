import logging
from dataclasses import dataclass

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from app.core.settings import Settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CollectionRegistry:
    projects: str
    workflow_runs: str
    artifacts: str
    execution_events: str


@dataclass(frozen=True)
class MongoResources:
    client: AsyncIOMotorClient
    database: AsyncIOMotorDatabase
    collections: CollectionRegistry


def _build_collections(settings: Settings) -> CollectionRegistry:
    return CollectionRegistry(
        projects=settings.projects_collection,
        workflow_runs=settings.workflow_runs_collection,
        artifacts=settings.artifacts_collection,
        execution_events=settings.execution_events_collection,
    )


async def connect_to_mongo(settings: Settings) -> MongoResources:
    client = AsyncIOMotorClient(settings.mongodb_uri, tz_aware=True)
    database = client[settings.mongodb_db_name]

    try:
        await database.command("ping")
        logger.info("Connected to MongoDB database '%s'", settings.mongodb_db_name)
    except PyMongoError:
        logger.exception("Unable to connect to MongoDB")
        client.close()
        raise

    return MongoResources(
        client=client,
        database=database,
        collections=_build_collections(settings),
    )


async def disconnect_from_mongo(resources: MongoResources | None) -> None:
    if resources is None:
        return

    resources.client.close()
    logger.info("MongoDB client closed")
