"""Password hashing and JWT utilities."""

from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import settings

_ph = PasswordHasher()


def hash_password(password: str) -> str:
    """Hash a plaintext password.

    Args:
        password (str): Plaintext password.

    Returns:
        str: Argon2 hash.
    """
    return _ph.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a hash.

    Args:
        plain (str): Plaintext password.
        hashed (str): Argon2 hash.

    Returns:
        bool: True if match, False otherwise.
    """
    try:
        return _ph.verify(hashed, plain)
    except (VerificationError, InvalidHashError):
        return False


def create_access_token(subject: str) -> str:
    """Create a signed JWT access token.

    Args:
        subject (str): Token subject (user ID as string).

    Returns:
        str: Encoded JWT.
    """
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode(
        {"sub": subject, "exp": expire},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(subject: str) -> str:
    """Create a signed JWT refresh token.

    Args:
        subject (str): Token subject (User ID as string).

    Returns:
        str: Encoded JWT.
    """
    expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    return jwt.encode(
        {"sub": subject, "exp": expire, "type": "refresh"},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> str:
    """Decode and validate a JWT access token.

    Args:
        token (str): Encoded JWT.

    Returns:
        str: Subject claim (user ID).

    Raises:
        jwt.PyJWTError: If token is invalid, expired, or missing the sub claim.
    """
    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
    if payload.get("type") == "refresh":
        raise jwt.InvalidTokenError("Refresh token cannot be used as access token.")
    sub = payload.get("sub")
    if not isinstance(sub, str):
        raise jwt.InvalidTokenError("Token missing sub claim.")
    return sub


def decode_refresh_token(token: str) -> str:
    """Decode and validate a JWT refresh token.

    Args:
        token (str): Encoded JWT.

    Returns:
        str: Subject claim (user ID).

    Raises:
        jwt.PyJWTError: If token is invalid, expired, or not a refresh token.
    """
    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
    if payload.get("type") != "refresh":
        raise jwt.InvalidTokenError("Not a refresh token.")
    sub = payload.get("sub")
    if not isinstance(sub, str):
        raise jwt.InvalidTokenError("Token missing sub claim.")
    return sub
