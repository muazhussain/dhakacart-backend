"""User domain service — auth, profile, and admin operations."""

import uuid

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.db.models.user import User
from app.schemas.user import (
    AdminUpdateUserRequest,
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UpdateMeRequest,
)


class EmailTakenError(Exception):
    """Raised when email is already registered."""


class InvalidCredentialsError(Exception):
    """Raised when email/password combination is wrong."""


class UserNotFoundError(Exception):
    """Raised when a user ID does not exist."""


class WrongPasswordError(Exception):
    """Raised when current password verification fails."""


class TokenBlacklistedError(Exception):
    """Raised when a refresh token has been blacklisted."""


async def register(db: AsyncSession, payload: RegisterRequest) -> User:
    """Create a new user account.

    Args:
        db (AsyncSession): Database session.
        payload (RegisterRequest): Registration data.

    Returns:
        User: Newly created user.

    Raises:
        EmailTakenError: If email is already registered.
    """
    if await db.scalar(select(User).where(User.email == payload.email)):
        raise EmailTakenError(payload.email)
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise EmailTakenError(payload.email)
    return user


async def login(db: AsyncSession, payload: LoginRequest) -> TokenResponse:
    """Authenticate a user and return a token pair.

    Args:
        db (AsyncSession): Database session.
        payload (LoginRequest): Login credentials.

    Returns:
        TokenResponse: Access and refresh tokens.

    Raises:
        InvalidCredentialsError: If credentials are wrong.
    """
    user = await db.scalar(select(User).where(User.email == payload.email))
    if not user or not user.is_active or not verify_password(payload.password, user.hashed_password):
        raise InvalidCredentialsError
    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


async def refresh(redis: Redis, refresh_token: str) -> TokenResponse:
    """Issue a new token pair from a valid refresh token.

    Args:
        redis (Redis): Redis client.
        refresh_token (str): Existing refresh token.

    Returns:
        TokenResponse: New access and refresh tokens.

    Raises:
        TokenBlacklistedError: If token has been invalidated.
        jwt.PyJWTError: If token is invalid or expired.
    """
    if await redis.exists(f"blacklist:{refresh_token}"):
        raise TokenBlacklistedError
    subject = decode_refresh_token(refresh_token)
    ttl = settings.refresh_token_expire_days * 86400
    await redis.set(f"blacklist:{refresh_token}", "1", ex=ttl)
    return TokenResponse(
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject),
    )


async def logout(redis: Redis, refresh_token: str) -> None:
    """Blacklist a refresh token.

    Args:
        redis (Redis): Redis client.
        refresh_token (str): Token to invalidate.
    """
    ttl = settings.refresh_token_expire_days * 86400
    await redis.setex(f"blacklist:{refresh_token}", ttl, "1")


async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> User:
    """Fetch a user by primary key.

    Args:
        db (AsyncSession): Database session.
        user_id (uuid.UUID): User primary key.

    Returns:
        User: Found user.

    Raises:
        UserNotFoundError: If no user with that ID exists.
    """
    user = await db.get(User, user_id)
    if not user:
        raise UserNotFoundError(user_id)
    return user


async def update_me(
    db: AsyncSession, user_id: uuid.UUID, payload: UpdateMeRequest
) -> User:
    """Update the authenticated user's profile.

    Args:
        db (AsyncSession): Database session.
        user_id (uuid.UUID): Authenticated user ID.
        payload (UpdateMeRequest): Fields to update.

    Returns:
        User: Updated user.

    Raises:
        EmailTakenError: If the new email is already in use.
        UserNotFoundError: If user does not exist.
    """
    user = await get_by_id(db, user_id)
    if payload.email is not None:
        if await db.scalar(
            select(User).where(User.email == payload.email, User.id != user_id)
        ):
            raise EmailTakenError(payload.email)
        user.email = payload.email
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise EmailTakenError(payload.email)
    return user


async def change_password(
    db: AsyncSession, user_id: uuid.UUID, payload: ChangePasswordRequest
) -> None:
    """Change the authenticated user's password.

    Args:
        db (AsyncSession): Database session.
        user_id (uuid.UUID): Authenticated user ID.
        payload (ChangePasswordRequest): Current and new passwords.

    Raises:
        WrongPasswordError: If current password is incorrect.
        UserNotFoundError: If user does not exist.
    """
    user = await get_by_id(db, user_id)
    if not verify_password(payload.current_password, user.hashed_password):
        raise WrongPasswordError
    user.hashed_password = hash_password(payload.new_password)
    await db.commit()


async def deactivate_me(db: AsyncSession, user_id: uuid.UUID) -> None:
    """Soft-delete the authenticated user's account.

    Args:
        db (AsyncSession): Database session.
        user_id (uuid.UUID): Authenticated user ID.

    Raises:
        UserNotFoundError: If user does not exist.
    """
    user = await get_by_id(db, user_id)
    user.is_active = False
    await db.commit()


async def list_users(db: AsyncSession, skip: int = 0, limit: int = 20) -> list[User]:
    """Fetch a paginated list of all users.

    Args:
        db (AsyncSession): Database session.
        skip (int): Number of records to skip.
        limit (int): Maximum records to return.

    Returns:
        list[User]: List of users.
    """
    result = await db.scalars(select(User).offset(skip).limit(limit))
    return list(result.all())


async def admin_update_user(
    db: AsyncSession, user_id: uuid.UUID, payload: AdminUpdateUserRequest
) -> User:
    """Update a user's role or active status.

    Args:
        db (AsyncSession): Database session.
        user_id (uuid.UUID): Target user ID.
        payload (AdminUpdateUserRequest): Fields to update.

    Returns:
        User: Updated user.

    Raises:
        UserNotFoundError: If user does not exist.
    """
    user = await get_by_id(db, user_id)
    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    await db.commit()
    return user


async def admin_delete_user(db: AsyncSession, user_id: uuid.UUID) -> None:
    """Permanently delete a user.

    Args:
        db (AsyncSession): Database session.
        user_id (uuid.UUID): Target user ID.

    Raises:
        UserNotFoundError: If user does not exist.
    """
    user = await get_by_id(db, user_id)
    await db.delete(user)
    await db.commit()
