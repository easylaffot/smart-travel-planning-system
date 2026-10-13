"""Validated application settings loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration with safe defaults and secret handling."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Smart Travel Planning System"
    app_env: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    ollama_api_key: SecretStr | None = None
    ollama_base_url: str = "https://ollama.com"
    ollama_model: str = ""

    search_api_key: SecretStr | None = None
    weather_api_key: SecretStr | None = None
    routing_api_key: SecretStr | None = None
    hotel_api_key: SecretStr | None = None
    transport_api_key: SecretStr | None = None

    use_mock_hotels: bool = True
    use_mock_transport: bool = True
    max_trip_days: int = Field(default=30, ge=1, le=90)
    max_revision_rounds: int = Field(default=2, ge=0, le=5)
    request_timeout_seconds: int = Field(default=20, ge=5, le=120)

    def ollama_is_configured(self) -> bool:
        """Return True when both the cloud key and model are configured."""
        return bool(self.ollama_api_key and self.ollama_model.strip())


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return one validated Settings object per process."""
    return Settings()
