"""Crew execution adapters used by the planning service."""

from typing import Any, Protocol

from crewai import Crew

from smart_travel_planner.models import CrewExecutionResult
from smart_travel_planner.utils.exceptions import AgentExecutionError


class CrewRunner(Protocol):
    """Contract followed by live and fake crew runners."""

    def run(self, inputs: dict[str, Any]) -> CrewExecutionResult:
        """Execute or simulate a crew run."""


class LiveCrewRunner:
    """Execute a configured CrewAI Crew."""

    def __init__(self, crew: Crew) -> None:
        self.crew = crew

    def run(self, inputs: dict[str, Any]) -> CrewExecutionResult:
        """Run CrewAI and normalize the immediate output container."""

        try:
            output = self.crew.kickoff(inputs=inputs)
        except (RuntimeError, ValueError, TypeError) as exc:
            raise AgentExecutionError(
                "The travel-planning crew could not complete execution."
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
