"""CrewAI tool to resolve a location string into a structured geographic result."""

from __future__ import annotations

import json
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from smart_travel_planner.providers.location_provider import OpenMeteoLocationProvider
from smart_travel_planner.utils.exceptions import ProviderError


class LocationToolInput(BaseModel):
    """Validated arguments for a location lookup tool."""

    location: str = Field(min_length=2)


class LocationTool(BaseTool):
    """Resolve a location into a structured provider result."""

    name: str = "location_lookup"
    description: str = (
        "Resolve a user-provided location string to latitude/longitude, country, "
        "and metadata using the configured provider."
    )
    args_schema: type[BaseModel] = LocationToolInput
    provider: Any = Field(default_factory=OpenMeteoLocationProvider, exclude=True)

    def __init__(self, provider: Any | None = None) -> None:
        super().__init__(provider=provider or OpenMeteoLocationProvider())

    def _run(self, location: str) -> str:
        """Return a safe JSON payload for the resolved location."""

        try:
            result = self.provider.search(location)
            payload = {
                "status": "success",
                "provider": "open_meteo_geocoding",
                "data_mode": result.source.data_mode.value,
                "warning": None,
                "error": None,
                "data": result.model_dump(mode="json"),
            }
        except ProviderError as exc:
            payload = {
                "status": "error",
                "provider": "open_meteo_geocoding",
                "data_mode": "live",
                "warning": "Location resolution failed for the submitted value.",
                "error": str(exc),
                "data": None,
            }

        return json.dumps(payload, ensure_ascii=False, indent=2)
