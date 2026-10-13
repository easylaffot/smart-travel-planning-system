"""Location lookup using the Open-Meteo geocoding API."""

from smart_travel_planner.models.provider_results import (
    DataMode,
    LocationResult,
    SourceMetadata,
)
from smart_travel_planner.providers.http_client import SafeHttpClient
from smart_travel_planner.utils.exceptions import ProviderError

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"


class OpenMeteoLocationProvider:
    """Resolve user-friendly location names into coordinates."""

    def __init__(self, http_client: SafeHttpClient | None = None) -> None:
        self.http_client = http_client or SafeHttpClient()

    def search(self, location: str) -> LocationResult:
        """Return the best matching geographic result."""

        cleaned_location = " ".join(location.split())

        if len(cleaned_location) < 2:
            raise ProviderError("Location must contain at least two characters")

        payload = self.http_client.get_json(
            GEOCODING_URL,
            params={
                "name": cleaned_location,
                "count": 1,
                "language": "en",
                "format": "json",
            },
        )

        results = payload.get("results") or []

        if not results:
            raise ProviderError(f"No geographic result found for {cleaned_location!r}")

        result = results[0]

        try:
            return LocationResult(
                query=cleaned_location,
                name=result["name"],
                latitude=result["latitude"],
                longitude=result["longitude"],
                country=result.get("country"),
                administrative_area=result.get("admin1"),
                timezone=result.get("timezone"),
                source=SourceMetadata(
                    provider="open_meteo_geocoding",
                    data_mode=DataMode.LIVE,
                    source_url=GEOCODING_URL,
                    is_estimate=False,
                ),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ProviderError("Geocoding provider returned an invalid result") from exc
