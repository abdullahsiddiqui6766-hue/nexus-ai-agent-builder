from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    groq_api_key: SecretStr = Field(
        default=SecretStr(""),
        validation_alias="GROQ_API_KEY",
    )

    tavily_api_key: SecretStr = Field(
        default=SecretStr(""),
        validation_alias="TAVILY_API_KEY",
    )

    search_provider: str = Field(
        default="duckduckgo",
        validation_alias="SEARCH_PROVIDER",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()