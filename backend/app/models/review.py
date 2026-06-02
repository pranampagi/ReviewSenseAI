"""Customer review model — ingested manually or via CSV bulk upload."""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class Review(Base):
    """Product review awaiting or completed ML analysis.

    ``status`` flow: pending → processing → complete | failed
    ``source``: manual | csv
    """

    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="manual", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_reviews_rating_range"),
    )
