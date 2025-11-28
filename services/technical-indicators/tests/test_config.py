"""Tests for technical indicators configuration."""

import pytest
from pydantic import ValidationError


class TestSettings:
    """Tests for Settings class."""

    def test_settings_from_env(self, mock_env_vars):
        """Test that settings load from environment variables."""
        from technical_indicators.config import Settings

        settings = Settings()

        assert settings.kafka_broker_address == "localhost:9092"
        assert settings.kafka_input_topic == "candles"
        assert settings.kafka_output_topic == "technical_indicators"
        assert settings.kafka_consumer_group == "test-group"
        assert settings.candle_seconds == 60

    def test_settings_defaults(self, monkeypatch):
        """Test default values."""
        monkeypatch.setenv("KAFKA_BROKER_ADDRESS", "localhost:9092")

        from technical_indicators.config import Settings

        settings = Settings(_env_file=None)

        assert settings.kafka_input_topic == "candles"
        assert settings.kafka_output_topic == "technical_indicators"
        assert settings.kafka_consumer_group == "technical-indicators-group"
        assert settings.candle_seconds == 60

    def test_settings_missing_required(self, monkeypatch):
        """Test that missing required fields raise validation error."""
        monkeypatch.delenv("KAFKA_BROKER_ADDRESS", raising=False)

        from technical_indicators.config import Settings

        with pytest.raises(ValidationError):
            Settings(_env_file=None)


class TestLoadIndicatorsConfig:
    """Tests for load_indicators_config function."""

    def test_load_config_from_service_dir(self):
        """Test loading config from service directory."""
        from technical_indicators.config import load_indicators_config

        config = load_indicators_config("indicators.yaml")

        assert "indicators" in config
        assert "max_candles" in config
        assert config["indicators"]["sma"]["enabled"] is True
        assert 7 in config["indicators"]["sma"]["periods"]
