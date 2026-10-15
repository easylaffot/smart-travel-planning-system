import json
import logging
from datetime import date, timedelta
from types import SimpleNamespace

import httpx
import pytest
from pydantic import SecretStr

from smart_travel_planner.models.provider_results import (
    DailyWeather,
    DataMode,
    LocationResult,
    RouteResult,
    SourceMetadata,
    WeatherResult,
)
from smart_travel_planner.providers.search_provider import DestinationSearchProvider
from smart_travel_planner.tools.budget_tool import BudgetCalculatorTool
from smart_travel_planner.tools.hotel_tool import HotelSearchTool
from smart_travel_planner.tools.location_tool import LocationTool
from smart_travel_planner.tools.routing_tool import RoutingTool
from smart_travel_planner.tools.schedule_tool import ItineraryScheduleValidatorTool
from smart_travel_planner.tools.search_tool import DestinationSearchTool
from smart_travel_planner.tools.transport_tool import TransportSearchTool
from smart_travel_planner.tools.weather_tool import WeatherTool


class FakeSearchHttpClient:
    def __init__(self, payload=None, *, status_code=200, responses=None):
        self.responses = list(responses or [(status_code, payload or {})])
        self.requests = []
        self.call_count = 0

    def post(self, url, *, headers, json, timeout):
        self.call_count += 1
        self.requests.append(
            {
                "url": url,
                "headers": headers,
                "json": json,
                "timeout": timeout,
            }
        )
        response = self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]
        if isinstance(response, Exception):
            raise response
        if isinstance(response, tuple):
            status_code, payload = response
        else:
            status_code, payload = 200, response
        return FakeSearchResponse(status_code, payload)


class FakeSearchResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self.payload = payload

    def json(self):
        return self.payload


class FakeLocationProvider:
    def search(self, location):
        return LocationResult(
            query=location,
            name="Jaipur",
            latitude=26.9196,
            longitude=75.7878,
            country="India",
            source=SourceMetadata(
                provider="fake_location_provider",
                data_mode=DataMode.LIVE,
                source_url="https://example.com/location",
                is_estimate=False,
            ),
        )


class FakeWeatherProvider:
    def __init__(self, result):
        self.result = result

    def forecast(self, location, start_date, end_date):
        return self.result


class FakeRoutingProvider:
    def __init__(self, result):
        self.result = result

    def route(self, origin, destination, profile="driving"):
        return self.result


class FakeDestinationSearchProvider:
    def search(self, query, destination, result_limit=5):
        raise AssertionError("The provider should not be called during construction")


@pytest.fixture(autouse=True)
def clear_destination_search_cache():
    DestinationSearchProvider._cache.clear()


def test_all_tools_instantiate_with_private_provider_dependencies() -> None:
    default_search_tool = DestinationSearchTool()
    fake_search_provider = FakeDestinationSearchProvider()
    injected_search_tool = DestinationSearchTool(provider=fake_search_provider)
    tools = [
        default_search_tool,
        injected_search_tool,
        LocationTool(),
        WeatherTool(),
        RoutingTool(),
        HotelSearchTool(),
        TransportSearchTool(),
        BudgetCalculatorTool(),
        ItineraryScheduleValidatorTool(),
    ]

    assert isinstance(default_search_tool._provider, DestinationSearchProvider)
    assert injected_search_tool._provider is fake_search_provider
    for tool in tools:
        serialized = tool.model_dump()
        tool_arguments = tool.args_schema.model_fields
        assert {"name", "description", "args_schema"}.issubset(type(tool).model_fields)
        assert not {
            "provider",
            "location_provider",
            "weather_provider",
            "routing_provider",
        }.intersection(serialized)
        assert not {
            "provider",
            "location_provider",
            "weather_provider",
            "routing_provider",
        }.intersection(tool_arguments)


