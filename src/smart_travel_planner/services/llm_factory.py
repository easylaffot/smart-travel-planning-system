"""Secure CrewAI LLM construction for Ollama Cloud."""

from typing import Any

from crewai import LLM

from smart_travel_planner.config.settings import Settings, get_settings
from smart_travel_planner.utils.exceptions import LLMConfigurationError


class OllamaLLMFactory:
    """Construct CrewAI LLM instances from validated Ollama settings."""

    PROVIDER_PREFIX = "ollama/"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def configuration_status(self) -> dict[str, object]:
        """Return configuration state without exposing secret values."""

        return self.settings.safe_llm_status()

    def normalized_model_name(self) -> str:
        """Return the CrewAI provider-prefixed Ollama model identifier."""

        configured_model = self.settings.ollama_model.strip()

        if not configured_model:
            raise LLMConfigurationError("OLLAMA_MODEL is required before creating the live LLM.")

        if configured_model.startswith(self.PROVIDER_PREFIX):
            return configured_model

        return f"{self.PROVIDER_PREFIX}{configured_model}"

    def create(self) -> LLM:
        """Create a configured CrewAI LLM without sending a network request."""

        api_key = self._validated_api_key()
        model_name = self.normalized_model_name()
        base_url = self.settings.ollama_base_url.strip()

        if not base_url:
            raise LLMConfigurationError("OLLAMA_BASE_URL must not be empty.")

        try:
            return LLM(
                model=model_name,
                base_url=base_url,
                api_key=api_key,
                temperature=self.settings.llm_temperature,
                max_tokens=self.settings.llm_max_tokens,
            )
        except (TypeError, ValueError) as exc:
            raise LLMConfigurationError(
                "CrewAI could not construct the configured Ollama LLM."
            ) from exc

    def _validated_api_key(self) -> str:
        """Return the secret key after validation without logging it."""

        secret = self.settings.ollama_api_key

        if secret is None:
            raise LLMConfigurationError("OLLAMA_API_KEY is required before creating the live LLM.")

        value = secret.get_secret_value().strip()

        if not value:
            raise LLMConfigurationError("OLLAMA_API_KEY is required before creating the live LLM.")

        return value


def ensure_llm(value: Any | None, settings: Settings | None = None) -> Any:
    """Return an injected LLM or create the configured Ollama LLM."""

    if value is not None:
        return value

    return OllamaLLMFactory(settings=settings).create()
