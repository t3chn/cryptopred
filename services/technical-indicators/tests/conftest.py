"""Pytest fixtures for technical indicators service tests."""

import pytest


@pytest.fixture
def sample_candle():
    """Single sample candle."""
    return {
        "pair": "BTCUSDT",
        "open": 50000.0,
        "high": 50500.0,
        "low": 49500.0,
        "close": 50200.0,
        "volume": 100.0,
        "window_start_ms": 1700000000000,
        "window_end_ms": 1700000060000,
        "candle_seconds": 60,
    }


@pytest.fixture
def sample_candles():
    """List of sample candles for indicator calculations."""
    base_time = 1700000000000
    candles = []

    # Generate 50 candles with realistic price movement
    prices = [
        50000,
        50100,
        50050,
        50200,
        50150,
        50300,
        50250,
        50400,
        50350,
        50500,
        50450,
        50600,
        50550,
        50700,
        50650,
        50800,
        50750,
        50900,
        50850,
        51000,
        50950,
        50800,
        50750,
        50600,
        50550,
        50400,
        50350,
        50200,
        50150,
        50000,
        49950,
        49800,
        49850,
        50000,
        50050,
        50200,
        50150,
        50300,
        50250,
        50400,
        50350,
        50500,
        50450,
        50600,
        50550,
        50700,
        50650,
        50800,
        50750,
        50900,
    ]

    for i, close in enumerate(prices):
        candles.append(
            {
                "pair": "BTCUSDT",
                "open": close - 50,
                "high": close + 100,
                "low": close - 100,
                "close": float(close),
                "volume": 100.0 + i * 10,
                "window_start_ms": base_time + i * 60000,
                "window_end_ms": base_time + (i + 1) * 60000,
                "candle_seconds": 60,
            }
        )

    return candles


@pytest.fixture
def indicators_config():
    """Sample indicators configuration."""
    return {
        "indicators": {
            "sma": {"enabled": True, "periods": [7, 14]},
            "ema": {"enabled": True, "periods": [7, 14]},
            "rsi": {"enabled": True, "periods": [14]},
            "macd": {"enabled": True, "fast": 12, "slow": 26, "signal": 9},
            "bbands": {"enabled": True, "period": 20, "std": 2.0},
            "stoch": {"enabled": True, "k": 14, "d": 3},
            "atr": {"enabled": True, "period": 14},
            "obv": {"enabled": True},
        },
        "max_candles": 100,
    }


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up environment variables for config testing."""
    monkeypatch.setenv("KAFKA_BROKER_ADDRESS", "localhost:9092")
    monkeypatch.setenv("KAFKA_INPUT_TOPIC", "candles")
    monkeypatch.setenv("KAFKA_OUTPUT_TOPIC", "technical_indicators")
    monkeypatch.setenv("KAFKA_CONSUMER_GROUP", "test-group")
    monkeypatch.setenv("CANDLE_SECONDS", "60")
