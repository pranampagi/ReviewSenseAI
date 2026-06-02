"""Async MongoDB client (Motor) for unstructured review storage.

MongoDB holds raw review documents and bulk-ingest job logs.
Structured entities (users, products, reviews, analysis) live in SQL.

Requires a compatible Motor + PyMongo pair (see ``requirements.txt``).
"""

from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings

# Module-level singleton — one client per process is recommended by Motor.
_client: AsyncIOMotorClient | None = None


def get_mongo_client() -> AsyncIOMotorClient:
    """Return the shared Motor client, creating it on first use."""
    global _client
    if _client is None:
        # Short timeout so /health fails fast when Mongo is down.
        _client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=2000)
    return _client


def get_mongo_db():
    """Return the application database (name from ``MONGODB_DB_NAME``)."""
    return get_mongo_client()[settings.mongodb_db_name]


async def ping_mongo() -> bool:
    """Return True if the MongoDB server responds to a ping command."""
    try:
        await get_mongo_client().admin.command("ping")
        return True
    except Exception:
        return False
