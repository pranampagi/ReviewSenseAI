"""Review ingestion API schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    """Body for ``POST /reviews`` (single review submission)."""

    product_id: uuid.UUID
    author: str | None = Field(default=None, max_length=255)
    rating: int = Field(ge=1, le=5)
    body: str = Field(min_length=1)


class ReviewRead(BaseModel):
    """Review row returned after create or list operations."""

    id: uuid.UUID
    product_id: uuid.UUID
    author: str | None
    rating: int
    body: str
    source: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class BulkUploadError(BaseModel):
    """One rejected CSV row."""

    row: int
    reason: str


class BulkUploadResponse(BaseModel):
    """Result of ``POST /reviews/bulk-upload``."""

    job_id: str
    accepted: int
    errors: list[BulkUploadError]
