"""Review ingestion routes — single submit and bulk CSV upload."""

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.review import BulkUploadResponse, ReviewCreate, ReviewRead
from app.services.review_service import ingest_csv, ingest_single

router = APIRouter(tags=["reviews"])


@router.post("", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
async def create_review(
    body: ReviewCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReviewRead:
    """Submit one review for a owned product; triggers background ML pipeline (stub until #12)."""
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
