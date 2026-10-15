"""Destination search provider with live and mock fallback handling."""

from __future__ import annotations

import threading
import time
from typing import Any, ClassVar

import httpx

from smart_travel_planner.config.settings import get_settings
from smart_travel_planner.models.provider_results import (
    DataMode,
    DestinationSearchResult,
    SearchResultItem,
    SourceMetadata,
)
from smart_travel_planner.utils.exceptions import ProviderError

_TAVILY_ENDPOINT = "https://api.tavily.com/search"
_CACHE_TTL_SECONDS = 12 * 60 * 60


class DestinationSearchProvider:
    """Search Tavily once per destination/interests, with cached mock fallback."""

    _cache: ClassVar[dict[tuple[str, tuple[str, ...]], tuple[float, DestinationSearchResult]]] = {}
    _cache_lock: ClassVar[threading.Lock] = threading.Lock()

    def __init__(
        self,
        http_client: Any | None = None,
        endpoint: str | None = None,
    ) -> None:
        settings = get_settings()
        self.http_client = http_client or httpx
        self.endpoint = endpoint or _TAVILY_ENDPOINT
        self.timeout = min(getattr(settings, "request_timeout_seconds", 20), 30)
        self.search_api_key = (
            settings.search_api_key.get_secret_value() if settings.search_api_key else None
        )

    def search(
        self,
        query: str,
        destination: str,
        result_limit: int = 5,
        interests: list[str] | None = None,
    ) -> DestinationSearchResult:
        """Return live Tavily results when possible, otherwise deterministic mock results."""

        normalized_destination = " ".join(destination.split())
        normalized_interests = tuple(
            sorted(
                {
                    " ".join(interest.split()).casefold()
                    for interest in (interests or [])
                    if interest.strip()
                }
            )
        )

        if not query.strip() or not normalized_destination:
            raise ProviderError("Both query and destination must be non-empty")

        safe_limit = max(1, min(int(result_limit), 8))
        normalized_query = self._build_query(normalized_destination, normalized_interests)

        cache_key = (normalized_destination.casefold(), normalized_interests)
        cached_result = self._get_cached(cache_key)
        expected_mode = DataMode.LIVE if self.search_api_key else DataMode.MOCK
        if cached_result is not None and cached_result.data_mode == expected_mode:
            return cached_result

        if not self.search_api_key:
            return self._cache_fallback(
                cache_key,
                query=normalized_query,
                destination=normalized_destination,
                result_limit=safe_limit,
            )

        payload = self._request_tavily(normalized_query)
        if payload is None:
            return self._cache_fallback(
                cache_key,
                query=normalized_query,
                destination=normalized_destination,
                result_limit=safe_limit,
            )

        raw_results = payload.get("results")
        if not isinstance(raw_results, list):
            return self._cache_fallback(
                cache_key,
                query=normalized_query,
                destination=normalized_destination,
                result_limit=safe_limit,
            )

        normalized_results: list[SearchResultItem] = []
        for result in raw_results[:safe_limit]:
            if not isinstance(result, dict):
                continue

            title = str(result.get("title") or result.get("name") or result.get("headline") or "")
            url = str(result.get("url") or result.get("link") or "")
            snippet = str(
                result.get("snippet")
                or result.get("content")
                or result.get("description")
                or result.get("summary")
                or ""
            )
            if not title.strip() or not url.lower().startswith(("http://", "https://")):
                continue

            normalized_results.append(
                SearchResultItem(
                    title=title,
                    url=url,
                    snippet=snippet or "No description provided by the source.",
                    provider="tavily",
                    data_mode=DataMode.LIVE,
                )
            )

        if not normalized_results:
            return self._cache_fallback(
                cache_key,
                query=normalized_query,
                destination=normalized_destination,
                result_limit=safe_limit,
            )

        result = DestinationSearchResult(
            query=normalized_query,
            destination=normalized_destination,
            results=normalized_results,
            warning=None,
            provider="destination_search",
            data_mode=DataMode.LIVE,
            source=SourceMetadata(
                provider="tavily",
                data_mode=DataMode.LIVE,
                source_url=self.endpoint,
                is_estimate=False,
            ),
        )
        self._set_cached(cache_key, result)
        return result.model_copy(deep=True)

    def _cache_fallback(
        self,
        cache_key: tuple[str, tuple[str, ...]],
        *,
        query: str,
        destination: str,
        result_limit: int,
    ) -> DestinationSearchResult:
        result = self._mock_search_result(
            query=query,
            destination=destination,
            result_limit=result_limit,
        )
        self._set_cached(cache_key, result)
        return result.model_copy(deep=True)

    @staticmethod
    def _build_query(destination: str, interests: tuple[str, ...]) -> str:
        interest_text = f"; interests: {', '.join(interests)}" if interests else ""
        return (
            f"{destination}{interest_text}; top attractions, local cultural "
            "experiences, local food experiences, markets, and practical transport guidance"
        )

    def _request_tavily(self, query: str) -> dict[str, Any] | None:
        headers = {
            "Authorization": f"Bearer {self.search_api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "query": query,
            "search_depth": "basic",
            "topic": "general",
            "max_results": 8,
            "include_answer": False,
            "include_raw_content": False,
            "include_images": False,
            "auto_parameters": False,
        }

        for attempt in range(2):
            try:
                response = self.http_client.post(
                    self.endpoint,
                    headers=headers,
                    json=body,
                    timeout=self.timeout,
                )
            except (httpx.TimeoutException, httpx.TransportError, TimeoutError, OSError):
                if attempt == 0:
                    continue
                return None
            except Exception:
                return None

            status_code = getattr(response, "status_code", 200)
            if status_code == 429 or status_code >= 500:
                if attempt == 0:
                    continue
                return None
            if status_code >= 400:
                return None

            try:
                payload = response.json() if hasattr(response, "json") else response
            except (ValueError, TypeError):
                return None
            return payload if isinstance(payload, dict) else None

        return None

    @classmethod
    def _get_cached(
        cls,
        key: tuple[str, tuple[str, ...]],
    ) -> DestinationSearchResult | None:
        now = time.monotonic()
        with cls._cache_lock:
            entry = cls._cache.get(key)
            if entry is None:
                return None
            created_at, result = entry
            if now - created_at >= _CACHE_TTL_SECONDS:
                del cls._cache[key]
                return None
            return result.model_copy(deep=True)

    @classmethod
    def _set_cached(
        cls,
        key: tuple[str, tuple[str, ...]],
        result: DestinationSearchResult,
    ) -> None:
        with cls._cache_lock:
            cls._cache[key] = (time.monotonic(), result.model_copy(deep=True))

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
