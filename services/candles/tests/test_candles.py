"""Tests for candle aggregation functions."""

import pytest
from candles.main import init_candle, update_candle


class TestInitCandle:
    """Tests for init_candle function."""

    def test_init_candle_basic(self, sample_trade):
        """Test basic candle initialization."""
        candle = init_candle(sample_trade)

        assert candle["open"] == 50000.0
        assert candle["high"] == 50000.0
        assert candle["low"] == 50000.0
        assert candle["close"] == 50000.0
        assert candle["volume"] == 0.1
        assert candle["pair"] == "BTCUSDT"

    def test_init_candle_different_prices(self):
        """Test initialization with different price values."""
        trade = {
            "product_id": "ETHUSDT",
            "price": 3000.50,
            "quantity": 1.5,
            "timestamp_ms": 1700000000000,
        }

        candle = init_candle(trade)

        assert candle["open"] == 3000.50
        assert candle["high"] == 3000.50
        assert candle["low"] == 3000.50
        assert candle["close"] == 3000.50
        assert candle["volume"] == 1.5
        assert candle["pair"] == "ETHUSDT"


class TestUpdateCandle:
    """Tests for update_candle function."""

    def test_update_candle_higher_price(self, sample_trade):
        """Test updating candle with higher price."""
        candle = init_candle(sample_trade)

        new_trade = {
            "product_id": "BTCUSDT",
            "price": 51000.0,  # Higher than initial
            "quantity": 0.2,
            "timestamp_ms": 1700000001000,
        }

        updated = update_candle(candle, new_trade)

        assert updated["open"] == 50000.0  # Open unchanged
        assert updated["high"] == 51000.0  # New high
        assert updated["low"] == 50000.0  # Low unchanged
        assert updated["close"] == 51000.0  # Close updated
        assert updated["volume"] == pytest.approx(0.3)  # Volume accumulated

    def test_update_candle_lower_price(self, sample_trade):
        """Test updating candle with lower price."""
        candle = init_candle(sample_trade)

        new_trade = {
            "product_id": "BTCUSDT",
            "price": 49000.0,  # Lower than initial
            "quantity": 0.15,
            "timestamp_ms": 1700000001000,
        }

        updated = update_candle(candle, new_trade)

        assert updated["open"] == 50000.0  # Open unchanged
        assert updated["high"] == 50000.0  # High unchanged
        assert updated["low"] == 49000.0  # New low
        assert updated["close"] == 49000.0  # Close updated
        assert updated["volume"] == 0.25  # Volume accumulated

    def test_update_candle_multiple_trades(self, sample_trades):
        """Test updating candle with multiple trades."""
        candle = init_candle(sample_trades[0])

        for trade in sample_trades[1:]:
            candle = update_candle(candle, trade)

        assert candle["open"] == 50000.0  # First trade price
        assert candle["high"] == 50100.0  # Max price
        assert candle["low"] == 49900.0  # Min price
        assert candle["close"] == 50050.0  # Last trade price
        assert candle["volume"] == pytest.approx(0.5)  # Sum of quantities

    def test_update_candle_preserves_pair(self, sample_trade):
        """Test that pair is preserved during updates."""
        candle = init_candle(sample_trade)

        new_trade = {
            "product_id": "BTCUSDT",
            "price": 50500.0,
            "quantity": 0.1,
            "timestamp_ms": 1700000001000,
        }

        updated = update_candle(candle, new_trade)

        assert updated["pair"] == "BTCUSDT"


class TestTimestampExtractor:
    """Tests for custom timestamp extractor."""

    def test_custom_ts_extractor(self):
        """Test that timestamp is extracted from message payload."""
        from candles.main import custom_ts_extractor

        value = {"timestamp_ms": 1700000000000}
        result = custom_ts_extractor(value, None, 0, None)

        assert result == 1700000000000