def test_mock_destination_search_fallback_when_key_is_empty(monkeypatch) -> None:
    monkeypatch.setattr(
        "smart_travel_planner.providers.search_provider.get_settings",
        lambda: SimpleNamespace(
            search_api_key=None,
            search_api_url="https://example.com/search",
            request_timeout_seconds=45,
        ),
    )

    http_client = FakeSearchHttpClient()
    provider = DestinationSearchProvider(http_client=http_client)
    result = provider.search("Jaipur heritage", "Jaipur", result_limit=3)

    assert result.data_mode == DataMode.MOCK
    assert result.warning is not None
    assert len(result.results) == 3
    assert "prototype" in result.results[0].title.lower()
    assert http_client.call_count == 0


def test_search_tool_returns_mock_attraction_and_experience_records(monkeypatch) -> None:
    monkeypatch.setattr(
        "smart_travel_planner.providers.search_provider.get_settings",
        lambda: SimpleNamespace(
            search_api_key=None,
            search_api_url="https://example.com/search",
            request_timeout_seconds=20,
        ),
    )
    http_client = FakeSearchHttpClient({})
    provider = DestinationSearchProvider(http_client=http_client)
    tool = DestinationSearchTool(provider=provider)

    payload = json.loads(
        tool._run(
            destination="Jaipur",
            interests=["culture", "local food"],
            result_limit=5,
        )
    )

    attractions = payload["data"]["attractions"]
    experiences = payload["data"]["local_experiences"]
    assert payload["status"] == "success"
    assert payload["data_mode"] == "mock"
    assert len(attractions) >= 3
    assert len(experiences) >= 2
    assert all(
        {"name", "category", "data_mode"}.issubset(record) for record in attractions + experiences
    )
    assert all(record["data_mode"] == "mock" for record in attractions + experiences)
    assert http_client.call_count == 0


def test_live_search_response_parsing_through_fake_http_client(monkeypatch) -> None:
    monkeypatch.setattr(
        "smart_travel_planner.providers.search_provider.get_settings",
        lambda: SimpleNamespace(
            search_api_key=SecretStr("demo-key"),
            search_api_url="https://example.com/search",
            request_timeout_seconds=45,
        ),
    )

    http_client = FakeSearchHttpClient(
        {
            "results": [
                {
                    "title": "Jaipur attractions",
                    "url": "https://example.com/jaipur",
                    "content": "Historic palaces and bazaars.",
                }
            ]
        }
    )
    provider = DestinationSearchProvider(http_client=http_client)

    result = provider.search("Jaipur", "Jaipur", result_limit=5)

    assert result.data_mode == DataMode.LIVE
    assert result.results[0].title == "Jaipur attractions"
    assert result.results[0].provider == "tavily"
    assert result.results[0].url == "https://example.com/jaipur"
    assert http_client.call_count == 1
    request = http_client.requests[0]
    assert request["url"] == "https://api.tavily.com/search"
    assert request["headers"]["Authorization"].startswith("Bearer ")
    assert request["headers"]["Content-Type"] == "application/json"
    assert request["timeout"] == 30
    assert request["json"]["search_depth"] == "basic"
    assert request["json"]["topic"] == "general"
    assert request["json"]["max_results"] == 8
    assert request["json"]["include_answer"] is False
    assert request["json"]["include_raw_content"] is False
    assert request["json"]["include_images"] is False
    assert request["json"]["auto_parameters"] is False


def test_search_header_value_is_not_logged(monkeypatch, caplog) -> None:
    monkeypatch.setattr(
        "smart_travel_planner.providers.search_provider.get_settings",
        lambda: SimpleNamespace(
            search_api_key=SecretStr("private-test-key"),
            request_timeout_seconds=10,
        ),
    )
    http_client = FakeSearchHttpClient({"results": []})
    provider = DestinationSearchProvider(http_client=http_client)

    with caplog.at_level(logging.DEBUG):
        provider.search("Jaipur", "Jaipur")

    assert http_client.requests[0]["headers"]["Authorization"] == "Bearer private-test-key"
    assert "private-test-key" not in caplog.text


