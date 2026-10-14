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
            )
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
                },
            }
        except ProviderError as exc:
            payload = {
                "status": "error",
                "provider": "destination_search",
                "data_mode": "live",
                "warning": "Destination search failed for the submitted query.",
                "error": str(exc),
                "data": None,
            }

        return json.dumps(payload, ensure_ascii=False, indent=2)
