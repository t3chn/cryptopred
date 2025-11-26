"""Tests for trades.trade module."""

import datetime
from dataclasses import dataclass

import pytest

from trades.trade import Trade


class TestTradeModel:
    """Test Trade model creation and methods."""

    def test_create_trade_with_all_fields(self):
        """Test creating Trade with all fields."""
        trade = Trade(
            product_id="BTCUSDT",
            price=97500.50,
            quantity=0.123,
            timestamp="2024-11-26T16:00:00Z",
            timestamp_ms=1732636800000,
        )
        assert trade.product_id == "BTCUSDT"
        assert trade.price == 97500.50
        assert trade.quantity == 0.123
        assert trade.timestamp == "2024-11-26T16:00:00Z"
        assert trade.timestamp_ms == 1732636800000

    def test_to_dict_returns_dict(self, sample_trade):
        """Test to_dict returns dictionary."""
        result = sample_trade.to_dict()
        assert isinstance(result, dict)

    def test_to_dict_contains_all_fields(self, sample_trade):
        """Test to_dict contains all required fields."""
        result = sample_trade.to_dict()
        assert "product_id" in result
        assert "price" in result
        assert "quantity" in result
        assert "timestamp" in result
        assert "timestamp_ms" in result

    def test_to_dict_values_match(self, sample_trade):
        """Test to_dict values match original."""
        result = sample_trade.to_dict()
        assert result["product_id"] == sample_trade.product_id
        assert result["price"] == sample_trade.price
        assert result["quantity"] == sample_trade.quantity
        assert result["timestamp"] == sample_trade.timestamp
        assert result["timestamp_ms"] == sample_trade.timestamp_ms

    def test_model_dump_equals_to_dict(self, sample_trade):
        """Test model_dump equals to_dict."""
        assert sample_trade.model_dump() == sample_trade.to_dict()

    def test_trade_with_zero_price(self):
        """Test Trade with zero price."""
        trade = Trade(
            product_id="BTCUSDT",
            price=0.0,
            quantity=1.0,
            timestamp="2024-11-26T16:00:00Z",
            timestamp_ms=1732636800000,
        )
        assert trade.price == 0.0

    def test_trade_with_zero_quantity(self):
        """Test Trade with zero quantity."""
        trade = Trade(
            product_id="BTCUSDT",
            price=97500.50,
            quantity=0.0,
            timestamp="2024-11-26T16:00:00Z",
            timestamp_ms=1732636800000,
        )
        assert trade.quantity == 0.0

    def test_trade_with_very_large_price(self):
        """Test Trade with very large price."""
        trade = Trade(
            product_id="BTCUSDT",
            price=9999999999.99999999,
            quantity=1.0,
            timestamp="2024-11-26T16:00:00Z",
            timestamp_ms=1732636800000,
        )
        assert trade.price > 9999999999

    def test_trade_with_very_small_quantity(self):
        """Test Trade with very small quantity."""
        trade = Trade(
            product_id="BTCUSDT",
            price=97500.50,
            quantity=0.00000001,
            timestamp="2024-11-26T16:00:00Z",
            timestamp_ms=1732636800000,
        )
        assert trade.quantity == 0.00000001

    def test_trade_with_empty_product_id(self):
        """Test Trade with empty product_id."""
        trade = Trade(
            product_id="",
            price=97500.50,
            quantity=1.0,
            timestamp="2024-11-26T16:00:00Z",
            timestamp_ms=1732636800000,
        )
        assert trade.product_id == ""