def test_tavily_timeout_retries_once_then_uses_mock_fallback(monkeypatch) -> None:
    monkeypatch.setattr(
        "smart_travel_planner.providers.search_provider.get_settings",
        lambda: SimpleNamespace(
            search_api_key=SecretStr("private-test-key"),
            request_timeout_seconds=12,
        ),
    )
    http_client = FakeSearchHttpClient(
        responses=[httpx.TimeoutException("timeout"), httpx.TimeoutException("timeout")]
    )

    result = DestinationSearchProvider(http_client=http_client).search(
        "Timeout City",
        "Timeout City",
    )

    assert result.data_mode == DataMode.MOCK
    assert http_client.call_count == 2
    assert all(request["timeout"] == 12 for request in http_client.requests)


def test_tavily_rate_limit_retries_once_then_uses_mock_fallback(monkeypatch) -> None:
    monkeypatch.setattr(
        "smart_travel_planner.providers.search_provider.get_settings",
        lambda: SimpleNamespace(
            search_api_key=SecretStr("private-test-key"),
            request_timeout_seconds=20,
        ),
    )
    http_client = FakeSearchHttpClient(responses=[(429, {}), (429, {})])

    result = DestinationSearchProvider(http_client=http_client).search(
        "Limited City",
        "Limited City",
    )

    assert result.data_mode == DataMode.MOCK
    assert http_client.call_count == 2


def test_tavily_empty_or_error_response_uses_mock_fallback(monkeypatch) -> None:
    monkeypatch.setattr(
        "smart_travel_planner.providers.search_provider.get_settings",
        lambda: SimpleNamespace(
            search_api_key=SecretStr("private-test-key"),
            request_timeout_seconds=20,
        ),
    )

    for city, payload in (
        ("Empty City", {"results": []}),
        ("Error City", {"error": "search unavailable"}),
    ):
        result = DestinationSearchProvider(http_client=FakeSearchHttpClient(payload)).search(
            city, city
        )
        assert result.data_mode == DataMode.MOCK


def test_live_search_cache_reuses_results_for_normalized_interests(monkeypatch) -> None:
    monkeypatch.setattr(
        "smart_travel_planner.providers.search_provider.get_settings",
        lambda: SimpleNamespace(
            search_api_key=SecretStr("private-test-key"),
            request_timeout_seconds=20,
        ),
    )
    http_client = FakeSearchHttpClient(
        {
            "results": [
                {
                    "title": "Cache City guide",
                    "url": "https://example.com/cache-city",
                    "content": "Attractions and local food.",
                }
            ]
        }
    )
    provider = DestinationSearchProvider(http_client=http_client)

    first = provider.search("Cache City", "  Cache   City ", interests=["Food", "Museums"])
    second = provider.search("Cache City", "cache city", interests=["museums", "food"])

    assert first.results == second.results
    assert http_client.call_count == 1


def test_malformed_search_response_uses_mock_fallback(monkeypatch) -> None:
    monkeypatch.setattr(
        "smart_travel_planner.providers.search_provider.get_settings",
        lambda: SimpleNamespace(
            search_api_key=SecretStr("demo-key"),
            search_api_url="https://example.com/search",
        ),
    )

    provider = DestinationSearchProvider(http_client=FakeSearchHttpClient({"unexpected": []}))

    result = provider.search("Jaipur", "Jaipur")

    assert result.data_mode == DataMode.MOCK
    assert result.warning is not None


def test_location_tool_returns_structured_json() -> None:
    tool = LocationTool(provider=FakeLocationProvider())

    result = json.loads(tool._run("Jaipur"))

    assert result["status"] == "success"
    assert result["data_mode"] == "live"
    assert result["data"]["name"] == "Jaipur"
    assert result["data"]["country"] == "India"


