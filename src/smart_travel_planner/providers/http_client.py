"""Shared HTTP client with safe retries and normalized failures."""

import logging
import time
from collections.abc import Mapping
from typing import Any

import httpx

from smart_travel_planner.config.settings import get_settings
from smart_travel_planner.utils.exceptions import ProviderError

LOGGER = logging.getLogger(__name__)

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class SafeHttpClient:
    """Small synchronous HTTP client for external travel providers."""

    def __init__(
        self,
        timeout_seconds: int | None = None,
        max_attempts: int = 3,
    ) -> None:
        settings = get_settings()
        self.timeout_seconds = timeout_seconds or settings.request_timeout_seconds
        self.max_attempts = max(1, max_attempts)

    def get_json(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """Perform a GET request and return a validated JSON object."""

        last_error: Exception | None = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                with httpx.Client(
                    timeout=self.timeout_seconds,
                    follow_redirects=True,
                ) as client:
                    response = client.get(
                        url,
                        params=params,
                        headers=headers,
                    )

                if response.status_code in RETRYABLE_STATUS_CODES:
                    raise ProviderError(
                        f"Provider returned retryable status {response.status_code}"
                    )

                response.raise_for_status()
                payload = response.json()

                if not isinstance(payload, dict):
                    raise ProviderError("Provider response must be a JSON object")

                return payload

            except (
                httpx.TimeoutException,
                httpx.NetworkError,
                httpx.HTTPStatusError,
                ValueError,
                ProviderError,
            ) as exc:
                last_error = exc
                LOGGER.warning(
                    "Provider request failed: attempt=%s/%s error_type=%s",
                    attempt,
                    self.max_attempts,
                    type(exc).__name__,
                )

                if attempt < self.max_attempts:
                    time.sleep(min(attempt, 2))

        raise ProviderError(
            f"External provider request failed after {self.max_attempts} attempts"
        ) from last_error
