"""Shared test fixtures for trades service tests."""

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

import pytest


@dataclass
class MockRestApiResponse:
    """Mock for CompressedAggregateTradesListResponseInner."""

    a: int | None = None  # Aggregate trade ID
    p: str | None = None  # Price
    q: str | None = None  # Quantity
    T: int | None = None  # Timestamp ms
    m: bool | None = None  # Is buyer market maker


@dataclass
class MockWebSocketResponse:
    """Mock for AggregateTradeStreamsResponse."""

    e: str | None = None  # Event type
    E: int | None = None  # Event time
    s: str | None = None  # Symbol
    a: int | None = None  # Aggregate trade ID
    p: str | None = None  # Price
    q: str | None = None  # Quantity
    T: int | None = None  # Timestamp ms
    m: bool | None = None  # Is buyer market maker


@pytest.fixture
def mock_rest_api_response():
    """Create a mock REST API response."""
    return MockRestApiResponse(
        a=123456789,
        p="97500.50",
        q="0.123",
        T=1732636800000,  # 2024-11-26 16:00:00 UTC
        m=True,
    )


@pytest.fixture
def mock_websocket_response():
    """Create a mock WebSocket response."""
    return MockWebSocketResponse(
        e="aggTrade",
        E=1732636800000,
        s="BTCUSDT",
        a=123456789,
        p="97500.50",
        q="0.123",
        T=1732636800000,
        m=True,
    )


@pytest.fixture
def mock_rest_api_response_empty_fields():
    """Mock response with None/empty fields."""
    return MockRestApiResponse()


@pytest.fixture
def mock_websocket_response_empty_fields():
    """Mock response with None/empty fields."""
    return MockWebSocketResponse()


@pytest.fixture
def mock_settings():
    """Create mock Settings object."""
    settings = MagicMock()
    settings.product_ids = ["BTCUSDT", "ETHUSDT"]
    settings.kafka_broker_address = "localhost:9092"
    settings.kafka_topic_name = "test-trades"
    settings.live_or_historical = "live"
    settings.last_n_days = 30
    settings.binance_api_key = None
    settings.binance_api_secret = None
    settings.rest_api_timeout = 30000
    settings.rest_api_retries = 3
    settings.websocket_reconnect_delay = 5000
    return settings


@pytest.fixture
def mock_settings_historical(mock_settings):
    """Create mock Settings for historical mode."""
    mock_settings.live_or_historical = "historical"
    mock_settings.last_n_days = 7
    return mock_settings


@pytest.fixture
def mock_settings_with_credentials(mock_settings):
    """Create mock Settings with API credentials."""
    mock_settings.binance_api_key = "test_api_key"
    mock_settings.binance_api_secret = "test_api_secret"
    return mock_settings


@pytest.fixture
def mock_settings_single_symbol(mock_settings):
    """Create mock Settings with a single symbol."""
    mock_settings.product_ids = ["BTCUSDT"]
    return mock_settings


@pytest.fixture
def mock_settings_many_symbols(mock_settings):
    """Create mock Settings with many symbols."""
    mock_settings.product_ids = [
        "BTCUSDT",
        "ETHUSDT",
        "SOLUSDT",
        "BNBUSDT",
        "XRPUSDT",
        "DOGEUSDT",
        "ADAUSDT",
        "AVAXUSDT",
        "LINKUSDT",
        "DOTUSDT",
    ]
    return mock_settings


@pytest.fixture
def mock_kafka_producer():
    """Create a mock Kafka producer."""
    producer = MagicMock()
    producer.produce = MagicMock()
    producer.flush = MagicMock()
    producer.__enter__ = MagicMock(return_value=producer)
    producer.__exit__ = MagicMock(return_value=None)
    return producer


@pytest.fixture
def mock_kafka_topic():
    """Create a mock Kafka topic."""
    topic = MagicMock()
    topic.name = "test-trades"
    topic.serialize = MagicMock(
        return_value=MagicMock(
            value=b'{"product_id": "BTCUSDT", "price": 97500.50}',
            key=b"BTCUSDT",
        )
    )
    return topic


