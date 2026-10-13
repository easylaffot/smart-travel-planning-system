from smart_travel_planner.models import (
    DataMode,
    LocationResult,
    SourceMetadata,
)
from smart_travel_planner.providers.routing_provider import (
    OsrmRoutingProvider,
)


class FakeHttpClient:
    def get_json(self, url, *, params=None, headers=None):
        return {
            "code": "Ok",
            "routes": [
                {
                    "distance": 12500.0,
                    "duration": 1800.0,
                }
            ],
        }


def make_location(
    name: str,
    latitude: float,
    longitude: float,
) -> LocationResult:
    return LocationResult(
        query=name,
        name=name,
        latitude=latitude,
        longitude=longitude,
        source=SourceMetadata(
            provider="test",
            data_mode=DataMode.MOCK,
        ),
    )


def test_routing_provider_converts_units() -> None:
    provider = OsrmRoutingProvider(FakeHttpClient())

    result = provider.route(
        make_location("Origin", 26.90, 75.70),
        make_location("Destination", 26.95, 75.80),
    )

    assert result.distance_km == 12.5
    assert result.duration_minutes == 30.0
    assert result.source.is_estimate is True
