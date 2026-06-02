"""Async SQLAlchemy engine, session factory, and FastAPI DB dependency.

Development uses SQLite via aiosqlite; production can switch to PostgreSQL
by changing ``DATABASE_URL`` in ``.env`` with no code changes.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# Echo SQL in development only — useful when debugging queries.
engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Declarative base for all SQLAlchemy ORM models in ``app.models``."""

    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield one async session per request; closes automatically after the handler."""
    async with AsyncSessionLocal() as session:
        yield session
