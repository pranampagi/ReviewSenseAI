"""ML analysis orchestration — sentiment, fake detection, aspects, and analytics queries."""

import asyncio
import math
import uuid
from datetime import datetime, timezone

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import AnalysisResult
from app.models.product import Product
from app.models.review import Review
from ml.aspect.infer import predict_aspects
from ml.fake_detector import predict as fake_predict
from ml.sentiment import analyse as sentiment_analyse


async def run_full_pipeline(review_id: str, db: AsyncSession) -> None:
    """Run all ML models for a review and persist ``analysis_results``.

    Called as a FastAPI background task after review ingestion or rerun.
    """
    try:
        uid = uuid.UUID(review_id)
        result = await db.execute(select(Review).where(Review.id == uid))
        review = result.scalar_one_or_none()
        if review is None:
            return

        review.status = "processing"
        await db.commit()

        sentiment_result = await asyncio.to_thread(sentiment_analyse, review.body)
        fake_result = await asyncio.to_thread(
            fake_predict,
            review.body,
            review.rating,
            sentiment_result["sentiment_score"],
        )
        aspect_result = await asyncio.to_thread(predict_aspects, review.body)

        ar_result = await db.execute(
            select(AnalysisResult).where(AnalysisResult.review_id == review.id)
        )
        analysis = ar_result.scalar_one_or_none()
        if analysis is None:
            analysis = AnalysisResult(review_id=review.id)
            db.add(analysis)

        analysis.sentiment = sentiment_result["sentiment"]
        analysis.sentiment_score = sentiment_result["sentiment_score"]
        analysis.is_fake = fake_result["is_fake"]
        analysis.fake_prob = fake_result["fake_prob"]
        analysis.aspect_price = aspect_result["price"]
        analysis.aspect_quality = aspect_result["quality"]
        analysis.aspect_shipping = aspect_result["shipping"]
        analysis.aspect_service = aspect_result["service"]
        analysis.completed_at = datetime.now(timezone.utc)

        review.status = "complete"
        await db.commit()
    except Exception:
        await db.rollback()
        try:
            uid = uuid.UUID(review_id)
            result = await db.execute(select(Review).where(Review.id == uid))
            review = result.scalar_one_or_none()
            if review is not None:
                review.status = "failed"
                await db.commit()
        except Exception:
            await db.rollback()


async def get_sentiment_trend(
    product_id: uuid.UUID,
    owner_id: uuid.UUID,
    start: datetime | None,
    end: datetime | None,
    db: AsyncSession,
) -> list[dict]:
    """Daily average sentiment score and label counts for a product."""
    stmt = (
        select(
            func.date(Review.created_at).label("day"),
            func.avg(AnalysisResult.sentiment_score).label("avg_score"),
            func.sum(case((AnalysisResult.sentiment == "POSITIVE", 1), else_=0)).label(
                "positive_count"
            ),
            func.sum(case((AnalysisResult.sentiment == "NEGATIVE", 1), else_=0)).label(
                "negative_count"
            ),
        )
        .join(Review, AnalysisResult.review_id == Review.id)
        .join(Product, Review.product_id == Product.id)
        .where(
            Product.owner_id == owner_id,
            Review.product_id == product_id,
            Review.status == "complete",
        )
        .group_by(func.date(Review.created_at))
        .order_by(func.date(Review.created_at))
    )

    if start is not None:
        stmt = stmt.where(Review.created_at >= start)
    if end is not None:
        stmt = stmt.where(Review.created_at <= end)

    rows = (await db.execute(stmt)).all()
    return [
        {
            "date": str(row.day),
            "avg_score": round(float(row.avg_score or 0), 4),
            "positive_count": int(row.positive_count or 0),
            "negative_count": int(row.negative_count or 0),
        }
        for row in rows
    ]


async def get_fake_alerts(
    owner_id: uuid.UUID,
    product_id: uuid.UUID | None,
    page: int,
    limit: int,
    db: AsyncSession,
) -> dict:
    """Paginated flagged reviews (``is_fake=True``) for the owner's products."""
    base = (
        select(Review, AnalysisResult, Product)
        .join(AnalysisResult, Review.id == AnalysisResult.review_id)
        .join(Product, Review.product_id == Product.id)
        .where(Product.owner_id == owner_id, AnalysisResult.is_fake.is_(True))
    )
    count_stmt = (
        select(func.count())
        .select_from(Review)
        .join(AnalysisResult, Review.id == AnalysisResult.review_id)
        .join(Product, Review.product_id == Product.id)
        .where(Product.owner_id == owner_id, AnalysisResult.is_fake.is_(True))
    )

    if product_id is not None:
        base = base.where(Review.product_id == product_id)
        count_stmt = count_stmt.where(Review.product_id == product_id)

    total = (await db.execute(count_stmt)).scalar_one()
    offset = (page - 1) * limit
    rows = (await db.execute(base.order_by(Review.created_at.desc()).offset(offset).limit(limit))).all()

    items = [
        {
            "review_id": review.id,
            "product_id": review.product_id,
            "product_name": product.name,
            "body_excerpt": review.body[:120] + ("…" if len(review.body) > 120 else ""),
            "fake_prob": analysis.fake_prob,
            "created_at": review.created_at,
        }
        for review, analysis, product in rows
    ]
    pages = max(1, math.ceil(total / limit)) if total else 1

    return {"items": items, "total": total, "page": page, "pages": pages}


async def get_aspect_summary(
    product_id: uuid.UUID,
    owner_id: uuid.UUID,
    db: AsyncSession,
) -> dict:
    """Average aspect scores across all completed reviews for a product."""
    stmt = (
        select(
            func.avg(AnalysisResult.aspect_price).label("price"),
            func.avg(AnalysisResult.aspect_quality).label("quality"),
            func.avg(AnalysisResult.aspect_shipping).label("shipping"),
            func.avg(AnalysisResult.aspect_service).label("service"),
        )
        .join(Review, AnalysisResult.review_id == Review.id)
        .join(Product, Review.product_id == Product.id)
        .where(
            Product.owner_id == owner_id,
            Review.product_id == product_id,
            Review.status == "complete",
        )
    )
    row = (await db.execute(stmt)).one()
    return {
        "price": round(float(row.price or 0.5), 4),
        "quality": round(float(row.quality or 0.5), 4),
        "shipping": round(float(row.shipping or 0.5), 4),
        "service": round(float(row.service or 0.5), 4),
    }
