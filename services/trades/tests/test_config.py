"""Tests for trades.config module."""

import pytest
from pydantic import ValidationError


class TestSettingsDefaults:
    """Test default values for Settings."""

    def test_default_product_ids(self, env_vars):
        """Test default product_ids list."""
        with env_vars(
            kafka_broker_address="localhost:9092",
            kafka_topic_name="trades",
        ):
            from trades.config import Settings

            settings = Settings(
                kafka_broker_address="localhost:9092",
                kafka_topic_name="trades",
            )
            assert len(settings.product_ids) == 10
            assert "BTCUSDT" in settings.product_ids
            assert "ETHUSDT" in settings.product_ids

    def test_default_live_or_historical(self, env_vars):
        """Test default live_or_historical is 'live'."""
        with env_vars(
            kafka_broker_address="localhost:9092",
            kafka_topic_name="trades",
        ):
            from trades.config import Settings

            settings = Settings(
                kafka_broker_address="localhost:9092",
                kafka_topic_name="trades",
            )
            assert settings.live_or_historical == "live"

    def test_default_last_n_days(self, env_vars):
        """Test default last_n_days is 30."""
        with env_vars(
            kafka_broker_address="localhost:9092",
            kafka_topic_name="trades",
        ):
            from trades.config import Settings

            settings = Settings(
                kafka_broker_address="localhost:9092",
                kafka_topic_name="trades",
            )
            assert settings.last_n_days == 30

    def test_default_binance_credentials_none(self, env_vars):
        """Test default binance credentials are None."""
        with env_vars(
            kafka_broker_address="localhost:9092",
            kafka_topic_name="trades",
        ):
            from trades.config import Settings

            settings = Settings(
                kafka_broker_address="localhost:9092",
                kafka_topic_name="trades",
            )
            assert settings.binance_api_key is None
            assert settings.binance_api_secret is None

    def test_default_rest_api_timeout(self, env_vars):
        """Test default REST API timeout is 30000ms."""
        with env_vars(
            kafka_broker_address="localhost:9092",
            kafka_topic_name="trades",
        ):
            from trades.config import Settings

            settings = Settings(
                kafka_broker_address="localhost:9092",
                kafka_topic_name="trades",
            )
            assert settings.rest_api_timeout == 30000

    def test_default_rest_api_retries(self, env_vars):
        """Test default REST API retries is 3."""
        with env_vars(
            kafka_broker_address="localhost:9092",
            kafka_topic_name="trades",
        ):
            from trades.config import Settings

            settings = Settings(
                kafka_broker_address="localhost:9092",
                kafka_topic_name="trades",
            )
            assert settings.rest_api_retries == 3

    def test_default_websocket_reconnect_delay(self, env_vars):
        """Test default WebSocket reconnect delay is 5000ms."""
        with env_vars(
            kafka_broker_address="localhost:9092",
            kafka_topic_name="trades",
        ):
            from trades.config import Settings

            settings = Settings(
                kafka_broker_address="localhost:9092",
                kafka_topic_name="trades",
            )
            assert settings.websocket_reconnect_delay == 5000


class TestSettingsLoading:
    """Test settings loading from various sources."""

    def test_load_from_env_variables(self, env_vars):
        """Test loading from environment variables."""
        with env_vars(
            kafka_broker_address="kafka.example.com:9093",
            kafka_topic_name="my-trades",
            live_or_historical="historical",
            last_n_days="7",
        ):
            from trades.config import Settings

            settings = Settings()
            assert settings.kafka_broker_address == "kafka.example.com:9093"
            assert settings.kafka_topic_name == "my-trades"
            assert settings.live_or_historical == "historical"
            assert settings.last_n_days == 7

    def test_env_override_explicit_values(self, env_vars):
        """Test environment variables override explicit values."""
        with env_vars(
            kafka_broker_address="from-env:9092",
            kafka_topic_name="from-env-topic",
        ):
            from trades.config import Settings

            # Environment variables should be used when creating without explicit args
            settings = Settings()
            assert settings.kafka_broker_address == "from-env:9092"
            assert settings.kafka_topic_name == "from-env-topic"

    def test_load_binance_credentials_from_env(self, env_vars):
        """Test loading Binance credentials from environment."""
        with env_vars(
            kafka_broker_address="localhost:9092",
            kafka_topic_name="trades",
            binance_api_key="my_api_key",
            binance_api_secret="my_api_secret",
        ):
            from trades.config import Settings

            settings = Settings()
            assert settings.binance_api_key == "my_api_key"
            assert settings.binance_api_secret == "my_api_secret"

    def test_load_sdk_config_from_env(self, env_vars):
        """Test loading SDK configuration from environment."""
        with env_vars(
            kafka_broker_address="localhost:9092",
            kafka_topic_name="trades",
            rest_api_timeout="60000",
            rest_api_retries="5",
            websocket_reconnect_delay="10000",
        ):
            from trades.config import Settings

            settings = Settings()
            assert settings.rest_api_timeout == 60000
            assert settings.rest_api_retries == 5
            assert settings.websocket_reconnect_delay == 10000


