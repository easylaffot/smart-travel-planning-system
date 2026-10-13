"""Weather forecasts using the Open-Meteo forecast API."""

from datetime import date, timedelta

from smart_travel_planner.models.provider_results import (
    DailyWeather,
    DataMode,
    LocationResult,
    SourceMetadata,
    WeatherResult,
)
from smart_travel_planner.providers.http_client import SafeHttpClient
from smart_travel_planner.utils.exceptions import ProviderError

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
MAX_FORECAST_DAYS = 16


class OpenMeteoWeatherProvider:
    """Retrieve available daily weather forecasts."""

    def __init__(self, http_client: SafeHttpClient | None = None) -> None:
        self.http_client = http_client or SafeHttpClient()

    def forecast(
        self,
        location: LocationResult,
        start_date: date,
        end_date: date,
    ) -> WeatherResult:
        """Return forecast data when the requested dates are available."""

        if end_date < start_date:
            raise ProviderError("Weather end date cannot be before start date")

        latest_available_date = date.today() + timedelta(days=MAX_FORECAST_DAYS - 1)

        if start_date > latest_available_date:
            return WeatherResult(
                location=location.name,
                latitude=location.latitude,
                longitude=location.longitude,
                forecast_available=False,
                daily=[],
                source=SourceMetadata(
                    provider="open_meteo_forecast",
                    data_mode=DataMode.UNAVAILABLE,
                    source_url=FORECAST_URL,
                    is_estimate=False,
                    message=("Travel dates are outside the currently available forecast window"),
                ),
            )

        forecast_end = min(end_date, latest_available_date)

        payload = self.http_client.get_json(
            FORECAST_URL,
            params={
                "latitude": location.latitude,
                "longitude": location.longitude,
                "start_date": start_date.isoformat(),
                "end_date": forecast_end.isoformat(),
                "daily": (
                    "weather_code,"
                    "temperature_2m_max,"
                    "temperature_2m_min,"
                    "precipitation_probability_max"
                ),
                "timezone": "auto",
            },
        )

        daily = payload.get("daily") or {}
        dates = daily.get("time") or []
        maximums = daily.get("temperature_2m_max") or []
        minimums = daily.get("temperature_2m_min") or []
        precipitation = daily.get("precipitation_probability_max") or []
        weather_codes = daily.get("weather_code") or []

        forecasts: list[DailyWeather] = []

        for index, date_value in enumerate(dates):
            forecasts.append(
                DailyWeather(
                    date=date.fromisoformat(date_value),
                    temperature_max_c=self._list_value(maximums, index),
                    temperature_min_c=self._list_value(minimums, index),
                    precipitation_probability_max=self._list_value(
                        precipitation,
                        index,
                    ),
                    weather_code=self._list_value(weather_codes, index),
                )
            )

        return WeatherResult(
            location=location.name,
            latitude=location.latitude,
            longitude=location.longitude,
            forecast_available=bool(forecasts),
            daily=forecasts,
            source=SourceMetadata(
                provider="open_meteo_forecast",
                data_mode=DataMode.LIVE,
                source_url=FORECAST_URL,
                is_estimate=False,
            ),
        )

    @staticmethod
    def _list_value(values: list, index: int):
        return values[index] if index < len(values) else None