def test_weather_tool_returns_forecast_data_through_fake_providers() -> None:
    weather_result = WeatherResult(
        location="Jaipur",
        latitude=26.9196,
        longitude=75.7878,
        forecast_available=True,
        daily=[
            DailyWeather(
                date=date.today(),
                temperature_max_c=29.5,
                temperature_min_c=17.2,
                precipitation_probability_max=10,
                weather_code=1,
            )
        ],
        source=SourceMetadata(
            provider="fake_weather_provider",
            data_mode=DataMode.LIVE,
            source_url="https://example.com/weather",
            is_estimate=False,
        ),
    )
    tool = WeatherTool(
        location_provider=FakeLocationProvider(),
        weather_provider=FakeWeatherProvider(weather_result),
    )

    payload = json.loads(
        tool._run(
            location="Jaipur",
            start_date=date.today().isoformat(),
            end_date=date.today().isoformat(),
        )
    )

    assert payload["status"] == "success"
    assert payload["data"]["forecast_available"] is True
    assert payload["data"]["daily"][0]["temperature_max_c"] == 29.5


def test_weather_tool_preserves_unavailable_status_outside_forecast_window() -> None:
    weather_result = WeatherResult(
        location="Jaipur",
        latitude=26.9196,
        longitude=75.7878,
        forecast_available=False,
        daily=[],
        source=SourceMetadata(
            provider="fake_weather_provider",
            data_mode=DataMode.UNAVAILABLE,
            source_url="https://example.com/weather",
            is_estimate=False,
            message="Dates outside forecast range.",
        ),
    )
    tool = WeatherTool(
        location_provider=FakeLocationProvider(),
        weather_provider=FakeWeatherProvider(weather_result),
    )

    payload = json.loads(
        tool._run(
            location="Jaipur",
            start_date=(date.today() + timedelta(days=40)).isoformat(),
            end_date=(date.today() + timedelta(days=41)).isoformat(),
        )
    )

    assert payload["status"] == "success"
    assert payload["data_mode"] == "unavailable"
    assert payload["warning"] is not None
    assert payload["data"]["forecast_available"] is False


def test_routing_tool_returns_converted_distance_and_duration() -> None:
    result = RouteResult(
        origin="Mumbai",
        destination="Jaipur",
        profile="driving",
        distance_km=12.5,
        duration_minutes=30.0,
        source=SourceMetadata(
            provider="fake_routing_provider",
            data_mode=DataMode.LIVE,
            source_url="https://example.com/route",
            is_estimate=True,
        ),
    )
    tool = RoutingTool(
        location_provider=FakeLocationProvider(),
        routing_provider=FakeRoutingProvider(result),
    )

    payload = json.loads(tool._run("Mumbai", "Jaipur", profile="driving"))

    assert payload["status"] == "success"
    assert payload["data"]["distance_km"] == 12.5
    assert payload["data"]["duration_minutes"] == 30.0
    assert payload["data"]["is_estimate"] is True


def test_routing_tool_rejects_unsupported_profiles() -> None:
    tool = RoutingTool(
        location_provider=FakeLocationProvider(),
        routing_provider=FakeRoutingProvider(
            RouteResult(
                origin="Mumbai",
                destination="Jaipur",
                profile="driving",
                distance_km=1.0,
                duration_minutes=10.0,
                source=SourceMetadata(
                    provider="fake_routing_provider",
                    data_mode=DataMode.LIVE,
                    source_url="https://example.com/route",
                    is_estimate=True,
                ),
            )
        ),
    )

    payload = json.loads(tool._run("Mumbai", "Jaipur", profile="flying"))

    assert payload["status"] == "error"
    assert "Unsupported route profile" in payload["error"]


def test_schedule_validator_accepts_non_overlapping_activities() -> None:
    trip_start = date(2025, 1, 10)
    trip_end = date(2025, 1, 12)
    payload = json.loads(
        ItineraryScheduleValidatorTool()._run(
            trip_start_date=trip_start,
            trip_end_date=trip_end,
            activities=[
                {
                    "date": "2025-01-10",
                    "start_time": "09:00:00",
                    "end_time": "10:30:00",
                    "title": "Museum visit",
                    "location": "Jaipur",
                    "category": "culture",
                    "estimated_cost": "250.00",
                    "currency": "INR",
                },
                {
                    "date": "2025-01-10",
                    "start_time": "12:00:00",
                    "end_time": "13:00:00",
                    "title": "Lunch",
                    "location": "Jaipur",
                    "category": "food",
                    "estimated_cost": "350.00",
                    "currency": "INR",
                },
            ],
        )
    )

    assert payload["valid"] is True
    assert payload["activity_count"] == 2


