"""Pytest fixtures for candles service tests."""

import pytest


@pytest.fixture
def sample_trade():
    """Sample trade data."""
    return {
        "product_id": "BTCUSDT",
        "price": 50000.0,
        "quantity": 0.1,
        "timestamp_ms": 1700000000000,
    }


@pytest.fixture
def sample_trades():
    """Multiple sample trades for testing aggregation."""
    return [
        {
            "product_id": "BTCUSDT",
            "price": 50000.0,
            "quantity": 0.1,
            "timestamp_ms": 1700000000000,
        },
        {
            "product_id": "BTCUSDT",
            "price": 50100.0,
            "quantity": 0.2,
            "timestamp_ms": 1700000001000,
        },
        {
            "product_id": "BTCUSDT",
            "price": 49900.0,
            "quantity": 0.15,
            "timestamp_ms": 1700000002000,
        },
        {
            "product_id": "BTCUSDT",
            "price": 50050.0,
            "quantity": 0.05,
            "timestamp_ms": 1700000003000,
        },
    ]


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up environment variables for config testing."""
    monkeypatch.setenv("KAFKA_BROKER_ADDRESS", "localhost:9092")
    monkeypatch.setenv("KAFKA_INPUT_TOPIC", "trades")
    monkeypatch.setenv("KAFKA_OUTPUT_TOPIC", "candles")
    monkeypatch.setenv("KAFKA_CONSUMER_GROUP", "test-group")
    monkeypatch.setenv("CANDLE_SECONDS", "60")
