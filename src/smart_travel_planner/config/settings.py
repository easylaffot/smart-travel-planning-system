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
    log_level: Literal[
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ] = "INFO"

    # Ollama Cloud
    ollama_api_key: SecretStr | None = None
    ollama_base_url: str = "https://ollama.com"
    ollama_model: str = ""

    # LLM and CrewAI execution
    llm_temperature: float = Field(default=0.2, ge=0.0, le=1.0)
    llm_max_tokens: int = Field(default=4096, ge=256, le=32768)
    crew_verbose: bool = False
    crew_max_rpm: int | None = Field(default=None, ge=1, le=1000)
    agent_max_iterations: int = Field(default=5, ge=1, le=20)
    agent_max_execution_seconds: int = Field(
        default=180,
        ge=30,
        le=1800,
    )
    crew_cache_enabled: bool = True

    # External providers
    search_api_key: SecretStr | None = None
    search_api_url: str = "https://example.com/search"
    weather_api_key: SecretStr | None = None
    routing_api_key: SecretStr | None = None
    hotel_api_key: SecretStr | None = None
    transport_api_key: SecretStr | None = None

    # Prototype and workflow controls
    use_mock_hotels: bool = True
    use_mock_transport: bool = True
    max_trip_days: int = Field(default=30, ge=1, le=90)
    max_revision_rounds: int = Field(default=2, ge=0, le=5)
    request_timeout_seconds: int = Field(default=20, ge=5, le=120)

    def ollama_is_configured(self) -> bool:
        """Return whether the required Ollama settings are available."""

        return bool(
            self.ollama_api_key
            and self.ollama_api_key.get_secret_value().strip()
            and self.ollama_model.strip()
        )

    def safe_llm_status(self) -> dict[str, object]:
        """Return LLM configuration status without exposing secrets."""

        return {
            "provider": "ollama",
            "base_url": self.ollama_base_url,
            "model_configured": bool(self.ollama_model.strip()),
            "api_key_configured": bool(
                self.ollama_api_key and self.ollama_api_key.get_secret_value().strip()
            ),
            "temperature": self.llm_temperature,
            "max_tokens": self.llm_max_tokens,
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return one validated Settings object per process."""

    return Settings()
