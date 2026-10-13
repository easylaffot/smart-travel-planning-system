"""Road routing through the public OSRM demonstration endpoint."""

from typing import Literal

from smart_travel_planner.models.provider_results import (
    DataMode,
    LocationResult,
    RouteResult,
    SourceMetadata,
)
from smart_travel_planner.providers.http_client import SafeHttpClient
from smart_travel_planner.utils.exceptions import ProviderError

OSRM_BASE_URL = "https://router.project-osrm.org"


class OsrmRoutingProvider:
    """Estimate road distance and duration between two locations."""

    def __init__(self, http_client: SafeHttpClient | None = None) -> None:
        self.http_client = http_client or SafeHttpClient()

    def route(
        self,
        origin: LocationResult,
        destination: LocationResult,
        profile: Literal["driving", "walking", "cycling"] = "driving",
    ) -> RouteResult:
        """Return the fastest route between two resolved locations."""

        coordinates = (
            f"{origin.longitude},{origin.latitude};{destination.longitude},{destination.latitude}"
        )

        url = f"{OSRM_BASE_URL}/route/v1/{profile}/{coordinates}"

        payload = self.http_client.get_json(
            url,
            params={
                "overview": "false",
                "steps": "false",
                "alternatives": "false",
            },
        )

        if payload.get("code") != "Ok":
            raise ProviderError(
                f"Routing provider failed with code {payload.get('code', 'unknown')}"
            )

        routes = payload.get("routes") or []

        if not routes:
            raise ProviderError("Routing provider returned no available route")

        route = routes[0]

        try:
            distance_km = round(float(route["distance"]) / 1000, 2)
            duration_minutes = round(float(route["duration"]) / 60, 1)
        except (KeyError, TypeError, ValueError) as exc:
            raise ProviderError("Routing provider returned invalid route measurements") from exc

        return RouteResult(
            origin=origin.name,
            destination=destination.name,
            profile=profile,
            distance_km=distance_km,
            duration_minutes=duration_minutes,
            source=SourceMetadata(
                provider="osrm",
                data_mode=DataMode.LIVE,
                source_url=url,
                is_estimate=True,
                message=(
                    "Road duration is an estimate and does not include real-time traffic conditions"
                ),
            ),
        )