class TestSettingsValidation:
    """Test settings validation."""

    def test_missing_kafka_broker_address_raises(self, env_vars):
        """Test missing kafka_broker_address raises error."""
        with env_vars(
            kafka_broker_address=None,
            kafka_topic_name="trades",
        ):
            from trades.config import Settings

            with pytest.raises(ValidationError) as exc_info:
                Settings(kafka_topic_name="trades")
            assert "kafka_broker_address" in str(exc_info.value)

    def test_missing_kafka_topic_name_raises(self, env_vars):
        """Test missing kafka_topic_name raises error."""
        with env_vars(
            kafka_broker_address="localhost:9092",
            kafka_topic_name=None,
        ):
            from trades.config import Settings

            with pytest.raises(ValidationError) as exc_info:
                Settings(kafka_broker_address="localhost:9092")
            assert "kafka_topic_name" in str(exc_info.value)

    def test_valid_live_mode(self, env_vars):
        """Test 'live' is valid for live_or_historical."""
        with env_vars(
            kafka_broker_address="localhost:9092",
            kafka_topic_name="trades",
        ):
            from trades.config import Settings

            settings = Settings(
                kafka_broker_address="localhost:9092",
                kafka_topic_name="trades",
                live_or_historical="live",
            )
            assert settings.live_or_historical == "live"

    def test_valid_historical_mode(self, env_vars):
        """Test 'historical' is valid for live_or_historical."""
        with env_vars(
            kafka_broker_address="localhost:9092",
            kafka_topic_name="trades",
        ):
            from trades.config import Settings

            settings = Settings(
                kafka_broker_address="localhost:9092",
                kafka_topic_name="trades",
                live_or_historical="historical",
            )
            assert settings.live_or_historical == "historical"

    def test_invalid_live_or_historical_raises(self, env_vars):
        """Test invalid live_or_historical value raises error."""
        with env_vars(
            kafka_broker_address="localhost:9092",
            kafka_topic_name="trades",
        ):
            from trades.config import Settings

            with pytest.raises(ValidationError) as exc_info:
                Settings(
                    kafka_broker_address="localhost:9092",
                    kafka_topic_name="trades",
                    live_or_historical="invalid",
                )
            assert "live_or_historical" in str(exc_info.value)

    def test_last_n_days_positive_integer(self, env_vars):
        """Test last_n_days accepts positive integer."""
        with env_vars(
            kafka_broker_address="localhost:9092",
            kafka_topic_name="trades",
        ):
            from trades.config import Settings

            settings = Settings(
                kafka_broker_address="localhost:9092",
                kafka_topic_name="trades",
                last_n_days=365,
            )
            assert settings.last_n_days == 365

    def test_custom_product_ids_list(self, env_vars):
        """Test custom product_ids list."""
        with env_vars(
            kafka_broker_address="localhost:9092",
            kafka_topic_name="trades",
        ):
            from trades.config import Settings

            settings = Settings(
                kafka_broker_address="localhost:9092",
                kafka_topic_name="trades",
                product_ids=["BTCUSDT", "ETHUSDT", "SOLUSDT"],
            )
            assert settings.product_ids == ["BTCUSDT", "ETHUSDT", "SOLUSDT"]


