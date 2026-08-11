"""Auth endpoint tests — register, login, refresh, and /me."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_returns_tokens(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "password123",
            "full_name": "New User",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]


@pytest.mark.asyncio
async def test_register_duplicate_email_conflict(client: AsyncClient) -> None:
    payload = {
        "email": "dup@example.com",
        "password": "password123",
        "full_name": "Dup",
    }
    first = await client.post("/auth/register", json=payload)
    assert first.status_code == 201
    second = await client.post("/auth/register", json=payload)
    assert second.status_code == 409
    assert "already registered" in second.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    await client.post(
        "/auth/register",
        json={"email": "login@example.com", "password": "password123"},
    )
    response = await client.post(
        "/auth/login",
        data={"username": "login@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    assert response.json()["access_token"]


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient) -> None:
    await client.post(
        "/auth/register",
        json={"email": "badpw@example.com", "password": "password123"},
    )
    response = await client.post(
        "/auth/login",
        data={"username": "badpw@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_token(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    response = await client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "tester@example.com"
    assert body["full_name"] == "Test User"
    assert "id" in body


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient) -> None:
    register = await client.post(
        "/auth/register",
        json={"email": "refresh@example.com", "password": "password123"},
    )
    refresh = register.json()["refresh_token"]
    response = await client.post(
        "/auth/refresh",
        headers={"Authorization": f"Bearer {refresh}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["mongo"] == "connected"
