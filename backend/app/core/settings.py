from functools import lru_cache
from app.core.environments import Environment
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    model_config = SettingsConfigDict(
        env_file="../.env",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
