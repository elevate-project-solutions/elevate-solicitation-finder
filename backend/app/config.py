from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Loads configuration from env variables and .env file
class Settings(BaseSettings):
    app_name: str = "Elevate Solicitation Finder"
    app_env: str = "development"
    debug: bool = False

    # Deadline filter defaults to 30 days and cannot be negative
    min_days_until_deadline: int = Field(default=30, ge=0)

    # Optional because not in use yet
    openai_ai_key: str | None = None
    database_url: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Prevents unrelated entries from breaking startup
        extra="ignore",
    )


# Prevents program from repeatedly loading configuration every time
@lru_cache
def get_settings() -> Settings:
    return Settings()
