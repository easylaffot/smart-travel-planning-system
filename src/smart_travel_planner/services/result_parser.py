"""Safely parse structured CrewAI travel-plan results."""

import json
from typing import Any

from pydantic import ValidationError

from smart_travel_planner.models import (
    CrewExecutionResult,
    FinalTravelPlanOutput,
)
from smart_travel_planner.utils.exceptions import ResultParsingError


class TravelPlanResultParser:
    """Convert crew output into a validated final travel plan."""

    def parse(
        self,
        result: CrewExecutionResult | FinalTravelPlanOutput | Any,
    ) -> FinalTravelPlanOutput:
        """Parse supported output forms without silently accepting bad data."""

        if isinstance(result, FinalTravelPlanOutput):
            return result

        if isinstance(result, CrewExecutionResult):
            if result.structured_output is not None:
                return result.structured_output

            if result.raw_output:
                return self._parse_raw_json(result.raw_output)

            raise ResultParsingError("Crew execution returned no structured or raw output.")

        pydantic_output = getattr(result, "pydantic", None)

        if isinstance(pydantic_output, FinalTravelPlanOutput):
            return pydantic_output

        raw_output = getattr(result, "raw", None)

        if isinstance(raw_output, str) and raw_output.strip():
            return self._parse_raw_json(raw_output)

        if isinstance(result, dict):
            return self._validate_mapping(result)

        if isinstance(result, str):
            return self._parse_raw_json(result)

        raise ResultParsingError("Unsupported CrewAI result type.")

    def _parse_raw_json(self, raw_output: str) -> FinalTravelPlanOutput:
        try:
            payload = json.loads(raw_output)
        except json.JSONDecodeError as exc:
            raise ResultParsingError("Crew output was not valid JSON.") from exc

        return self._validate_mapping(payload)

    @staticmethod
    def _validate_mapping(
        payload: dict[str, Any],
    ) -> FinalTravelPlanOutput:
        try:
            return FinalTravelPlanOutput.model_validate(payload)
        except ValidationError as exc:
            raise ResultParsingError(
                "Crew output did not match the final travel-plan schema."
            ) from exc
