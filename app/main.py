"""FastAPI application factory."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.core.limiter import limiter
from app.db.mongo import close_mongo, init_mongo
from app.db.redis import close_redis, get_redis, init_redis


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Manage startup and shutdown of shared resources."""
    await init_redis()
    await init_mongo()
    yield
    await close_redis()
    await close_mongo()


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
app.add_middleware(SlowAPIMiddleware)


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