class TestTimestampConversion:
    """Test timestamp conversion methods."""

    def test_unix_seconds_to_iso_format_normal(self):
        """Test normal timestamp conversion."""
        result = Trade.unix_seconds_to_iso_format(1732636800.0)
        assert "2024-11-26" in result
        assert result.endswith("Z")

    def test_unix_seconds_to_iso_format_epoch_zero(self):
        """Test epoch zero timestamp."""
        result = Trade.unix_seconds_to_iso_format(0)
        assert "1970-01-01" in result
        assert result.endswith("Z")

    def test_unix_seconds_to_iso_format_far_future(self):
        """Test far future timestamp."""
        # Year 2100
        result = Trade.unix_seconds_to_iso_format(4102444800.0)
        assert "2100-01-01" in result
        assert result.endswith("Z")

    def test_unix_seconds_to_iso_format_millisecond_precision(self):
        """Test millisecond precision is preserved."""
        result = Trade.unix_seconds_to_iso_format(1732636800.123456)
        assert "123456" in result or "123" in result  # Depending on formatting

    def test_unix_seconds_to_iso_format_negative(self):
        """Test negative timestamp (before epoch)."""
        result = Trade.unix_seconds_to_iso_format(-86400)  # 1 day before epoch
        assert "1969-12-31" in result

    def test_iso_format_to_unix_seconds_normal(self):
        """Test normal ISO to unix conversion."""
        result = Trade.iso_format_to_unix_seconds("2024-11-26T16:00:00Z")
        assert isinstance(result, float)
        assert result > 0

    def test_iso_format_to_unix_seconds_with_microseconds(self):
        """Test ISO with microseconds."""
        result = Trade.iso_format_to_unix_seconds("2024-11-26T16:00:00.123456Z")
        assert isinstance(result, float)

    def test_timestamp_roundtrip(self):
        """Test roundtrip conversion."""
        original = 1732636800.123
        iso = Trade.unix_seconds_to_iso_format(original)
        back = Trade.iso_format_to_unix_seconds(iso)
        assert abs(original - back) < 0.001  # Allow small floating point error

    def test_unix_seconds_to_iso_ends_with_z(self):
        """Test output always ends with Z."""
        result = Trade.unix_seconds_to_iso_format(1732636800.0)
        assert result.endswith("Z")
        assert "+00:00" not in result

    def test_unix_seconds_with_fractional_seconds(self):
        """Test timestamp with fractional seconds."""
        result = Trade.unix_seconds_to_iso_format(1732636800.5)
        assert isinstance(result, str)


class TestFromSdkRestApi:
    """Test Trade.from_sdk_rest_api factory method."""

    def test_from_sdk_rest_api_normal(self, mock_rest_api_response):
        """Test normal SDK REST API response parsing."""
        trade = Trade.from_sdk_rest_api("BTCUSDT", mock_rest_api_response)
        assert trade.product_id == "BTCUSDT"
        assert trade.price == 97500.50
        assert trade.quantity == 0.123
        assert trade.timestamp_ms == 1732636800000

    def test_from_sdk_rest_api_missing_timestamp(self, mock_rest_api_response_empty_fields):
        """Test SDK response with missing timestamp."""
        trade = Trade.from_sdk_rest_api("BTCUSDT", mock_rest_api_response_empty_fields)
        assert trade.timestamp_ms == 0

    def test_from_sdk_rest_api_missing_price(self, mock_rest_api_response_empty_fields):
        """Test SDK response with missing price."""
        trade = Trade.from_sdk_rest_api("BTCUSDT", mock_rest_api_response_empty_fields)
        assert trade.price == 0.0

    def test_from_sdk_rest_api_missing_quantity(self, mock_rest_api_response_empty_fields):
        """Test SDK response with missing quantity."""
        trade = Trade.from_sdk_rest_api("BTCUSDT", mock_rest_api_response_empty_fields)
        assert trade.quantity == 0.0

    def test_from_sdk_rest_api_empty_string_price(self):
        """Test SDK response with empty string price."""

        @dataclass
        class MockResponse:
            p: str = ""
            q: str = "1.0"
            T: int = 1732636800000

        trade = Trade.from_sdk_rest_api("BTCUSDT", MockResponse())
        assert trade.price == 0.0

    def test_from_sdk_rest_api_empty_string_quantity(self):
        """Test SDK response with empty string quantity."""

        @dataclass
        class MockResponse:
            p: str = "100.0"
            q: str = ""
            T: int = 1732636800000

        trade = Trade.from_sdk_rest_api("BTCUSDT", MockResponse())
        assert trade.quantity == 0.0

    def test_from_sdk_rest_api_very_large_price(self):
        """Test SDK response with very large price."""

        @dataclass
        class MockResponse:
            p: str = "99999999999999.99"
            q: str = "1.0"
            T: int = 1732636800000

        trade = Trade.from_sdk_rest_api("BTCUSDT", MockResponse())
        assert trade.price == 99999999999999.99

    def test_from_sdk_rest_api_very_small_quantity(self):
        """Test SDK response with very small quantity."""

        @dataclass
        class MockResponse:
            p: str = "100.0"
            q: str = "0.00000001"
            T: int = 1732636800000

        trade = Trade.from_sdk_rest_api("BTCUSDT", MockResponse())
        assert trade.quantity == 0.00000001

    def test_from_sdk_rest_api_product_id_preserved(self):
        """Test product_id is preserved from argument."""

        @dataclass
        class MockResponse:
            p: str = "100.0"
            q: str = "1.0"
            T: int = 1732636800000

        trade = Trade.from_sdk_rest_api("ETHUSDT", MockResponse())
        assert trade.product_id == "ETHUSDT"

    def test_from_sdk_rest_api_timestamp_converted(self, mock_rest_api_response):
        """Test timestamp is correctly converted to ISO format."""
        trade = Trade.from_sdk_rest_api("BTCUSDT", mock_rest_api_response)
        assert "2024-11-26" in trade.timestamp
        assert trade.timestamp.endswith("Z")


