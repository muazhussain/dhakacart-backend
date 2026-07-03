"""Auth endpoints — register, login, token refresh, logout."""

import jwt
from fastapi import APIRouter, HTTPException, Request, status

from app.core.dependencies import DbDep
from app.core.limiter import limiter
from app.db.redis import RedisDep
from app.schemas.user import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services import user_service
from app.services.user_service import (
    EmailTakenError,
    InvalidCredentialsError,
    TokenBlacklistedError,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
@limiter.limit("5/minute")
async def register(
    request: Request, payload: RegisterRequest, db: DbDep
) -> UserResponse:
    try:
        user = await user_service.register(db, payload)
    except EmailTakenError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Email already registered."
        ) from None
    return UserResponse.model_validate(user)


@router.post("/token", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, payload: LoginRequest, db: DbDep) -> TokenResponse:
    try:
        return await user_service.login(db, payload)
    except InvalidCredentialsError:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Invalid credentials."
        ) from None


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("20/minute")
async def refresh(
    request: Request, payload: RefreshRequest, redis: RedisDep
) -> TokenResponse:
    try:
        return await user_service.refresh(redis, payload.refresh_token)
    except TokenBlacklistedError:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Token has been revoked."
        ) from None
    except jwt.PyJWTError:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token."
        ) from None


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: RefreshRequest, redis: RedisDep) -> None:
    await user_service.logout(redis, payload.refresh_token)
