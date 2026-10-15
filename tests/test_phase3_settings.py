"""Tests for Phase 3 LLM and CrewAI settings."""

from pydantic import SecretStr

from smart_travel_planner.config.settings import Settings


def test_phase3_execution_defaults_are_safe() -> None:
    """Phase 3 defaults should constrain agent execution."""

    settings = Settings(
        _env_file=None,
        app_env="test",
    )

    assert settings.llm_temperature == 0.2
    assert settings.llm_max_tokens == 8192
    assert settings.agent_max_iterations == 5
    assert settings.agent_max_execution_seconds == 180
    assert settings.crew_verbose is False
    assert settings.crew_cache_enabled is True


def test_safe_llm_status_does_not_reveal_key() -> None:
    """Configuration status must not include the secret value."""

    secret_value = "test-secret-value"

    settings = Settings(
        _env_file=None,
        app_env="test",
        ollama_api_key=SecretStr(secret_value),
        ollama_model="gemma-test",
    )

    status = settings.safe_llm_status()
    rendered = str(status)

    assert status["api_key_configured"] is True
    assert status["model_configured"] is True
    assert secret_value not in rendered


def test_ollama_configuration_requires_key_and_model() -> None:
    """Both the key and selected model are required."""

    missing_model = Settings(
        _env_file=None,
        ollama_api_key=SecretStr("test-key"),
        ollama_model="",
    )

    missing_key = Settings(
        _env_file=None,
        ollama_api_key=None,
        ollama_model="gemma-test",
    )

    configured = Settings(
        _env_file=None,
        ollama_api_key=SecretStr("test-key"),
        ollama_model="gemma-test",
    )

    assert missing_model.ollama_is_configured() is False
    assert missing_key.ollama_is_configured() is False
    assert configured.ollama_is_configured() is True
