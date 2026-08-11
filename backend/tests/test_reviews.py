"""Product and review ingestion / listing tests."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import AnalysisResult
from app.models.review import Review


@pytest.mark.asyncio
async def test_create_and_list_product(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    created = await client.post(
        "/products",
        headers=auth_headers,
        json={"name": "Coffee Mug", "category": "Kitchen", "description": "Ceramic"},
    )
    assert created.status_code == 201
    product = created.json()
    assert product["name"] == "Coffee Mug"

    listed = await client.get("/products", headers=auth_headers)
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1
    assert any(item["id"] == product["id"] for item in listed.json()["items"])


@pytest.mark.asyncio
async def test_create_review(
    client: AsyncClient,
    auth_headers: dict[str, str],
    product_id: str,
) -> None:
    response = await client.post(
        "/reviews",
        headers=auth_headers,
        json={
            "product_id": product_id,
            "author": "Alice",
            "rating": 5,
            "body": "Absolutely love this product, shipping was fast and quality is great!",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["rating"] == 5
    assert body["status"] == "pending"
    assert body["product_id"] == product_id


@pytest.mark.asyncio
async def test_create_review_unknown_product(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    response = await client.post(
        "/reviews",
        headers=auth_headers,
        json={
            "product_id": "00000000-0000-0000-0000-000000000099",
            "author": "Bob",
            "rating": 3,
            "body": "This product does not belong to me so create should fail.",
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_reviews_filter_by_product(
    client: AsyncClient,
    auth_headers: dict[str, str],
    product_id: str,
) -> None:
    await client.post(
        "/reviews",
        headers=auth_headers,
        json={
            "product_id": product_id,
            "author": "Carol",
            "rating": 4,
            "body": "Solid purchase overall, would recommend to friends and family.",
        },
    )
    response = await client.get(
        "/reviews",
        headers=auth_headers,
        params={"product_id": product_id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert all(item["product_id"] == product_id for item in data["items"])


@pytest.mark.asyncio
async def test_review_detail_with_analysis(
    client: AsyncClient,
    auth_headers: dict[str, str],
    product_id: str,
    db_session: AsyncSession,
) -> None:
    created = await client.post(
        "/reviews",
        headers=auth_headers,
        json={
            "product_id": product_id,
            "author": "Dana",
            "rating": 2,
            "body": "Quality was disappointing and customer service never replied to me.",
        },
    )
    assert created.status_code == 201
    review_id = created.json()["id"]

    result = await db_session.execute(
        select(Review).where(Review.id == uuid.UUID(review_id))
    )
    review = result.scalar_one()
    review.status = "complete"
    db_session.add(
        AnalysisResult(
            review_id=review.id,
            sentiment="NEGATIVE",
            sentiment_score=0.18,
            is_fake=False,
            fake_prob=0.12,
            aspect_price=0.4,
            aspect_quality=0.2,
            aspect_shipping=0.5,
            aspect_service=0.15,
        )
    )
    await db_session.commit()

    detail = await client.get(f"/reviews/{review_id}", headers=auth_headers)
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["status"] == "complete"
    assert payload["analysis_result"] is not None
    assert payload["analysis_result"]["sentiment"] == "NEGATIVE"
    assert payload["analysis_result"]["is_fake"] is False
    assert payload["analysis_result"]["aspect_quality"] == pytest.approx(0.2)


@pytest.mark.asyncio
async def test_reviews_require_auth(client: AsyncClient) -> None:
    response = await client.get("/reviews")
    assert response.status_code == 401
