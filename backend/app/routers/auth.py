"""Authentication routes — register, login, refresh, and current user profile."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserRead
from app.services.auth_service import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

router = APIRouter(tags=["auth"])
refresh_bearer = HTTPBearer()


def _tokens_for_user(user: User) -> TokenResponse:
    """Build access + refresh token pair for a user."""
    subject = str(user.id)
    return TokenResponse(
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject),
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Create a new account and return JWT tokens."""
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=body.email,
        hashed_pw=hash_password(body.password),
        full_name=body.full_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _tokens_for_user(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """Authenticate with email/password and return JWT tokens."""
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(form_data.password, user.hashed_pw):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account inactive")
    return _tokens_for_user(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    credentials: HTTPAuthorizationCredentials = Depends(refresh_bearer),
) -> TokenResponse:
    """Exchange a valid refresh token (Bearer) for a new access + refresh pair."""
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        uuid.UUID(user_id)  # validate format
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from None

    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
    )


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)) -> User:
    """Return the profile for the authenticated user."""
    return current_user
