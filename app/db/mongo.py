"""Async MongoDB client and FastAPI dependency."""

from typing import Annotated

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

_client: AsyncIOMotorClient | None = None


async def init_mongo() -> None:
    """Create the shared MongoDB client. Called once during app startup."""
    global _client
    _client = AsyncIOMotorClient(settings.mongodb_url)


async def close_mongo() -> None:
    """Close the shared MongoDB client. Called once during app shutdown."""
    global _client
    if _client is not None:
        _client.close()
        _client = None


def get_mongo_db() -> AsyncIOMotorDatabase:
    """Return the shared MongoDB database.

    Returns:
        AsyncIOMotorDatabase: Motor async database instance.

    Raises:
        RuntimeError: If called before the app lifespan initialises MongoDB.
    """
    if _client is None:
        raise RuntimeError("MongoDB client is not initialised.")
    return _client[settings.mongodb_db]


MongoDep = Annotated[AsyncIOMotorDatabase, Depends(get_mongo_db)]
