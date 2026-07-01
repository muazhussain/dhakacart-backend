"""FastAPI application factory."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.redis import close_redis, get_redis, init_redis


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage startup and shutdown of shared resources."""
    await init_redis()
    yield
    await close_redis()


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan,
)


@app.get("/health", tags=["health"])
async def health() -> JSONResponse:
    """Liveness and readiness probe for Kubernetes.

    Returns:
        JSONResponse: 200 with status ok, or 503 if Redis is unreachable.
    """
    try:
        await get_redis().ping()
    except Exception:
        return JSONResponse(status_code=503, content={"status": "degraded"})
    return JSONResponse(status_code=200, content={"status": "ok"})
