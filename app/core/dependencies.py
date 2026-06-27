"""FastAPI dependencies for DB sessions and authenticated users."""

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

DbDep = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> str:
    """Extract and validate the current user from a JWT bearer token.

    Args:
        token (str): Bearer token from Authorization header.

    Returns:
        str: User ID from token subject claim.

    Raises:
        HTTPException: 401 if token is missing, invalid, or expired.
    """
    try:
        return decode_access_token(token)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None


CurrentUserDep = Annotated[str, Depends(get_current_user)]
