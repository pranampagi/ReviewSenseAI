"""Helpers for MongoDB collections used during review ingestion.

These are called from the review service (Commit #7+) when saving raw text
and logging CSV bulk-upload jobs. SQL remains the source of truth for review IDs.
"""

from app.mongo import get_mongo_db


async def insert_raw_review(doc: dict) -> str:
    """Insert a document into ``raw_reviews`` and return its ``_id`` as a string.

    Expected keys (see ReviewSenseAI.md): review_id, product_id, raw_text, metadata, ingested_at.
    """
    result = await get_mongo_db()["raw_reviews"].insert_one(doc)
    return str(result.inserted_id)


async def insert_ingest_log(doc: dict) -> str:
    """Insert a bulk-upload job record into ``ingest_logs`` and return ``_id`` as a string.

    Expected keys: job_id, user_id, filename, total_rows, success_count, error_count, etc.
    """
    result = await get_mongo_db()["ingest_logs"].insert_one(doc)
    return str(result.inserted_id)
