"""Tests for candles service configuration."""

import pytest
from pydantic import ValidationError


class TestSettings:
    """Tests for Settings class."""

    def test_settings_from_env(self, mock_env_vars):
        """Test that settings load from environment variables."""
        from candles.config import Settings

        settings = Settings()

        assert settings.kafka_broker_address == "localhost:9092"
        assert settings.kafka_input_topic == "trades"
        assert settings.kafka_output_topic == "candles"
        assert settings.kafka_consumer_group == "test-group"
        assert settings.candle_seconds == 60

    def test_settings_missing_required(self, monkeypatch):
        """Test that missing required fields raise validation error."""
        # Clear all env vars
        monkeypatch.delenv("KAFKA_BROKER_ADDRESS", raising=False)
        monkeypatch.delenv("KAFKA_INPUT_TOPIC", raising=False)
        monkeypatch.delenv("KAFKA_OUTPUT_TOPIC", raising=False)
        monkeypatch.delenv("KAFKA_CONSUMER_GROUP", raising=False)

        from candles.config import Settings

        with pytest.raises(ValidationError):
            Settings(_env_file=None)

    def test_candle_seconds_default(self, monkeypatch):
        """Test that candle_seconds has a default value."""
        monkeypatch.setenv("KAFKA_BROKER_ADDRESS", "localhost:9092")
        monkeypatch.setenv("KAFKA_INPUT_TOPIC", "trades")
        monkeypatch.setenv("KAFKA_OUTPUT_TOPIC", "candles")
        monkeypatch.setenv("KAFKA_CONSUMER_GROUP", "test-group")
        # Don't set CANDLE_SECONDS

        from candles.config import Settings

        settings = Settings(_env_file=None)
        assert settings.candle_seconds == 60

    def test_candle_seconds_custom(self, monkeypatch):
        """Test that candle_seconds can be customized."""
        monkeypatch.setenv("KAFKA_BROKER_ADDRESS", "localhost:9092")
        monkeypatch.setenv("KAFKA_INPUT_TOPIC", "trades")
        monkeypatch.setenv("KAFKA_OUTPUT_TOPIC", "candles")
        monkeypatch.setenv("KAFKA_CONSUMER_GROUP", "test-group")
        monkeypatch.setenv("CANDLE_SECONDS", "300")

        from candles.config import Settings

        settings = Settings(_env_file=None)
        assert settings.candle_seconds == 300
