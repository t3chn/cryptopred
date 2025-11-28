"""Async HTTP client for LunarCrush API v4."""

import asyncio
import time
from typing import TYPE_CHECKING

import httpx
from loguru import logger

from lunarcrush.models import (
    CoinTimeSeries,
    CoinTimeSeriesResponse,
    TopicTimeSeries,
    TopicTimeSeriesResponse,
)

if TYPE_CHECKING:
    from lunarcrush.config import Settings


class LunarCrushError(Exception):
    """Base exception for LunarCrush API errors."""

    pass


class RateLimitError(LunarCrushError):
    """Raised when rate limit is exceeded."""

    pass


class AuthenticationError(LunarCrushError):
    """Raised when API key is invalid."""

    pass


class LunarCrushClient:
    """
    Async HTTP client for LunarCrush API v4.

    Features:
    - Async requests with httpx
    - Rate limit handling with exponential backoff
    - Automatic retry on transient errors
    - Pydantic model validation
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://lunarcrush.com/api4",
        timeout: int = 30,
        requests_per_minute: int = 30,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._requests_per_minute = requests_per_minute
        self._request_times: list[float] = []
        self._client: httpx.AsyncClient | None = None

    @classmethod
    def from_config(cls, config: "Settings") -> "LunarCrushClient":
        """Create client from Settings config."""
        return cls(
            api_key=config.lunarcrush_api_key,
            base_url=config.lunarcrush_base_url,
            timeout=config.request_timeout,
            requests_per_minute=config.requests_per_minute,
        )

    async def __aenter__(self) -> "LunarCrushClient":
        self._client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=self.timeout,
        )
        return self

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure client is initialized."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout,
            )
        return self._client

    async def _rate_limit(self):
        """Simple rate limiter to avoid hitting API limits."""
        now = time.time()
        # Remove requests older than 1 minute
        self._request_times = [t for t in self._request_times if now - t < 60]

        if len(self._request_times) >= self._requests_per_minute:
            # Wait until oldest request expires
            wait_time = 60 - (now - self._request_times[0]) + 0.1
            if wait_time > 0:
                logger.debug(f"Rate limiting: waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)

        self._request_times.append(time.time())

    async def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        retries: int = 3,
    ) -> dict:
        """Make HTTP request with retry logic."""
        await self._rate_limit()
        client = await self._ensure_client()

        url = f"{self.base_url}{path}"
        last_error = None

        for attempt in range(retries):
            try:
                response = await client.request(method, url, params=params)

                if response.status_code == 401:
                    raise AuthenticationError("Invalid API key")

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limited, waiting {retry_after}s")
                    await asyncio.sleep(retry_after)
                    continue

                response.raise_for_status()
                return response.json()

            except httpx.TimeoutException as e:
                last_error = e
                wait = 2**attempt
                logger.warning(f"Timeout on attempt {attempt + 1}, retrying in {wait}s")
                await asyncio.sleep(wait)

            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500:
                    last_error = e
                    wait = 2**attempt
                    logger.warning(f"Server error {e.response.status_code}, retrying in {wait}s")
                    await asyncio.sleep(wait)
                else:
                    raise LunarCrushError(f"HTTP error: {e}") from e

        raise LunarCrushError(f"Failed after {retries} retries: {last_error}")

    async def get_coin_time_series(
        self,
        coin: str,
        bucket: str = "hour",
        interval: str | None = None,
        start: int | None = None,
        end: int | None = None,
    ) -> list[CoinTimeSeries]:
        """
        Get historical time series data for a coin.

        Args:
            coin: Coin symbol (BTC, ETH) or numeric ID
            bucket: Time bucket - "hour" or "day"
            interval: Convenience interval like "1w", "1m" (ignored if start/end provided)
            start: Start unix timestamp (seconds)
            end: End unix timestamp (seconds)

        Returns:
            List of CoinTimeSeries data points
        """
        params: dict = {"bucket": bucket}
        if interval and not (start or end):
            params["interval"] = interval
        if start:
            params["start"] = start
        if end:
            params["end"] = end

        logger.debug(f"Fetching coin time series for {coin} with params {params}")
        data = await self._request("GET", f"/public/coins/{coin}/time-series/v2", params=params)

        response = CoinTimeSeriesResponse.model_validate(data)
        logger.info(f"Fetched {len(response.data)} data points for {coin}")
        return response.data

    async def get_topic_time_series(
        self,
        topic: str,
        bucket: str = "hour",
        interval: str | None = None,
        start: int | None = None,
        end: int | None = None,
    ) -> list[TopicTimeSeries]:
        """
        Get historical time series data for a social topic.

        Args:
            topic: Topic name in lowercase (bitcoin, ethereum)
            bucket: Time bucket - "hour" or "day"
            interval: Convenience interval like "1w", "1m"
            start: Start unix timestamp (seconds)
            end: End unix timestamp (seconds)

        Returns:
            List of TopicTimeSeries data points
        """
        params: dict = {"bucket": bucket}
        if interval and not (start or end):
            params["interval"] = interval
        if start:
            params["start"] = start
        if end:
            params["end"] = end

        logger.debug(f"Fetching topic time series for {topic} with params {params}")
        data = await self._request("GET", f"/public/topic/{topic}/time-series/v2", params=params)

        response = TopicTimeSeriesResponse.model_validate(data)
        logger.info(f"Fetched {len(response.data)} data points for topic {topic}")
        return response.data

    async def get_coins_list(
        self,
        sort: str = "market_cap_rank",
        limit: int = 100,
        desc: bool = True,
    ) -> list[dict]:
        """
        Get list of coins with current metrics.

        Args:
            sort: Sort field (market_cap_rank, galaxy_score, alt_rank, etc.)
            limit: Number of results (max 1000)
            desc: Sort descending

        Returns:
            List of coin data dictionaries
        """
        params = {"sort": sort, "limit": limit}
        if desc:
            params["desc"] = "true"

        data = await self._request("GET", "/public/coins/list/v2", params=params)
        return data.get("data", [])

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
