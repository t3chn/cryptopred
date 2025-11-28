"""Tests for LunarCrush API client."""

import pytest
import respx
from httpx import Response
from lunarcrush.client import AuthenticationError, LunarCrushClient, LunarCrushError
from lunarcrush.models import CoinTimeSeries, LunarCrushMetric


class TestLunarCrushClient:
    """Tests for LunarCrushClient."""

    @pytest.fixture
    def client(self) -> LunarCrushClient:
        """Create test client."""
        return LunarCrushClient(
            api_key="test_api_key",
            base_url="https://lunarcrush.com/api4",
            timeout=10,
            requests_per_minute=60,
        )

    @respx.mock
    async def test_get_coin_time_series_success(
        self, client: LunarCrushClient, sample_coin_time_series_response: dict
    ):
        """Test successful coin time series fetch."""
        respx.get("https://lunarcrush.com/api4/public/coins/BTC/time-series/v2").mock(
            return_value=Response(200, json=sample_coin_time_series_response)
        )

        async with client:
            result = await client.get_coin_time_series("BTC", bucket="hour")

        assert len(result) == 2
        assert isinstance(result[0], CoinTimeSeries)
        assert result[0].time == 1763424000
        assert result[0].sentiment == 75
        assert result[0].galaxy_score == 53
        assert result[0].close == 91913

    @respx.mock
    async def test_get_coin_time_series_with_time_range(
        self, client: LunarCrushClient, sample_coin_time_series_response: dict
    ):
        """Test coin time series with start/end parameters."""
        route = respx.get("https://lunarcrush.com/api4/public/coins/ETH/time-series/v2").mock(
            return_value=Response(200, json=sample_coin_time_series_response)
        )

        async with client:
            await client.get_coin_time_series(
                "ETH",
                bucket="hour",
                start=1763424000,
                end=1764115200,
            )

        assert route.called
        request = route.calls[0].request
        assert "start=1763424000" in str(request.url)
        assert "end=1764115200" in str(request.url)

    @respx.mock
    async def test_get_topic_time_series_success(
        self, client: LunarCrushClient, sample_topic_time_series_response: dict
    ):
        """Test successful topic time series fetch."""
        respx.get("https://lunarcrush.com/api4/public/topic/bitcoin/time-series/v2").mock(
            return_value=Response(200, json=sample_topic_time_series_response)
        )

        async with client:
            result = await client.get_topic_time_series("bitcoin", bucket="hour")

        assert len(result) == 1
        assert result[0].time == 1763424000
        assert result[0].sentiment == 75

    @respx.mock
    async def test_authentication_error(self, client: LunarCrushClient):
        """Test authentication error handling."""
        respx.get("https://lunarcrush.com/api4/public/coins/BTC/time-series/v2").mock(
            return_value=Response(401, json={"error": "Invalid API key"})
        )

        async with client:
            with pytest.raises(AuthenticationError, match="Invalid API key"):
                await client.get_coin_time_series("BTC")

    @respx.mock
    async def test_rate_limit_retry(
        self, client: LunarCrushClient, sample_coin_time_series_response: dict
    ):
        """Test rate limit handling with retry."""
        route = respx.get("https://lunarcrush.com/api4/public/coins/BTC/time-series/v2")
        route.side_effect = [
            Response(429, headers={"Retry-After": "1"}),
            Response(200, json=sample_coin_time_series_response),
        ]

        async with client:
            result = await client.get_coin_time_series("BTC")

        assert len(result) == 2
        assert route.call_count == 2

    @respx.mock
    async def test_server_error_retry(
        self, client: LunarCrushClient, sample_coin_time_series_response: dict
    ):
        """Test server error handling with retry."""
        route = respx.get("https://lunarcrush.com/api4/public/coins/BTC/time-series/v2")
        route.side_effect = [
            Response(500, json={"error": "Internal server error"}),
            Response(200, json=sample_coin_time_series_response),
        ]

        async with client:
            result = await client.get_coin_time_series("BTC")

        assert len(result) == 2

    @respx.mock
    async def test_max_retries_exceeded(self, client: LunarCrushClient):
        """Test that max retries raises error."""
        respx.get("https://lunarcrush.com/api4/public/coins/BTC/time-series/v2").mock(
            return_value=Response(500, json={"error": "Server error"})
        )

        async with client:
            with pytest.raises(LunarCrushError, match="Failed after 3 retries"):
                await client.get_coin_time_series("BTC")


class TestLunarCrushMetric:
    """Tests for LunarCrushMetric model."""

    def test_from_coin_time_series(self, sample_coin_time_series_response: dict):
        """Test creating metric from CoinTimeSeries."""
        ts_data = sample_coin_time_series_response["data"][0]
        ts = CoinTimeSeries.model_validate(ts_data)

        metric = LunarCrushMetric.from_coin_time_series("BTC", ts)

        assert metric.coin == "BTC"
        assert metric.time == 1763424000
        assert metric.time_ms == 1763424000000
        assert metric.sentiment == 75
        assert metric.galaxy_score == 53
        assert metric.alt_rank == 150
        assert metric.interactions == 5075541
        assert metric.social_dominance == 37.7476

    def test_metric_serialization(self):
        """Test metric serialization for Kafka."""
        metric = LunarCrushMetric(
            coin="ETH",
            time=1763424000,
            time_ms=1763424000000,
            sentiment=80.5,
            galaxy_score=65.0,
            alt_rank=5,
            interactions=1000000,
        )

        data = metric.model_dump()

        assert data["coin"] == "ETH"
        assert data["sentiment"] == 80.5
        assert data["galaxy_score"] == 65.0
        assert "time" in data
        assert "time_ms" in data
