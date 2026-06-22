"""ML analysis and analytics routes."""

import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, get_db
from app.dependencies import get_current_user
from app.models.product import Product
from app.models.review import Review
from app.models.user import User
from app.schemas.analysis import AspectSummary, FakeAlertListResponse, SentimentTrendPoint
from app.services.analysis_service import (
    get_aspect_summary,
    get_fake_alerts,
    get_sentiment_trend,
    run_full_pipeline,
)

router = APIRouter(tags=["analysis"])


async def _assert_product_owned(
    product_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> Product:
    """Return product if it exists and belongs to ``current_user``."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None or product.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


async def _assert_review_owned(
    review_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> Review:
    """Return review if its product belongs to ``current_user``."""
    result = await db.execute(
        select(Review)
        .join(Product, Review.product_id == Product.id)
        .where(Review.id == review_id, Product.owner_id == current_user.id)
    )
    review = result.scalar_one_or_none()
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    return review


@router.get("/sentiment-trend", response_model=list[SentimentTrendPoint])
async def sentiment_trend(
    product_id: uuid.UUID = Query(...),
    start: datetime | None = Query(None),
    end: datetime | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Sentiment over time for a product (daily aggregates)."""
    await _assert_product_owned(product_id, current_user, db)
    return await get_sentiment_trend(product_id, current_user.id, start, end, db)


@router.get("/fake-alerts", response_model=FakeAlertListResponse)
async def fake_alerts(
    product_id: uuid.UUID | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Paginated list of reviews flagged as likely fake."""
    if product_id is not None:
        await _assert_product_owned(product_id, current_user, db)
    return await get_fake_alerts(current_user.id, product_id, page, limit, db)


@router.get("/aspect-summary/{product_id}", response_model=AspectSummary)
async def aspect_summary(
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Average aspect sentiment scores across completed reviews for a product."""
    await _assert_product_owned(product_id, current_user, db)
    return await get_aspect_summary(product_id, current_user.id, db)


@router.post("/rerun/{review_id}", status_code=status.HTTP_202_ACCEPTED)
async def rerun_analysis(
    review_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Force re-run all ML models on a review (async background job)."""
    await _assert_review_owned(review_id, current_user, db)

    async def task() -> None:
        async with AsyncSessionLocal() as session:
            await run_full_pipeline(str(review_id), session)

    background_tasks.add_task(task)
    return {"status": "queued", "review_id": str(review_id)}
