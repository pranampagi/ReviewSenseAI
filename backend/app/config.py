"""Application configuration loaded from environment variables.

Uses Pydantic Settings to read ``backend/.env`` (see ``.env.example``).
All modules should import ``settings`` from here instead of reading os.environ directly.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the ReviewSense API."""

    app_name: str = "ReviewSense AI"
    app_env: str = "development"
    secret_key: str
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    database_url: str
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "reviewsense"
    hf_model_id: str = "distilbert-base-uncased-finetuned-sst-2-english"
    ml_models_dir: str = "./ml/models"
    allowed_origins: str = "http://localhost:5173"

    @property
    def origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list for FastAPI middleware."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Singleton used across the app (import: ``from app.config import settings``).
settings = Settings()
