"""Destination search provider with live and mock fallback handling."""

from __future__ import annotations

from smart_travel_planner.config.settings import get_settings
from smart_travel_planner.models.provider_results import (
    DataMode,
    DestinationSearchResult,
    SearchResultItem,
    SourceMetadata,
)
from smart_travel_planner.providers.http_client import SafeHttpClient
from smart_travel_planner.utils.exceptions import ProviderError


class DestinationSearchProvider:
    """Resolve a destination with either a configured live provider or mock demo data."""

    def __init__(
        self,
        http_client: SafeHttpClient | None = None,
        endpoint: str | None = None,
    ) -> None:
        settings = get_settings()
        self.http_client = http_client or SafeHttpClient()
        self.endpoint = endpoint or settings.search_api_url or "https://example.com/search"
        self.search_api_key = (
            settings.search_api_key.get_secret_value() if settings.search_api_key else None
        )

    def search(
        self,
        query: str,
        destination: str,
        result_limit: int = 5,
    ) -> DestinationSearchResult:
        """Return a focused set of destination search results."""

        normalized_query = " ".join(query.split())
        normalized_destination = " ".join(destination.split())

        if not normalized_query or not normalized_destination:
            raise ProviderError("Both query and destination must be non-empty")

        safe_limit = max(1, min(int(result_limit), 10))

        if not self.search_api_key:
            return self._mock_search_result(
                query=normalized_query,
                destination=normalized_destination,
                result_limit=safe_limit,
            )

        headers = {"Authorization": f"Bearer {self.search_api_key}"}

        try:
            payload = self.http_client.get_json(
                self.endpoint,
                params={
                    "query": normalized_query,
                    "destination": normalized_destination,
                    "limit": safe_limit,
                },
                headers=headers,
            )
        except ProviderError:
            return self._mock_search_result(
                query=normalized_query,
                destination=normalized_destination,
                result_limit=safe_limit,
            )

        raw_results = payload.get("results") or payload.get("items") or payload.get("data")

        if raw_results is None:
            raise ProviderError("Destination search provider returned a malformed response")

        if not isinstance(raw_results, list):
            raise ProviderError("Destination search provider returned a malformed response")

        normalized_results: list[SearchResultItem] = []
        for index, result in enumerate(raw_results[:safe_limit], start=1):
            if not isinstance(result, dict):
                raise ProviderError("Destination search provider returned malformed search entries")

            title = str(
                result.get("title")
                or result.get("name")
                or result.get("headline")
                or f"Search result {index}"
            )
            url = str(result.get("url") or result.get("link") or "")
            snippet = str(
                result.get("snippet")
                or result.get("description")
                or result.get("summary")
                or "No summary provided by the upstream provider."
            )
            provider_name = str(result.get("provider") or "destination_search")

            normalized_results.append(
                SearchResultItem(
                    title=title,
                    url=url,
                    snippet=snippet,
                    provider=provider_name,
                    data_mode=DataMode.LIVE,
                )
            )

        if not normalized_results:
            raise ProviderError("Destination search provider returned no usable results")

        return DestinationSearchResult(
            query=normalized_query,
            destination=normalized_destination,
            results=normalized_results,
            warning=None,
            provider="destination_search",
            data_mode=DataMode.LIVE,
            source=SourceMetadata(
                provider="destination_search",
                data_mode=DataMode.LIVE,
                source_url=self.endpoint,
                is_estimate=False,
            ),
        )

    def _mock_search_result(
        self,
        *,
        query: str,
        destination: str,
        result_limit: int,
    ) -> DestinationSearchResult:
        """Return a deterministic mock result set that is clearly labelled as demo data."""

        warning = (
            "Demo destination search results are illustrative prototype data, not current "
            "researched facts."
        )
        results = [
            SearchResultItem(
                title=f"Prototype destination overview: {destination}",
                url="https://example.com/demo/destination",
                snippet=(
                    f"{destination} is a sample destination used for prototype planning. "
                    f"This result is demonstration data for development and testing only."
                ),
                provider="mock_destination_search",
                data_mode=DataMode.MOCK,
            )
            for _ in range(result_limit)
        ]

        return DestinationSearchResult(
            query=query,
            destination=destination,
            results=results,
            warning=warning,
            provider="mock_destination_search",
            data_mode=DataMode.MOCK,
            source=SourceMetadata(
                provider="mock_destination_search",
                data_mode=DataMode.MOCK,
                source_url=self.endpoint,
                is_estimate=True,
                message=(
                    "Mock destination-search results are demonstration data and not "
                    "current researched facts."
                ),
            ),
        )
