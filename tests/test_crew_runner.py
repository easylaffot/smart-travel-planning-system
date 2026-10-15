"""Tests for safe live CrewAI execution diagnostics."""

from types import SimpleNamespace

import pytest

from smart_travel_planner.services.crew_runner import LiveCrewRunner
from smart_travel_planner.utils.exceptions import AgentExecutionError


def test_live_runner_reports_safe_exception_chain_and_http_status() -> None:
    secret_text = "sensitive-provider-response"

    class HttpFailure(RuntimeError):
        response = SimpleNamespace(status_code=401)

    class Crew:
        def kickoff(self, *, inputs: dict) -> None:
            raise RuntimeError(secret_text) from HttpFailure(secret_text)

    with pytest.raises(AgentExecutionError) as error:
        LiveCrewRunner(Crew()).run({})

    assert "RuntimeError -> HttpFailure" in str(error.value)
    assert "HTTP status: 401" in str(error.value)
    assert secret_text not in str(error.value)


def test_live_runner_logs_and_chains_unexpected_exception(caplog) -> None:
    original_error = LookupError("unexpected provider failure")

    class Crew:
        def kickoff(self, *, inputs: dict) -> None:
            raise original_error

    with pytest.raises(AgentExecutionError) as error:
        LiveCrewRunner(Crew()).run({})

    assert error.value.__cause__ is original_error
    assert "LookupError" in str(error.value)
    assert "Live CrewAI execution failed" in caplog.text
