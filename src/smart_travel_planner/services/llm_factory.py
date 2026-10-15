"""Secure CrewAI LLM construction for Ollama Cloud."""

from typing import Any

from crewai import LLM

from smart_travel_planner.config.settings import Settings, get_settings
from smart_travel_planner.utils.exceptions import LLMConfigurationError


class OllamaLLMFactory:
    """Construct CrewAI LLM instances for Ollama Cloud."""

    PROVIDER_PREFIX = "openai/"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def configuration_status(self) -> dict[str, object]:
        """Return configuration state without exposing secrets."""

        return self.settings.safe_llm_status()

    def normalized_model_name(self) -> str:
        """Return the CrewAI OpenAI-compatible model identifier."""

        configured_model = self.settings.ollama_model.strip()

        if not configured_model:
            raise LLMConfigurationError("OLLAMA_MODEL is required before creating the live LLM.")

        for prefix in ("openai/", "ollama/"):
            if configured_model.startswith(prefix):
                configured_model = configured_model[len(prefix) :]
                break

        return f"{self.PROVIDER_PREFIX}{configured_model}"

    def normalized_base_url(self) -> str:
        """Return the Ollama Cloud OpenAI-compatible API endpoint."""

        base_url = self.settings.ollama_base_url.strip().rstrip("/")

        if not base_url:
            raise LLMConfigurationError("OLLAMA_BASE_URL must not be empty.")

        if base_url.endswith("/v1"):
            return base_url

        return f"{base_url}/v1"

    def create(self) -> LLM:
        """Create the CrewAI LLM without sending a request."""

        try:
            return LLM(
                model=self.normalized_model_name(),
                base_url=self.normalized_base_url(),
                api_key=self._validated_api_key(),
                temperature=self.settings.llm_temperature,
                max_tokens=self.settings.llm_max_tokens,
            )
        except LLMConfigurationError:
            raise
        except (TypeError, ValueError) as exc:
            raise LLMConfigurationError(
                "CrewAI could not construct the configured Ollama LLM."
            ) from exc

    def _validated_api_key(self) -> str:
        """Return the validated secret without logging it."""

        secret = self.settings.ollama_api_key

        if secret is None:
            raise LLMConfigurationError("OLLAMA_API_KEY is required before creating the live LLM.")

        value = secret.get_secret_value().strip()

        if not value:
            raise LLMConfigurationError("OLLAMA_API_KEY is required before creating the live LLM.")

        return value


def ensure_llm(
    value: Any | None,
    settings: Settings | None = None,
) -> Any:
    """Return an injected LLM or create the configured live LLM."""

    if value is not None:
        return value

    return OllamaLLMFactory(settings=settings).create()
