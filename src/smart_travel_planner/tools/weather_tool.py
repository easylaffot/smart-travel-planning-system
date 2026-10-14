"""CrewAI tool to resolve and summarize weather forecasts."""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

from smart_travel_planner.models.provider_results import DataMode
from smart_travel_planner.providers.location_provider import OpenMeteoLocationProvider
from smart_travel_planner.providers.weather_provider import OpenMeteoWeatherProvider
from smart_travel_planner.utils.exceptions import ProviderError


class WeatherToolInput(BaseModel):
    """Validated arguments for a weather-query tool."""

    location: str = Field(min_length=2)
    start_date: str = Field(min_length=1)
    end_date: str = Field(min_length=1)


class WeatherTool(BaseTool):
    """Resolve a place and return its compatible forecast payload."""

    name: str = "weather_forecast"
    description: str = (
        "Return structured weather data for a destination over a requested date range. "
        "If dates are outside the available window, the tool preserves that status rather "
        "than inventing future weather."
    )
    args_schema: type[BaseModel] = WeatherToolInput
    _location_provider: OpenMeteoLocationProvider = PrivateAttr()
    _weather_provider: OpenMeteoWeatherProvider = PrivateAttr()

    def __init__(
        self,
        location_provider: OpenMeteoLocationProvider | None = None,
        weather_provider: OpenMeteoWeatherProvider | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._location_provider = location_provider or OpenMeteoLocationProvider()
        self._weather_provider = weather_provider or OpenMeteoWeatherProvider()

    def _run(self, location: str, start_date: str, end_date: str) -> str:
        """Return a structured weather payload as JSON."""

        try:
            start = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date)
            if end < start:
                raise ProviderError("end_date cannot be earlier than start_date")

            resolved_location = self._location_provider.search(location)
            result = self._weather_provider.forecast(
                resolved_location,
                start,
                end,
            )
            payload = {
                "status": "success",
                "provider": "open_meteo_forecast",
                "data_mode": result.source.data_mode.value,
                "warning": (
                    "No weather was invented for dates outside the current forecast window."
                    if result.source.data_mode == DataMode.UNAVAILABLE
                    else None
                ),
                "error": None,
                "data": result.model_dump(mode="json"),
            }
        except ProviderError as exc:
            payload = {
                "status": "error",
                "provider": "open_meteo_forecast",
                "data_mode": "live",
                "warning": "Weather query failed for the submitted range.",
                "error": str(exc),
                "data": None,
            }
        except ValueError as exc:
            payload = {
                "status": "error",
                "provider": "open_meteo_forecast",
                "data_mode": "live",
                "warning": "Dates must use ISO format such as YYYY-MM-DD.",
                "error": str(exc),
                "data": None,
            }

        return json.dumps(payload, ensure_ascii=False, indent=2)
