from smart_travel_planner.models import DataMode
from smart_travel_planner.providers.location_provider import (
    OpenMeteoLocationProvider,
)


class FakeHttpClient:
    def get_json(self, url, *, params=None, headers=None):
        return {
            "results": [
                {
                    "name": "Jaipur",
                    "latitude": 26.9196,
                    "longitude": 75.7878,
                    "country": "India",
                    "admin1": "Rajasthan",
                    "timezone": "Asia/Kolkata",
                }
            ]
        }


def test_location_provider_returns_structured_result() -> None:
    provider = OpenMeteoLocationProvider(FakeHttpClient())

    result = provider.search("Jaipur")

    assert result.name == "Jaipur"
    assert result.country == "India"
    assert result.latitude == 26.9196
    assert result.source.data_mode == DataMode.LIVE
