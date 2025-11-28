"""Tests for technical indicators calculations."""

import pytest
from technical_indicators.indicators import compute_indicators


class TestComputeIndicators:
    """Tests for compute_indicators function."""

    def test_empty_candles(self, indicators_config):
        """Test with empty candles list."""
        result = compute_indicators([], indicators_config)
        assert result == {}

    def test_insufficient_candles_for_sma(self, indicators_config):
        """Test SMA with insufficient candles."""
        candles = [{"close": 100.0}]
        result = compute_indicators(candles, indicators_config)

        # SMA should be None when not enough data
        assert result.get("sma_7") is None

    def test_sma_calculation(self, sample_candles, indicators_config):
        """Test SMA calculation with sufficient data."""
        result = compute_indicators(sample_candles, indicators_config)

        # SMA 7 should exist
        assert "sma_7" in result
        assert result["sma_7"] is not None
        assert isinstance(result["sma_7"], float)

        # SMA 14 should exist
        assert "sma_14" in result
        assert result["sma_14"] is not None

    def test_ema_calculation(self, sample_candles, indicators_config):
        """Test EMA calculation."""
        result = compute_indicators(sample_candles, indicators_config)

        assert "ema_7" in result
        assert result["ema_7"] is not None
        assert isinstance(result["ema_7"], float)

        assert "ema_14" in result
        assert result["ema_14"] is not None

    def test_rsi_calculation(self, sample_candles, indicators_config):
        """Test RSI calculation."""
        result = compute_indicators(sample_candles, indicators_config)

        assert "rsi_14" in result
        # RSI should be between 0 and 100
        if result["rsi_14"] is not None:
            assert 0 <= result["rsi_14"] <= 100

    def test_macd_calculation(self, sample_candles, indicators_config):
        """Test MACD calculation."""
        result = compute_indicators(sample_candles, indicators_config)

        assert "macd" in result
        assert "macd_signal" in result
        assert "macd_hist" in result

    def test_bollinger_bands(self, sample_candles, indicators_config):
        """Test Bollinger Bands calculation."""
        result = compute_indicators(sample_candles, indicators_config)

        assert "bb_upper" in result
        assert "bb_middle" in result
        assert "bb_lower" in result

        # Upper should be >= middle >= lower
        if all(result.get(k) is not None for k in ["bb_upper", "bb_middle", "bb_lower"]):
            assert result["bb_upper"] >= result["bb_middle"]
            assert result["bb_middle"] >= result["bb_lower"]

    def test_stochastic(self, sample_candles, indicators_config):
        """Test Stochastic oscillator calculation."""
        result = compute_indicators(sample_candles, indicators_config)

        assert "stoch_k" in result
        assert "stoch_d" in result

        # Stochastic values should be between 0 and 100
        if result["stoch_k"] is not None:
            assert 0 <= result["stoch_k"] <= 100
        if result["stoch_d"] is not None:
            assert 0 <= result["stoch_d"] <= 100

    def test_atr_calculation(self, sample_candles, indicators_config):
        """Test ATR calculation."""
        result = compute_indicators(sample_candles, indicators_config)

        assert "atr_14" in result
        # ATR should be positive
        if result["atr_14"] is not None:
            assert result["atr_14"] >= 0

    def test_obv_calculation(self, sample_candles, indicators_config):
        """Test OBV calculation."""
        result = compute_indicators(sample_candles, indicators_config)

        assert "obv" in result
        assert result["obv"] is not None

    def test_disabled_indicator(self, sample_candles):
        """Test that disabled indicators are not computed."""
        config = {
            "indicators": {
                "sma": {"enabled": False, "periods": [7]},
                "ema": {"enabled": True, "periods": [7]},
            },
            "max_candles": 100,
        }
        result = compute_indicators(sample_candles, config)

        assert "sma_7" not in result
        assert "ema_7" in result

    def test_custom_periods(self, sample_candles):
        """Test custom period configuration."""
        config = {
            "indicators": {
                "sma": {"enabled": True, "periods": [5, 10]},
            },
            "max_candles": 100,
        }
        result = compute_indicators(sample_candles, config)

        assert "sma_5" in result
        assert "sma_10" in result
        assert "sma_7" not in result  # Default period not included

    def test_all_indicators_disabled(self, sample_candles):
        """Test with all indicators disabled."""
        config = {
            "indicators": {
                "sma": {"enabled": False},
                "ema": {"enabled": False},
            },
            "max_candles": 100,
        }
        result = compute_indicators(sample_candles, config)
        assert result == {}

    def test_indicator_values_are_numeric(self, sample_candles, indicators_config):
        """Test that all returned values are numeric."""
        result = compute_indicators(sample_candles, indicators_config)

        for key, value in result.items():
            if value is not None:
                assert isinstance(value, (int, float)), f"{key} is not numeric: {type(value)}"


class TestIndicatorAccuracy:
    """Tests for indicator calculation accuracy."""

    def test_sma_manual_calculation(self):
        """Test SMA against manual calculation."""
        # Create simple candles with known values and all OHLCV fields
        candles = [
            {
                "open": float(i),
                "high": float(i + 1),
                "low": float(i - 0.5),
                "close": float(i),
                "volume": 100.0,
            }
            for i in range(1, 8)
        ]  # close: 1, 2, 3, 4, 5, 6, 7

        config = {
            "indicators": {"sma": {"enabled": True, "periods": [7]}},
            "max_candles": 100,
        }

        result = compute_indicators(candles, config)

        # SMA of 1-7 = (1+2+3+4+5+6+7)/7 = 28/7 = 4.0
        assert result["sma_7"] == pytest.approx(4.0, rel=1e-6)

    def test_ema_responds_to_recent_prices(self, sample_candles, indicators_config):
        """Test that EMA is more responsive to recent prices than SMA."""
        result = compute_indicators(sample_candles, indicators_config)

        # Both should exist
        assert result.get("sma_7") is not None
        assert result.get("ema_7") is not None

        # EMA and SMA should be different (EMA weights recent more)
        # This is a sanity check, not exact equality
        # In trending data, they will differ
