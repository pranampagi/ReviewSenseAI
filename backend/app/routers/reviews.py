"""Review routes — ingestion, listing, detail, and bulk job status."""

import math
import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.analysis import AnalysisResult
from app.models.product import Product
from app.models.review import Review
from app.models.user import User
from app.mongo_collections import get_ingest_log_by_job_id
from app.schemas.analysis import AnalysisResultRead
from app.schemas.review import (
    BulkUploadResponse,
    ReviewCreate,
    ReviewDetailRead,
    ReviewListResponse,
    ReviewRead,
)
from app.services.review_service import ingest_csv, ingest_single

router = APIRouter(tags=["reviews"])


async def _get_owned_review(
    review_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> Review:
    """Load a review that belongs to a product owned by ``current_user``."""
    result = await db.execute(
        select(Review)
        .join(Product, Review.product_id == Product.id)
        .where(Review.id == review_id, Product.owner_id == current_user.id)
    )
    review = result.scalar_one_or_none()
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    return review


def _reviews_for_owner_query(current_user: User):
    """Base query: reviews whose product is owned by the current user."""
    return (
        select(Review)
        .join(Product, Review.product_id == Product.id)
        .where(Product.owner_id == current_user.id)
    )


@router.get("/bulk-jobs/{job_id}")
async def get_bulk_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
) -> dict:
    """Return MongoDB ingest log for a CSV bulk-upload job (owner-only)."""
    doc = await get_ingest_log_by_job_id(job_id)
    if doc is None or doc.get("user_id") != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return doc


@router.get("", response_model=ReviewListResponse)
async def list_reviews(
    product_id: uuid.UUID | None = Query(None),
    sentiment: str | None = Query(None, pattern="^(POSITIVE|NEGATIVE)$"),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReviewListResponse:
    """List reviews with optional filters on product, sentiment, and date range."""
    base = _reviews_for_owner_query(current_user)
    count_stmt = (
        select(func.count())
        .select_from(Review)
        .join(Product, Review.product_id == Product.id)
        .where(Product.owner_id == current_user.id)
    )

    if product_id is not None:
        base = base.where(Review.product_id == product_id)
        count_stmt = count_stmt.where(Review.product_id == product_id)

    if start_date is not None:
        base = base.where(Review.created_at >= start_date)
        count_stmt = count_stmt.where(Review.created_at >= start_date)

    if end_date is not None:
        base = base.where(Review.created_at <= end_date)
        count_stmt = count_stmt.where(Review.created_at <= end_date)

    if sentiment is not None:
        base = base.join(AnalysisResult, Review.id == AnalysisResult.review_id).where(
            AnalysisResult.sentiment == sentiment
        )
        count_stmt = count_stmt.join(AnalysisResult, Review.id == AnalysisResult.review_id).where(
            AnalysisResult.sentiment == sentiment
        )

    total = (await db.execute(count_stmt)).scalar_one()
    offset = (page - 1) * limit
    result = await db.execute(
        base.order_by(Review.created_at.desc()).offset(offset).limit(limit)
    )
    items = result.scalars().all()
    pages = max(1, math.ceil(total / limit)) if total else 1

    return ReviewListResponse(
        items=[ReviewRead.model_validate(r) for r in items],
        total=total,
        page=page,
        pages=pages,
    )


@router.get("/{review_id}", response_model=ReviewDetailRead)
async def get_review(
    review_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReviewDetailRead:
    """Return one review with nested ``analysis_result`` when analysis exists."""
    review = await _get_owned_review(review_id, current_user, db)

    analysis_row = None
    if review.status == "complete":
        ar = await db.execute(
            select(AnalysisResult).where(AnalysisResult.review_id == review.id)
        )
        analysis_row = ar.scalar_one_or_none()

    return ReviewDetailRead(
        **ReviewRead.model_validate(review).model_dump(),
        analysis_result=AnalysisResultRead.model_validate(analysis_row) if analysis_row else None,
    )


@router.post("", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
async def create_review(
    body: ReviewCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReviewRead:
    """Submit one review for an owned product; triggers background ML pipeline."""
    review = await ingest_single(body, current_user, db, background_tasks)
    return review


@router.post("/bulk-upload", response_model=BulkUploadResponse)
async def bulk_upload(
    background_tasks: BackgroundTasks,
    product_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BulkUploadResponse:
    """Upload a CSV with columns ``author``, ``rating``, ``body`` (up to 10k rows)."""
    return await ingest_csv(file, product_id, current_user, db, background_tasks)