class TestFromSdkWebsocket:
    """Test Trade.from_sdk_websocket factory method."""

    def test_from_sdk_websocket_normal(self, mock_websocket_response):
        """Test normal SDK WebSocket response parsing."""
        trade = Trade.from_sdk_websocket(mock_websocket_response)
        assert trade.product_id == "BTCUSDT"
        assert trade.price == 97500.50
        assert trade.quantity == 0.123
        assert trade.timestamp_ms == 1732636800000

    def test_from_sdk_websocket_missing_symbol(self, mock_websocket_response_empty_fields):
        """Test SDK response with missing symbol."""
        trade = Trade.from_sdk_websocket(mock_websocket_response_empty_fields)
        assert trade.product_id == ""

    def test_from_sdk_websocket_missing_timestamp(self, mock_websocket_response_empty_fields):
        """Test SDK response with missing timestamp."""
        trade = Trade.from_sdk_websocket(mock_websocket_response_empty_fields)
        assert trade.timestamp_ms == 0

    def test_from_sdk_websocket_missing_price(self, mock_websocket_response_empty_fields):
        """Test SDK response with missing price."""
        trade = Trade.from_sdk_websocket(mock_websocket_response_empty_fields)
        assert trade.price == 0.0

    def test_from_sdk_websocket_missing_quantity(self, mock_websocket_response_empty_fields):
        """Test SDK response with missing quantity."""
        trade = Trade.from_sdk_websocket(mock_websocket_response_empty_fields)
        assert trade.quantity == 0.0

    def test_from_sdk_websocket_symbol_extracted(self, mock_websocket_response):
        """Test symbol is extracted from response."""
        trade = Trade.from_sdk_websocket(mock_websocket_response)
        assert trade.product_id == mock_websocket_response.s

    def test_from_sdk_websocket_timestamp_converted(self, mock_websocket_response):
        """Test timestamp is correctly converted."""
        trade = Trade.from_sdk_websocket(mock_websocket_response)
        assert trade.timestamp.endswith("Z")

    def test_from_sdk_websocket_with_none_values(self):
        """Test SDK response with all None values."""

        @dataclass
        class MockResponse:
            s: str | None = None
            p: str | None = None
            q: str | None = None
            T: int | None = None

        trade = Trade.from_sdk_websocket(MockResponse())
        assert trade.product_id == ""
        assert trade.price == 0.0
        assert trade.quantity == 0.0
        assert trade.timestamp_ms == 0


class TestLegacyMethods:
    """Test legacy factory methods for backwards compatibility."""

    def test_from_binance_websocket_response(self):
        """Test legacy WebSocket factory method."""
        trade = Trade.from_binance_websocket_response(
            product_id="BTCUSDT",
            price=97500.50,
            quantity=0.123,
            timestamp_ms=1732636800000,
        )
        assert trade.product_id == "BTCUSDT"
        assert trade.price == 97500.50
        assert trade.quantity == 0.123
        assert trade.timestamp_ms == 1732636800000

    def test_from_binance_rest_api_response(self):
        """Test legacy REST API factory method."""
        trade = Trade.from_binance_rest_api_response(
            product_id="ETHUSDT",
            price=3500.25,
            quantity=1.5,
            timestamp_ms=1732636800000,
        )
        assert trade.product_id == "ETHUSDT"
        assert trade.price == 3500.25
        assert trade.quantity == 1.5
        assert trade.timestamp_ms == 1732636800000

    def test_legacy_methods_produce_same_result(self):
        """Test legacy methods produce same result as direct construction."""
        args = {
            "product_id": "BTCUSDT",
            "price": 97500.50,
            "quantity": 0.123,
            "timestamp_ms": 1732636800000,
        }

        from_ws = Trade.from_binance_websocket_response(**args)
        from_rest = Trade.from_binance_rest_api_response(**args)

        assert from_ws.to_dict() == from_rest.to_dict()

    def test_legacy_timestamp_conversion(self):
        """Test legacy methods convert timestamp correctly."""
        trade = Trade.from_binance_websocket_response(
            product_id="BTCUSDT",
            price=97500.50,
            quantity=0.123,
            timestamp_ms=1732636800000,
        )
        assert "2024-11-26" in trade.timestamp
        assert trade.timestamp.endswith("Z")

    def test_legacy_with_zero_values(self):
        """Test legacy methods with zero values."""
        trade = Trade.from_binance_websocket_response(
            product_id="BTCUSDT",
            price=0.0,
            quantity=0.0,
            timestamp_ms=0,
        )
        assert trade.price == 0.0
        assert trade.quantity == 0.0
        assert trade.timestamp_ms == 0


