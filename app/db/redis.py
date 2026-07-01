"""Async Redis client and FastAPI dependency."""

from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis

from app.core.config import settings

_redis: Redis | None = None


async def init_redis() -> None:
    """Create the shared Redis client. Called once during app startup."""
    global _redis
    _redis = Redis.from_url(settings.redis_url, decode_responses=True)


async def close_redis() -> None:
    """Close the shared Redis client. Called once during app shutdown."""
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


def get_redis() -> Redis:
    """Return the shared async Redis client.

    Returns:
        Redis: Async Redis client instance.

    Raises:
        RuntimeError: If called before the app lifespan initialises Redis.
    """
    if _redis is None:
        raise RuntimeError("Redis client is not initialised.")
    return _redis


RedisDep = Annotated[Redis, Depends(get_redis)]
