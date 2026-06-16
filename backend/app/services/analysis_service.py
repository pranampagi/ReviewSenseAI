"""ML analysis orchestration (sentiment, fake detection, aspects).

``run_full_pipeline`` is invoked as a background task after review ingestion.
Full implementation will be added later; this stub keeps reviews in ``pending``.
"""

from sqlalchemy.ext.asyncio import AsyncSession


async def run_full_pipeline(review_id: str, db: AsyncSession) -> None:
    """Run all ML models for a review and persist ``analysis_results``.

    Stub until full implementation wires sentiment, fake detector, and aspect models.
    """
    _ = review_id, db