class TestTradeEquality:
    """Test Trade equality and comparison."""

    def test_trades_with_same_values_equal(self):
        """Test trades with same values are equal."""
        trade1 = Trade(
            product_id="BTCUSDT",
            price=97500.50,
            quantity=0.123,
            timestamp="2024-11-26T16:00:00Z",
            timestamp_ms=1732636800000,
        )
        trade2 = Trade(
            product_id="BTCUSDT",
            price=97500.50,
            quantity=0.123,
            timestamp="2024-11-26T16:00:00Z",
            timestamp_ms=1732636800000,
        )
        assert trade1 == trade2

    def test_trades_with_different_price_not_equal(self):
        """Test trades with different price are not equal."""
        trade1 = Trade(
            product_id="BTCUSDT",
            price=97500.50,
            quantity=0.123,
            timestamp="2024-11-26T16:00:00Z",
            timestamp_ms=1732636800000,
        )
        trade2 = Trade(
            product_id="BTCUSDT",
            price=97501.00,
            quantity=0.123,
            timestamp="2024-11-26T16:00:00Z",
            timestamp_ms=1732636800000,
        )
        assert trade1 != trade2

    def test_trades_with_different_symbol_not_equal(self):
        """Test trades with different symbol are not equal."""
        trade1 = Trade(
            product_id="BTCUSDT",
            price=97500.50,
            quantity=0.123,
            timestamp="2024-11-26T16:00:00Z",
            timestamp_ms=1732636800000,
        )
        trade2 = Trade(
            product_id="ETHUSDT",
            price=97500.50,
            quantity=0.123,
            timestamp="2024-11-26T16:00:00Z",
            timestamp_ms=1732636800000,
        )
        assert trade1 != trade2


class TestTradeValidation:
    """Test Trade pydantic validation."""

    def test_invalid_price_type_raises(self):
        """Test invalid price type raises validation error."""
        with pytest.raises(Exception):  # Pydantic will raise ValidationError
            Trade(
                product_id="BTCUSDT",
                price="not_a_number",
                quantity=0.123,
                timestamp="2024-11-26T16:00:00Z",
                timestamp_ms=1732636800000,
            )

    def test_invalid_quantity_type_raises(self):
        """Test invalid quantity type raises validation error."""
        with pytest.raises(Exception):
            Trade(
                product_id="BTCUSDT",
                price=97500.50,
                quantity="not_a_number",
                timestamp="2024-11-26T16:00:00Z",
                timestamp_ms=1732636800000,
            )

    def test_invalid_timestamp_ms_type_raises(self):
        """Test invalid timestamp_ms type raises validation error."""
        with pytest.raises(Exception):
            Trade(
                product_id="BTCUSDT",
                price=97500.50,
                quantity=0.123,
                timestamp="2024-11-26T16:00:00Z",
                timestamp_ms="not_a_number",
            )

    def test_string_price_converted_to_float(self):
        """Test string price is converted to float by pydantic."""
        trade = Trade(
            product_id="BTCUSDT",
            price="97500.50",
            quantity=0.123,
            timestamp="2024-11-26T16:00:00Z",
            timestamp_ms=1732636800000,
        )
        assert trade.price == 97500.50
        assert isinstance(trade.price, float)

    def test_string_quantity_converted_to_float(self):
        """Test string quantity is converted to float by pydantic."""
        trade = Trade(
            product_id="BTCUSDT",
            price=97500.50,
            quantity="0.123",
            timestamp="2024-11-26T16:00:00Z",
            timestamp_ms=1732636800000,
        )
        assert trade.quantity == 0.123
        assert isinstance(trade.quantity, float)

    def test_string_timestamp_ms_converted_to_int(self):
        """Test string timestamp_ms is converted to int by pydantic."""
        trade = Trade(
            product_id="BTCUSDT",
            price=97500.50,
            quantity=0.123,
            timestamp="2024-11-26T16:00:00Z",
            timestamp_ms="1732636800000",
        )
        assert trade.timestamp_ms == 1732636800000
        assert isinstance(trade.timestamp_ms, int)
