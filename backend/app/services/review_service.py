"""Review ingestion — single submit and bulk CSV upload."""

import io
import uuid
from datetime import datetime, timezone

import pandas as pd
from fastapi import BackgroundTasks, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.product import Product
from app.models.review import Review
from app.models.user import User
from app.mongo_collections import insert_ingest_log, insert_raw_review
from app.schemas.review import BulkUploadError, BulkUploadResponse, ReviewCreate
from app.services.analysis_service import run_full_pipeline

BATCH_SIZE = 500


async def _assert_product_owned(
    product_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> None:
    """Ensure the product exists and belongs to the current user."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None or product.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")


def _compute_metadata(text: str, upload_source: str, **extra) -> dict:
    """Derive char/word stats stored alongside raw text in MongoDB."""
    words = text.split()
    return {
        "char_count": len(text),
        "word_count": len(words),
        "caps_ratio": round(sum(c.isupper() for c in text) / max(len(text), 1), 4),
        "exclamation_count": text.count("!"),
        "upload_source": upload_source,
        **extra,
    }


async def _enqueue_analysis(review_id: uuid.UUID, background_tasks: BackgroundTasks) -> None:
    """Schedule ML pipeline in a fresh DB session after the HTTP response."""

    async def task() -> None:
        async with AsyncSessionLocal() as session:
            await run_full_pipeline(str(review_id), session)

    background_tasks.add_task(task)


async def _save_raw_review_doc(
    review: Review,
    metadata: dict,
) -> None:
    """Persist unstructured copy in MongoDB ``raw_reviews``."""
    await insert_raw_review(
        {
            "review_id": str(review.id),
            "product_id": str(review.product_id),
            "raw_text": review.body,
            "metadata": metadata,
            "ingested_at": datetime.now(timezone.utc),
        }
    )


async def ingest_single(
    data: ReviewCreate,
    current_user: User,
    db: AsyncSession,
    background_tasks: BackgroundTasks,
) -> Review:
    """Insert one review into SQL + MongoDB and queue ML analysis."""
    await _assert_product_owned(data.product_id, current_user, db)

    review = Review(
        product_id=data.product_id,
        author=data.author,
        rating=data.rating,
        body=data.body,
        source="manual",
        status="pending",
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)

    metadata = _compute_metadata(review.body, upload_source="manual")
    await _save_raw_review_doc(review, metadata)
    await _enqueue_analysis(review.id, background_tasks)
    return review


async def ingest_csv(
    file: UploadFile,
    product_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
    background_tasks: BackgroundTasks,
) -> BulkUploadResponse:
    """Parse a CSV (columns: author, rating, body), bulk-insert valid rows, log job in MongoDB."""
    await _assert_product_owned(product_id, current_user, db)

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a .csv")

    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid CSV: {exc}",
        ) from exc

    required = {"author", "rating", "body"}
    missing = required - set(df.columns.str.lower())
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required columns: {', '.join(sorted(missing))}",
        )

    # Normalise column names to lowercase for lookup.
    df.columns = [c.lower() for c in df.columns]

    job_id = str(uuid.uuid4())
    errors: list[BulkUploadError] = []
    valid_rows: list[dict] = []

    for idx, row in df.iterrows():
        row_num = int(idx) + 2  # 1-based + header row
        body = row.get("body")
        rating = row.get("rating")

        if pd.isna(body) or str(body).strip() == "":
            errors.append(BulkUploadError(row=row_num, reason="missing body"))
            continue

        try:
            rating_int = int(rating)
        except (TypeError, ValueError):
            errors.append(BulkUploadError(row=row_num, reason="invalid rating"))
            continue

        if rating_int < 1 or rating_int > 5:
            errors.append(BulkUploadError(row=row_num, reason="rating out of range (1-5)"))
            continue

        author = None if pd.isna(row.get("author")) else str(row["author"]).strip() or None
        valid_rows.append(
            {
                "author": author,
                "rating": rating_int,
                "body": str(body).strip(),
                "row_number": row_num,
            }
        )

    accepted_reviews: list[Review] = []
    started_at = datetime.now(timezone.utc)

    for batch_start in range(0, len(valid_rows), BATCH_SIZE):
        batch = valid_rows[batch_start : batch_start + BATCH_SIZE]
        reviews = [
            Review(
                product_id=product_id,
                author=row["author"],
                rating=row["rating"],
                body=row["body"],
                source="csv",
                status="pending",
            )
            for row in batch
        ]
        db.add_all(reviews)
        await db.commit()
        for review, row in zip(reviews, batch, strict=True):
            await db.refresh(review)
            metadata = _compute_metadata(
                review.body,
                upload_source="csv",
                filename=file.filename,
                row_number=row["row_number"],
            )
            await _save_raw_review_doc(review, metadata)
            await _enqueue_analysis(review.id, background_tasks)
            accepted_reviews.append(review)

    completed_at = datetime.now(timezone.utc)
    await insert_ingest_log(
        {
            "job_id": job_id,
            "user_id": str(current_user.id),
            "filename": file.filename,
            "total_rows": len(df),
            "success_count": len(accepted_reviews),
            "error_count": len(errors),
            "errors": [e.model_dump() for e in errors],
            "started_at": started_at,
            "completed_at": completed_at,
            "status": "completed",
        }
    )

    return BulkUploadResponse(
        job_id=job_id,
        accepted=len(accepted_reviews),
        errors=errors,
    )
