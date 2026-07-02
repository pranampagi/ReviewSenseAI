"""ML analysis result schemas returned with review detail and analytics endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AnalysisResultRead(BaseModel):
    """ML pipeline output attached to a single review."""

    id: uuid.UUID
    review_id: uuid.UUID
    sentiment: str | None
    sentiment_score: float | None
    is_fake: bool | None
    fake_prob: float | None
    aspect_price: float | None
    aspect_quality: float | None
    aspect_shipping: float | None
    aspect_service: float | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class SentimentTrendPoint(BaseModel):
    """One day of aggregated sentiment for a product."""

    date: str
    avg_score: float
    positive_count: int
    negative_count: int


class FakeAlertItem(BaseModel):
    """One flagged review in the fake-alerts panel."""

    review_id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    body_excerpt: str
    fake_prob: float | None
    created_at: datetime


class FakeAlertListResponse(BaseModel):
    """Paginated fake review alerts."""

    items: list[FakeAlertItem]
    total: int
    page: int
    pages: int


class AspectSummary(BaseModel):
    """Average aspect sentiment scores for a product."""

    price: float
    quality: float
    shipping: float
    service: float


class AspectTextRequest(BaseModel):
    """Body for ``POST /analyze/aspects`` — run aspect model on arbitrary text."""

    text: str = Field(min_length=1, description="Review text to score")
