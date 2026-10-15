"""CrewAI tool to call the destination-search provider."""

from __future__ import annotations

import json
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr, field_validator

from smart_travel_planner.providers.search_provider import DestinationSearchProvider
from smart_travel_planner.utils.exceptions import ProviderError


class SearchToolInput(BaseModel):
    """Structured arguments for destination-search requests."""

    destination: str = Field(min_length=2)
    interests: list[str] | str = Field(default_factory=list)
    result_limit: int = Field(default=5, ge=1, le=10)

    @field_validator("interests", mode="before")
    @classmethod
    def parse_interests(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return [str(value).strip()]


class DestinationSearchTool(BaseTool):
    """Search for destination ideas and return structured results."""

    name: str = "destination_search"
    description: str = (
        "Search for destination ideas and supporting sources for a city or region, "
        "based on the provided interests and destination context."
    )
    args_schema: type[BaseModel] = SearchToolInput
    _provider: DestinationSearchProvider = PrivateAttr()

    def __init__(
        self,
        provider: DestinationSearchProvider | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._provider = provider or DestinationSearchProvider()

    def _run(
        self,
        destination: str,
        interests: list[str] | str | None = None,
        result_limit: int = 5,
    ) -> str:
        """Return structured destination-search content as JSON."""

        if isinstance(interests, str):
            interest_items = [item.strip() for item in interests.split(",") if item.strip()]
        elif interests is None:
            interest_items = []
        else:
            interest_items = [str(item).strip() for item in interests if str(item).strip()]

        query = " ".join([destination.strip(), *interest_items]).strip()

        try:
            result = self._provider.search(
                query=query,
                destination=destination,
                result_limit=result_limit,
                interests=interest_items,
            )
            has_mock_results = result.data_mode.value == "mock" and bool(result.results)
            attractions = (
                [
                    {
                        "name": f"Prototype attraction idea {index} for {result.destination}",
                        "category": "prototype_attraction_idea",
                        "data_mode": "mock",
                    }
                    for index in range(1, 4)
                ]
                if has_mock_results
                else []
            )
            local_experiences = (
                [
                    {
                        "name": f"Prototype local experience idea {index} for {result.destination}",
                        "category": "prototype_local_experience_idea",
                        "data_mode": "mock",
                    }
                    for index in range(1, 3)
                ]
                if has_mock_results
                else []
            )
            routing_notes = []
            sources = (
                [item.url for item in result.results if item.url]
                if result.data_mode.value == "live"
                else []
            )
            if result.data_mode.value == "live":
                attractions = []
                local_experiences = []
                for item in result.results:
                    searchable_text = f"{item.title} {item.snippet}".casefold()
                    is_routing_guidance = _contains_any(
                        searchable_text,
                        ("transport", "transit", "route", "getting around", "traffic"),
                    )
                    record = {
                        "name": item.title,
                        "category": _live_category(searchable_text),
                        "description": item.snippet,
                        "source_url": item.url,
                        "duration": "Not specified",
                        "data_mode": "live",
                    }
                    if is_routing_guidance:
                        routing_notes.append(f"{item.snippet} ({item.url})")
                    if _contains_any(
                        searchable_text,
                        (
                            "food",
                            "cuisine",
                            "restaurant",
                            "market",
                            "bazaar",
                            "culture",
                            "cultural",
                            "experience",
                            "festival",
                            "workshop",
                        ),
                    ):
                        local_experiences.append(record)
                    elif not is_routing_guidance:
                        attractions.append(record)
            payload = {
                "status": "success",
                "provider": result.provider,
                "data_mode": result.data_mode.value,
                "warning": result.warning,
                "error": None,
                "data": {
                    "query": result.query,
                    "destination": result.destination,
                    "results": [item.model_dump(mode="json") for item in result.results],
                    "attractions": attractions,
                    "local_experiences": local_experiences,
                    "routing_notes": routing_notes,
                    "sources": sources,
                },
            }
        except ProviderError as exc:
            payload = {
                "status": "unavailable",
                "provider": "destination_search",
                "data_mode": "unavailable",
                "warning": "Destination search was unavailable for the submitted query.",
                "error": str(exc),
                "data": None,
            }

        return json.dumps(payload, ensure_ascii=False, indent=2)


def _contains_any(value: str, terms: tuple[str, ...]) -> bool:
    return any(term in value for term in terms)


def _live_category(value: str) -> str:
    if _contains_any(value, ("food", "cuisine", "restaurant")):
        return "local_food"
    if _contains_any(value, ("culture", "cultural", "festival", "workshop")):
        return "cultural_experience"
    if _contains_any(value, ("market", "bazaar")):
        return "market"
    if _contains_any(value, ("transport", "transit", "route", "traffic")):
        return "transport_guidance"
    return "attraction"
