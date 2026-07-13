from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.environments import Environment


class Settings(BaseSettings):
    environment: Environment = Environment.DEVELOPMENT

    app_name: str = "Taxi Intelligence Platform"
    app_version: str = "0.1.0"

    host: str = "0.0.0.0"
    port: int = 8000

    database_url: str
    redis_url: str

    airport_api_key: str | None = None
    weather_api_key: str | None = None
    events_api_key: str | None = None

    airport_scheduler_enabled: bool = True
    airport_scheduler_interval_seconds: int = 300
    airport_scheduler_run_on_startup: bool = True

    airport_scheduler_max_attempts: int = 2
    airport_scheduler_retry_backoff_seconds: float = 2.0

    model_config = SettingsConfigDict(
        env_file="../.env",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
