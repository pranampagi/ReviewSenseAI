"""ML analysis result schemas returned with review detail."""

import uuid
from datetime import datetime

from pydantic import BaseModel


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
