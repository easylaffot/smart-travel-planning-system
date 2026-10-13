"""Structured outputs returned by external and mock providers."""

from datetime import UTC, date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl


class DataMode(StrEnum):
    """Indicates where a result originated."""

    LIVE = "live"
    SEARCH = "search"
    CACHED = "cached"
    MOCK = "mock"
    ESTIMATED = "estimated"
    UNAVAILABLE = "unavailable"


class SourceMetadata(BaseModel):
    """Source and freshness information attached to provider results."""

    provider: str
    data_mode: DataMode
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source_url: HttpUrl | None = None
    is_estimate: bool = False
    message: str | None = None


class SearchResultItem(BaseModel):
    """One destination-search result returned by a live or mock provider."""

    title: str
    url: str = ""
    snippet: str = ""
    provider: str = "destination_search"
    data_mode: DataMode = DataMode.MOCK
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DestinationSearchResult(BaseModel):
    """Structured output returned by the destination-search provider."""

    query: str
    destination: str
    results: list[SearchResultItem] = Field(default_factory=list)
    warning: str | None = None
    provider: str = "destination_search"
    data_mode: DataMode = DataMode.MOCK
    source: SourceMetadata | None = None


class LocationResult(BaseModel):
    """Resolved geographic location."""

    query: str
    name: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    country: str | None = None
    administrative_area: str | None = None
    timezone: str | None = None
    source: SourceMetadata


class DailyWeather(BaseModel):
    """Weather information for one calendar day."""

    date: date
    temperature_max_c: float | None = None
    temperature_min_c: float | None = None
    precipitation_probability_max: int | None = Field(
        default=None,
        ge=0,
        le=100,
    )
    weather_code: int | None = None


class WeatherResult(BaseModel):
    """Weather forecast returned for a destination."""

    location: str
    latitude: float
    longitude: float
    forecast_available: bool
    daily: list[DailyWeather] = Field(default_factory=list)
    source: SourceMetadata


class RouteResult(BaseModel):
    """Road distance and duration between two coordinates."""

    origin: str
    destination: str
    profile: str
    distance_km: float = Field(ge=0)
    duration_minutes: float = Field(ge=0)
    source: SourceMetadata
