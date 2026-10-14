"""Offline tests for the Ollama CrewAI LLM factory."""

import pytest
from pydantic import SecretStr

from smart_travel_planner.config.settings import Settings
from smart_travel_planner.services import OllamaLLMFactory
from smart_travel_planner.utils.exceptions import LLMConfigurationError


def make_settings(
    *,
    api_key: str | None = "test-key",
    model: str = "gemma-test",
) -> Settings:
    """Create isolated settings without reading the local .env file."""

    return Settings(
        _env_file=None,
        app_env="test",
        ollama_api_key=(SecretStr(api_key) if api_key is not None else None),
        ollama_model=model,
        ollama_base_url="https://ollama.com",
    )


def test_missing_ollama_key_is_rejected() -> None:
    factory = OllamaLLMFactory(
        settings=make_settings(api_key=None),
    )

    with pytest.raises(
        LLMConfigurationError,
        match="OLLAMA_API_KEY",
    ):
        factory.create()


def test_missing_ollama_model_is_rejected() -> None:
    factory = OllamaLLMFactory(
        settings=make_settings(model=""),
    )

    with pytest.raises(
        LLMConfigurationError,
        match="OLLAMA_MODEL",
    ):
        factory.create()


def test_model_name_gets_ollama_prefix() -> None:
    factory = OllamaLLMFactory(
        settings=make_settings(model="gemma-test"),
    )

    assert factory.normalized_model_name() == "ollama/gemma-test"


def test_existing_provider_prefix_is_preserved() -> None:
    factory = OllamaLLMFactory(
        settings=make_settings(model="ollama/gemma-test"),
    )

    assert factory.normalized_model_name() == "ollama/gemma-test"


def test_configuration_status_does_not_reveal_key() -> None:
    key = "private-test-key"
    factory = OllamaLLMFactory(
        settings=make_settings(api_key=key),
    )

    status = factory.configuration_status()

    assert status["api_key_configured"] is True
    assert key not in str(status)


def test_create_constructs_llm_without_network_call() -> None:
    factory = OllamaLLMFactory(
        settings=make_settings(),
    )

    llm = factory.create()

    assert llm is not None
    assert factory.normalized_model_name() == "ollama/gemma-test"
