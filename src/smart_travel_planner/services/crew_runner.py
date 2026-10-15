"""Crew execution adapters used by the planning service."""

import logging
from typing import Any, Protocol

from crewai import Crew

from smart_travel_planner.models import CrewExecutionResult
from smart_travel_planner.utils.exceptions import AgentExecutionError

logger = logging.getLogger(__name__)


class CrewRunner(Protocol):
    """Contract followed by live and fake crew runners."""

    def run(self, inputs: dict[str, Any]) -> CrewExecutionResult:
        """Execute or simulate a crew run."""


def _safe_execution_error(exc: Exception) -> str:
    """Describe failure types and HTTP status without exposing exception text."""

    chain: list[str] = []
    http_status: int | None = None
    current: BaseException | None = exc
    seen: set[int] = set()

    while current is not None and id(current) not in seen and len(chain) < 5:
        seen.add(id(current))
        chain.append(type(current).__name__)

        response = getattr(current, "response", None)
        status_code = getattr(response, "status_code", None)
        if isinstance(status_code, int) and 100 <= status_code <= 599:
            http_status = status_code

        current = current.__cause__ or current.__context__

    detail = f"Exception chain: {' -> '.join(chain)}."
    if http_status is not None:
        detail += f" HTTP status: {http_status}."

    return detail


class LiveCrewRunner:
    """Execute a configured CrewAI Crew."""

    def __init__(self, crew: Crew) -> None:
        self.crew = crew

    def run(self, inputs: dict[str, Any]) -> CrewExecutionResult:
        """Run CrewAI and normalize the immediate output container."""

        try:
            output = self.crew.kickoff(inputs=inputs)
        except Exception as exc:
            logger.exception("Live CrewAI execution failed")
            raise AgentExecutionError(
                "The travel-planning crew could not complete execution. "
                f"{_safe_execution_error(exc)}"
            ) from exc

        structured = getattr(output, "pydantic", None)
        raw = getattr(output, "raw", None)

        if raw is None:
            raw = str(output)

        return CrewExecutionResult(
            raw_output=raw,
            structured_output=structured,
            metadata={
                "runner": "live_crewai",
            },
        )


class FakeCrewRunner:
    """Offline runner for deterministic automated tests."""

    def __init__(self, result: CrewExecutionResult) -> None:
        self.result = result
        self.call_count = 0
        self.last_inputs: dict[str, Any] | None = None

    def run(self, inputs: dict[str, Any]) -> CrewExecutionResult:
        """Return the configured result without any network call."""

        self.call_count += 1
        self.last_inputs = dict(inputs)
        return self.result
