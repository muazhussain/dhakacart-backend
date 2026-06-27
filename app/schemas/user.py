"""Pydantic schemas for user auth requests and responses."""

import uuid

from pydantic import BaseModel, ConfigDict, EmailStr

from app.db.models.user import UserRole


class RegisterRequest(BaseModel):
    """Payload for user registration."""

    email: EmailStr
    password: str
    role: UserRole = UserRole.customer


class LoginRequest(BaseModel):
    """Payload for user login."""

    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Payload for token refresh."""

    refresh_token: str


class TokenResponse(BaseModel):
    """JWT token pair returned after successful auth."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Public user representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    role: UserRole
    is_active: bool


class UpdateMeRequest(BaseModel):
    """Payload for updating own profile."""

    email: EmailStr | None = None


class ChangePasswordRequest(BaseModel):
    """Payload for changing own password."""

    current_password: str
    new_password: str


class AdminUpdateUserRequest(BaseModel):
    """Payload for admin updating a user."""

    role: UserRole | None = None
    is_active: bool | None = None