@pytest.fixture
def mock_kafka_app(mock_kafka_producer, mock_kafka_topic):
    """Create a mock Kafka Application."""
    app = MagicMock()
    app.topic = MagicMock(return_value=mock_kafka_topic)
    app.get_producer = MagicMock(return_value=mock_kafka_producer)
    return app


@pytest.fixture
def mock_sdk_rest_api():
    """Create a mock SDK REST API client."""
    rest_api = MagicMock()
    response = MagicMock()
    response.rate_limits = {"REQUEST_WEIGHT": {"limit": 2400, "used": 1}}
    response.data = MagicMock(
        return_value=[
            MockRestApiResponse(a=1, p="97500.00", q="0.1", T=1732636800000, m=True),
            MockRestApiResponse(a=2, p="97501.00", q="0.2", T=1732636801000, m=False),
        ]
    )
    rest_api.compressed_aggregate_trades_list = MagicMock(return_value=response)
    return rest_api


@pytest.fixture
def mock_sdk_websocket_streams():
    """Create a mock SDK WebSocket Streams client."""
    ws_streams = MagicMock()
    ws_streams.create_connection = AsyncMock()
    return ws_streams


@pytest.fixture
def mock_sdk_client(mock_sdk_rest_api, mock_sdk_websocket_streams):
    """Create a mock SDK DerivativesTradingUsdsFutures client."""
    client = MagicMock()
    client.rest_api = mock_sdk_rest_api
    client.websocket_streams = mock_sdk_websocket_streams
    return client


@pytest.fixture
def mock_websocket_connection():
    """Create a mock WebSocket connection."""
    connection = AsyncMock()
    stream = AsyncMock()
    stream.on = MagicMock()
    stream.unsubscribe = AsyncMock()
    connection.aggregate_trade_streams = AsyncMock(return_value=stream)
    connection.close_connection = AsyncMock()
    return connection


# Integration test fixtures (used by tests marked with @pytest.mark.integration)


@pytest.fixture
def real_settings():
    """Real settings for integration tests (requires env file)."""
    import os

    os.environ.setdefault("kafka_broker_address", "localhost:9092")
    os.environ.setdefault("kafka_topic_name", "test-trades")

    from trades.config import Settings

    return Settings(
        kafka_broker_address="localhost:9092",
        kafka_topic_name="test-trades",
        product_ids=["BTCUSDT"],
        live_or_historical="historical",
        last_n_days=1,
    )


@pytest.fixture
def real_historical_client(real_settings):
    """Real BinanceHistoricalClient for integration tests."""
    from trades.binance_client import BinanceHistoricalClient

    return BinanceHistoricalClient(real_settings)


@pytest.fixture
async def real_live_client(real_settings):
    """Real BinanceLiveClient for integration tests."""
    real_settings.live_or_historical = "live"

    from trades.binance_client import BinanceLiveClient

    client = BinanceLiveClient(real_settings)
    yield client
    if client._is_running:
        await client.stop()


# Helper fixtures


@pytest.fixture
def sample_trade():
    """Create a sample Trade object."""
    from trades.trade import Trade

    return Trade(
        product_id="BTCUSDT",
        price=97500.50,
        quantity=0.123,
        timestamp="2024-11-26T16:00:00Z",
        timestamp_ms=1732636800000,
    )


@pytest.fixture
def sample_trades(sample_trade):
    """Create a list of sample Trade objects."""
    from trades.trade import Trade

    return [
        sample_trade,
        Trade(
            product_id="ETHUSDT",
            price=3500.25,
            quantity=1.5,
            timestamp="2024-11-26T16:00:01Z",
            timestamp_ms=1732636801000,
        ),
        Trade(
            product_id="SOLUSDT",
            price=250.75,
            quantity=10.0,
            timestamp="2024-11-26T16:00:02Z",
            timestamp_ms=1732636802000,
        ),
    ]


@pytest.fixture
def env_vars():
    """Context manager for setting environment variables."""
    import os
    from contextlib import contextmanager

    @contextmanager
    def _set_env(**kwargs):
        old_values = {}
        for key, value in kwargs.items():
            old_values[key] = os.environ.get(key)
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        try:
            yield
        finally:
            for key, old_value in old_values.items():
                if old_value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = old_value

    return _set_env
