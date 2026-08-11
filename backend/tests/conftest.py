"""Shared fixtures for API and ML tests.

Uses an in-memory SQLite database and stubs MongoDB / background ML enqueue
so tests do not require DistilBERT download or a live Mongo instance.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.routers import analysis, auth, products, reviews


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest_asyncio.fixture
async def test_engine():
    """Single shared in-memory SQLite engine (StaticPool keeps one connection)."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(test_engine, monkeypatch) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client against a FastAPI app wired to the test database."""
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)

    # Avoid MongoDB and background ML during API tests.
    monkeypatch.setattr(
        "app.services.review_service.insert_raw_review",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        "app.services.review_service.insert_ingest_log",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        "app.services.review_service._enqueue_analysis",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        "app.mongo.ping_mongo",
        AsyncMock(return_value=True),
    )

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        yield

    application = FastAPI(title="ReviewSense AI Test", lifespan=lifespan)
    application.include_router(auth.router, prefix="/auth")
    application.include_router(products.router, prefix="/products")
    application.include_router(reviews.router, prefix="/reviews")
    application.include_router(analysis.router, prefix="/analyze")

    @application.get("/health")
    async def health() -> dict[str, str]:
        from app.mongo import ping_mongo

        mongo_ok = await ping_mongo()
        return {"status": "ok", "env": "test", "mongo": "connected" if mongo_ok else "error"}

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    application.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    """Register a fresh user and return Bearer authorization headers."""
    response = await client.post(
        "/auth/register",
        json={
            "email": "tester@example.com",
            "password": "password123",
            "full_name": "Test User",
        },
    )
    assert response.status_code == 201, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def product_id(client: AsyncClient, auth_headers: dict[str, str]) -> str:
    """Create one owned product and return its id."""
    response = await client.post(
        "/products",
        headers=auth_headers,
        json={
            "name": "Test Widget",
            "category": "Gadgets",
            "description": "A product for tests",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]
