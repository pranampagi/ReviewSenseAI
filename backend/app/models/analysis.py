import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reviews.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    sentiment: Mapped[str | None] = mapped_column(String(20), nullable=True)
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_fake: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    fake_prob: Mapped[float | None] = mapped_column(Float, nullable=True)
    aspect_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    aspect_quality: Mapped[float | None] = mapped_column(Float, nullable=True)
    aspect_shipping: Mapped[float | None] = mapped_column(Float, nullable=True)
    aspect_service: Mapped[float | None] = mapped_column(Float, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
