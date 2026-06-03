"""Password hashing and JWT creation/validation."""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
import bcrypt

from app.config import settings

ALGORITHM = "HS256"


def hash_password(plain: str) -> str:
    """Return a bcrypt hash suitable for storing in ``users.hashed_pw``."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    """Compare a login password with the stored hash."""
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))


def create_access_token(subject: str) -> str:
    """Create a short-lived access JWT. ``subject`` is typically the user UUID string."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({"sub": subject, "exp": expire}, settings.secret_key, algorithm=ALGORITHM)


def create_refresh_token(subject: str) -> str:
    """Create a long-lived refresh JWT (includes ``type: refresh`` claim)."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    payload = {"sub": subject, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT; raises ``JWTError`` if invalid or expired."""
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
