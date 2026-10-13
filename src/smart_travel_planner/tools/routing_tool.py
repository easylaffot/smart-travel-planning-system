"""CrewAI tool to resolve routes between two locations."""

from __future__ import annotations

import json
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from smart_travel_planner.models.provider_results import DataMode
from smart_travel_planner.providers.location_provider import OpenMeteoLocationProvider
from smart_travel_planner.providers.routing_provider import OsrmRoutingProvider
from smart_travel_planner.utils.exceptions import ProviderError


class RoutingToolInput(BaseModel):
    """Validated arguments for routing calculations."""

    origin: str = Field(min_length=2)
    destination: str = Field(min_length=2)
    profile: str = Field(default="driving")


class RoutingTool(BaseTool):
    """Resolve both endpoints and return a structured route summary."""

    name: str = "route_search"
    description: str = (
        "Calculate a route between two locations using the supported road profiles: "
        "driving, walking, and cycling."
    )
    args_schema: type[BaseModel] = RoutingToolInput
    location_provider: Any = Field(
        default_factory=OpenMeteoLocationProvider,
        exclude=True,
    )
    routing_provider: Any = Field(
        default_factory=OsrmRoutingProvider,
        exclude=True,
    )

    def __init__(
        self,
        location_provider: Any | None = None,
        routing_provider: Any | None = None,
    ) -> None:
        super().__init__(
            location_provider=location_provider or OpenMeteoLocationProvider(),
            routing_provider=routing_provider or OsrmRoutingProvider(),
        )

    def _run(self, origin: str, destination: str, profile: str = "driving") -> str:
        """Return route data as a JSON payload."""

        supported_profiles = {"driving", "walking", "cycling"}
        normalized_profile = profile.strip().lower()

        try:
            if normalized_profile not in supported_profiles:
                raise ProviderError(
                    "Unsupported route profile. Supported profiles: driving, walking, cycling"
                )

            origin_result = self.location_provider.search(origin)
            destination_result = self.location_provider.search(destination)
            route = self.routing_provider.route(
                origin_result,
                destination_result,
                profile=normalized_profile,
            )
            payload = {
                "status": "success",
                "provider": "osrm",
                "data_mode": route.source.data_mode.value,
                "warning": None,
                "error": None,
                "data": {
                    "origin": route.origin,
                    "destination": route.destination,
                    "profile": route.profile,
                    "distance_km": route.distance_km,
                    "duration_minutes": route.duration_minutes,
                    "is_estimate": route.source.is_estimate,
                    "source_url": (
                        str(route.source.source_url) if route.source.source_url else None
                    ),
                },
            }
        except ProviderError as exc:
            payload = {
                "status": "error",
                "provider": "osrm",
                "data_mode": DataMode.LIVE.value,
                "warning": "Route calculation failed for the submitted locations.",
                "error": str(exc),
                "data": None,
            }

        return json.dumps(payload, ensure_ascii=False, indent=2)
