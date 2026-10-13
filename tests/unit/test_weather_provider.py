"""Tests for the Open-Meteo weather provider."""

from datetime import date, timedelta

from smart_travel_planner.models import (
    DataMode,
    LocationResult,
    SourceMetadata,
)
from smart_travel_planner.providers.weather_provider import (
    OpenMeteoWeatherProvider,
)


class FakeHttpClient:
    """Return predictable weather data without using a live API."""

    def get_json(self, url, *, params=None, headers=None):
        requested_date = params["start_date"]

        return {
            "daily": {
                "time": [requested_date],
                "temperature_2m_max": [29.5],
                "temperature_2m_min": [17.2],
                "precipitation_probability_max": [10],
                "weather_code": [1],
            }
        }


def make_location() -> LocationResult:
    """Create a reusable Jaipur test location."""

    return LocationResult(
        query="Jaipur",
        name="Jaipur",
        latitude=26.9196,
        longitude=75.7878,
        country="India",
        source=SourceMetadata(
            provider="test",
            data_mode=DataMode.MOCK,
        ),
    )


def test_weather_provider_returns_structured_forecast() -> None:
    """The provider should convert valid API data into structured output."""

    provider = OpenMeteoWeatherProvider(FakeHttpClient())
    travel_date = date.today() + timedelta(days=2)

    result = provider.forecast(
        make_location(),
        travel_date,
        travel_date,
    )

    assert result.forecast_available is True
    assert len(result.daily) == 1
    assert result.daily[0].temperature_max_c == 29.5
    assert result.daily[0].temperature_min_c == 17.2
    assert result.daily[0].precipitation_probability_max == 10


def test_future_weather_is_reported_as_unavailable() -> None:
    """Weather outside the forecast window should not be invented."""

    provider = OpenMeteoWeatherProvider(FakeHttpClient())
    future_date = date.today() + timedelta(days=40)

    result = provider.forecast(
        make_location(),
        future_date,
        future_date + timedelta(days=2),
    )

    assert result.forecast_available is False
    assert result.source.data_mode == DataMode.UNAVAILABLE
    assert result.daily == []