def test_schedule_validator_detects_overlapping_activities() -> None:
    payload = json.loads(
        ItineraryScheduleValidatorTool()._run(
            trip_start_date=date(2025, 1, 10),
            trip_end_date=date(2025, 1, 12),
            activities=[
                {
                    "date": "2025-01-10",
                    "start_time": "09:00:00",
                    "end_time": "11:00:00",
                    "title": "Activity one",
                    "location": "Jaipur",
                    "category": "travel",
                    "estimated_cost": "100.00",
                    "currency": "INR",
                },
                {
                    "date": "2025-01-10",
                    "start_time": "10:30:00",
                    "end_time": "12:00:00",
                    "title": "Activity two",
                    "location": "Jaipur",
                    "category": "travel",
                    "estimated_cost": "120.00",
                    "currency": "INR",
                },
            ],
        )
    )

    assert payload["valid"] is False
    assert any("Overlapping" in item for item in payload["conflicts"])


def test_schedule_validator_rejects_activities_outside_trip_dates() -> None:
    payload = json.loads(
        ItineraryScheduleValidatorTool()._run(
            trip_start_date=date(2025, 1, 10),
            trip_end_date=date(2025, 1, 12),
            activities=[
                {
                    "date": "2025-01-13",
                    "start_time": "09:00:00",
                    "end_time": "10:00:00",
                    "title": "Outside trip",
                    "location": "Jaipur",
                    "category": "travel",
                    "estimated_cost": "99.00",
                    "currency": "INR",
                }
            ],
        )
    )

    assert payload["valid"] is False
    assert any("outside the trip window" in item for item in payload["conflicts"])


def test_schedule_validator_orders_activities_chronologically() -> None:
    payload = json.loads(
        ItineraryScheduleValidatorTool()._run(
            trip_start_date=date(2025, 1, 10),
            trip_end_date=date(2025, 1, 10),
            activities=[
                {
                    "date": "2025-01-10",
                    "start_time": "12:00:00",
                    "end_time": "13:00:00",
                    "title": "Lunch",
                    "location": "Jaipur",
                    "category": "food",
                    "estimated_cost": "250.00",
                    "currency": "INR",
                },
                {
                    "date": "2025-01-10",
                    "start_time": "09:00:00",
                    "end_time": "10:30:00",
                    "title": "Museum visit",
                    "location": "Jaipur",
                    "category": "culture",
                    "estimated_cost": "300.00",
                    "currency": "INR",
                },
            ],
        )
    )

    first_start = payload["ordered_days"][0]["activities"][0]["start_time"]
    assert first_start == "09:00:00"


def test_schedule_validator_rejects_end_time_before_start_time() -> None:
    payload = json.loads(
        ItineraryScheduleValidatorTool()._run(
            trip_start_date=date(2025, 1, 10),
            trip_end_date=date(2025, 1, 12),
            activities=[
                {
                    "date": "2025-01-10",
                    "start_time": "12:00:00",
                    "end_time": "11:00:00",
                    "title": "Broken timing",
                    "location": "Jaipur",
                    "category": "travel",
                    "estimated_cost": "0.00",
                    "currency": "INR",
                }
            ],
        )
    )

    assert payload["valid"] is False
    assert any("before or at start time" in item for item in payload["conflicts"])


def test_empty_schedule_produces_valid_warning_instead_of_crashing() -> None:
    payload = json.loads(
        ItineraryScheduleValidatorTool()._run(
            trip_start_date=date(2025, 1, 10),
            trip_end_date=date(2025, 1, 12),
            activities=[],
        )
    )

    assert payload["valid"] is True
    assert payload["activity_count"] == 0
    assert any("No activities scheduled" in item for item in payload["warnings"])
