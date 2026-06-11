"""FastAPI application entry point.

Registers CORS, health check, SQL tables on startup, and API routers (auth, …).
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.models import AnalysisResult, Product, Review, User  # noqa: F401 — register models
from app.mongo import ping_mongo
from app.routers import auth, products


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create SQL tables on startup (SQLite dev convenience). Use Alembic for production."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


def create_app() -> FastAPI:
    """Build and configure the FastAPI application instance."""
    app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix="/auth")
    app.include_router(products.router, prefix="/products")

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        """Liveness check: API status, environment name, and MongoDB connectivity."""
        mongo_ok = await ping_mongo()
        return {
            "status": "ok",
            "env": settings.app_env,
            "mongo": "connected" if mongo_ok else "error",
        }

    return app


app = create_app()