class TestSettingsEdgeCases:
    """Test edge cases for Settings."""

    def test_empty_product_ids_list(self, env_vars):
        """Test empty product_ids list is allowed."""
        with env_vars(
            kafka_broker_address="localhost:9092",
            kafka_topic_name="trades",
        ):
            from trades.config import Settings

            settings = Settings(
                kafka_broker_address="localhost:9092",
                kafka_topic_name="trades",
                product_ids=[],
            )
            assert settings.product_ids == []

    def test_single_product_id(self, env_vars):
        """Test single product_id in list."""
        with env_vars(
            kafka_broker_address="localhost:9092",
            kafka_topic_name="trades",
        ):
            from trades.config import Settings

            settings = Settings(
                kafka_broker_address="localhost:9092",
                kafka_topic_name="trades",
                product_ids=["BTCUSDT"],
            )
            assert settings.product_ids == ["BTCUSDT"]

    def test_very_large_last_n_days(self, env_vars):
        """Test very large last_n_days value."""
        with env_vars(
            kafka_broker_address="localhost:9092",
            kafka_topic_name="trades",
        ):
            from trades.config import Settings

            settings = Settings(
                kafka_broker_address="localhost:9092",
                kafka_topic_name="trades",
                last_n_days=3650,  # 10 years
            )
            assert settings.last_n_days == 3650

    def test_zero_timeout_value(self, env_vars):
        """Test zero timeout value."""
        with env_vars(
            kafka_broker_address="localhost:9092",
            kafka_topic_name="trades",
        ):
            from trades.config import Settings

            settings = Settings(
                kafka_broker_address="localhost:9092",
                kafka_topic_name="trades",
                rest_api_timeout=0,
            )
            assert settings.rest_api_timeout == 0

    def test_zero_retries_value(self, env_vars):
        """Test zero retries value."""
        with env_vars(
            kafka_broker_address="localhost:9092",
            kafka_topic_name="trades",
        ):
            from trades.config import Settings

            settings = Settings(
                kafka_broker_address="localhost:9092",
                kafka_topic_name="trades",
                rest_api_retries=0,
            )
            assert settings.rest_api_retries == 0

    def test_special_characters_in_topic_name(self, env_vars):
        """Test special characters in topic name."""
        with env_vars(
            kafka_broker_address="localhost:9092",
            kafka_topic_name="trades",
        ):
            from trades.config import Settings

            settings = Settings(
                kafka_broker_address="localhost:9092",
                kafka_topic_name="trades-v2_test.topic",
            )
            assert settings.kafka_topic_name == "trades-v2_test.topic"

    def test_ipv6_broker_address(self, env_vars):
        """Test IPv6 broker address."""
        with env_vars(
            kafka_broker_address="localhost:9092",
            kafka_topic_name="trades",
        ):
            from trades.config import Settings

            settings = Settings(
                kafka_broker_address="[::1]:9092",
                kafka_topic_name="trades",
            )
            assert settings.kafka_broker_address == "[::1]:9092"

    def test_multiple_brokers_address(self, env_vars):
        """Test multiple brokers in address."""
        with env_vars(
            kafka_broker_address="localhost:9092",
            kafka_topic_name="trades",
        ):
            from trades.config import Settings

            settings = Settings(
                kafka_broker_address="broker1:9092,broker2:9092,broker3:9092",
                kafka_topic_name="trades",
            )
            assert (
                settings.kafka_broker_address
                == "broker1:9092,broker2:9092,broker3:9092"
            )

    def test_api_key_with_special_characters(self, env_vars):
        """Test API key with special characters."""
        with env_vars(
            kafka_broker_address="localhost:9092",
            kafka_topic_name="trades",
        ):
            from trades.config import Settings

            settings = Settings(
                kafka_broker_address="localhost:9092",
                kafka_topic_name="trades",
                binance_api_key="key_with-special.chars123",
            )
            assert settings.binance_api_key == "key_with-special.chars123"

    def test_api_secret_with_special_characters(self, env_vars):
        """Test API secret with special characters."""
        with env_vars(
            kafka_broker_address="localhost:9092",
            kafka_topic_name="trades",
        ):
            from trades.config import Settings

            settings = Settings(
                kafka_broker_address="localhost:9092",
                kafka_topic_name="trades",
                binance_api_secret="secret_with-special.chars123!@#",
            )
            assert settings.binance_api_secret == "secret_with-special.chars123!@#"

    def test_last_n_days_one(self, env_vars):
        """Test last_n_days = 1."""
        with env_vars(
            kafka_broker_address="localhost:9092",
            kafka_topic_name="trades",
        ):
            from trades.config import Settings

            settings = Settings(
                kafka_broker_address="localhost:9092",
                kafka_topic_name="trades",
                last_n_days=1,
            )
            assert settings.last_n_days == 1

    def test_lowercase_product_ids(self, env_vars):
        """Test lowercase product_ids are accepted."""
        with env_vars(
            kafka_broker_address="localhost:9092",
            kafka_topic_name="trades",
        ):
            from trades.config import Settings

            settings = Settings(
                kafka_broker_address="localhost:9092",
                kafka_topic_name="trades",
                product_ids=["btcusdt", "ethusdt"],
            )
            assert settings.product_ids == ["btcusdt", "ethusdt"]

    def test_mixed_case_product_ids(self, env_vars):
        """Test mixed case product_ids are accepted."""
        with env_vars(
            kafka_broker_address="localhost:9092",
            kafka_topic_name="trades",
        ):
            from trades.config import Settings

            settings = Settings(
                kafka_broker_address="localhost:9092",
                kafka_topic_name="trades",
                product_ids=["BtcUsdt", "EthUsdt"],
            )
            assert settings.product_ids == ["BtcUsdt", "EthUsdt"]


class TestSettingsType:
    """Test Settings type coercion."""

    def test_last_n_days_string_to_int(self, env_vars):
        """Test last_n_days string is converted to int."""
        with env_vars(
            kafka_broker_address="localhost:9092",
            kafka_topic_name="trades",
            last_n_days="15",
        ):
            from trades.config import Settings

            settings = Settings()
            assert settings.last_n_days == 15
            assert isinstance(settings.last_n_days, int)

    def test_timeout_string_to_int(self, env_vars):
        """Test timeout string is converted to int."""
        with env_vars(
            kafka_broker_address="localhost:9092",
            kafka_topic_name="trades",
            rest_api_timeout="45000",
        ):
            from trades.config import Settings

            settings = Settings()
            assert settings.rest_api_timeout == 45000
            assert isinstance(settings.rest_api_timeout, int)

    def test_retries_string_to_int(self, env_vars):
        """Test retries string is converted to int."""
        with env_vars(
            kafka_broker_address="localhost:9092",
            kafka_topic_name="trades",
            rest_api_retries="5",
        ):
            from trades.config import Settings

            settings = Settings()
            assert settings.rest_api_retries == 5
            assert isinstance(settings.rest_api_retries, int)
