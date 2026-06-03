"""Authentication API schemas — register, login, tokens, and user profile."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Body for ``POST /auth/register``."""

    email: EmailStr
    password: str = Field(min_length=8, description="Plain-text password; hashed before storage")
    full_name: str | None = None


class LoginRequest(BaseModel):
    """Body for ``POST /auth/login`` (also used as OAuth2 form fields in OpenAPI)."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT pair returned after successful register or login."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    """Public user profile — never includes password hash."""

    id: uuid.UUID
    email: EmailStr
    full_name: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
