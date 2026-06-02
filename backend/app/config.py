from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
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
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
