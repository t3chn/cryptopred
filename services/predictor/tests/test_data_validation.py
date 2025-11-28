"""Tests for data validation module."""

import pandas as pd
import pytest
from predictor.data_validation import (
    DataQualityReport,
    OHLCVRecord,
    TechnicalIndicatorRecord,
    ValidationResult,
    detect_outliers_iqr,
    generate_quality_report,
    remove_outliers,
    validate_data,
    validate_dataframe_schema,
    validate_features,
    validate_indicator_ranges,
    validate_price_ranges,
)


class TestOHLCVSchema:
    """Tests for OHLCV Pydantic schema."""

    def test_valid_record(self):
        """Test valid OHLCV record."""
        record = OHLCVRecord(
            window_start_ms=1700000000000,
            open=50000.0,
            high=51000.0,
            low=49000.0,
            close=50500.0,
            volume=1000000.0,
        )
        assert record.close == 50500.0

    def test_negative_price_rejected(self):
        """Test that negative prices are rejected."""
        with pytest.raises(ValueError):
            OHLCVRecord(
                window_start_ms=1700000000000,
                open=-100.0,
                high=51000.0,
                low=49000.0,
                close=50500.0,
                volume=1000000.0,
            )

    def test_negative_volume_rejected(self):
        """Test that negative volume is rejected."""
        with pytest.raises(ValueError):
            OHLCVRecord(
                window_start_ms=1700000000000,
                open=50000.0,
                high=51000.0,
                low=49000.0,
                close=50500.0,
                volume=-100.0,
            )


class TestTechnicalIndicatorSchema:
    """Tests for TechnicalIndicator Pydantic schema."""

    def test_valid_record(self):
        """Test valid technical indicator record."""
        record = TechnicalIndicatorRecord(
            window_start_ms=1700000000000,
            pair="BTCUSDT",
            close=50000.0,
            volume=1000000.0,
            rsi_14=65.5,
            adx_14=25.0,
        )
        assert record.rsi_14 == 65.5

    def test_rsi_out_of_range_rejected(self):
        """Test that RSI outside 0-100 is rejected."""
        with pytest.raises(ValueError):
            TechnicalIndicatorRecord(
                window_start_ms=1700000000000,
                pair="BTCUSDT",
                close=50000.0,
                volume=1000000.0,
                rsi_14=150.0,
            )


class TestValidateData:
    """Tests for validate_data function."""

    def test_removes_missing_values(self):
        """Test that rows with missing values are removed."""
        data = pd.DataFrame({"a": [1, 2, None, 4], "b": [1, None, 3, 4]})
        result = validate_data(data, max_percentage_rows_with_missing_values=1.0)
        assert len(result) == 2

    def test_raises_on_empty_result(self):
        """Test that empty result raises ValueError."""
        data = pd.DataFrame({"a": [None, None], "b": [None, None]})
        with pytest.raises(ValueError, match="No valid rows"):
            validate_data(data)


class TestValidateFeatures:
    """Tests for validate_features function."""

    def test_valid_features(self):
        """Test validation with all required features present."""
        data = pd.DataFrame({"close": [1, 2], "volume": [100, 200], "rsi_14": [50, 60]})
        assert validate_features(data, ["close", "volume"])

    def test_missing_features(self):
        """Test validation raises on missing features."""
        data = pd.DataFrame({"close": [1, 2]})
        with pytest.raises(ValueError, match="Missing required features"):
            validate_features(data, ["close", "volume"])


class TestValidatePriceRanges:
    """Tests for validate_price_ranges function."""

    def test_valid_prices(self):
        """Test valid price ranges."""
        data = pd.DataFrame({"close": [50000, 51000, 49000], "open": [49500, 50500, 48500]})
        result = validate_price_ranges(data)
        assert result.is_valid
        assert result.invalid_rows == 0

    def test_negative_prices_detected(self):
        """Test that negative prices are detected."""
        data = pd.DataFrame({"close": [50000, -100, 49000]})
        result = validate_price_ranges(data)
        assert not result.is_valid
        assert result.invalid_rows > 0
        assert len(result.errors) > 0


class TestValidateIndicatorRanges:
    """Tests for validate_indicator_ranges function."""

    def test_valid_indicators(self):
        """Test valid indicator ranges."""
        data = pd.DataFrame(
            {"rsi_14": [30, 50, 70], "adx_14": [20, 30, 40], "volume": [100, 200, 300]}
        )
        result = validate_indicator_ranges(data)
        assert result.is_valid

    def test_rsi_out_of_range(self):
        """Test RSI outside 0-100 is detected."""
        data = pd.DataFrame({"rsi_14": [30, 150, 70]})
        result = validate_indicator_ranges(data)
        assert not result.is_valid
        assert "rsi_14" in result.errors[0]

    def test_negative_volume(self):
        """Test negative volume is detected."""
        data = pd.DataFrame({"volume": [100, -50, 200]})
        result = validate_indicator_ranges(data)
        assert not result.is_valid


class TestDetectOutliersIQR:
    """Tests for detect_outliers_iqr function."""

    def test_detects_outliers(self):
        """Test that outliers are detected."""
        data = pd.DataFrame({"values": [10, 11, 12, 13, 14, 100]})  # 100 is outlier
        outliers = detect_outliers_iqr(data)
        assert outliers["values"].sum() >= 1  # At least one outlier

    def test_no_outliers(self):
        """Test with no outliers."""
        data = pd.DataFrame({"values": [10, 11, 12, 13, 14, 15]})
        outliers = detect_outliers_iqr(data)
        assert outliers["values"].sum() == 0


class TestRemoveOutliers:
    """Tests for remove_outliers function."""

    def test_removes_outlier_rows(self):
        """Test that outlier rows are removed."""
        data = pd.DataFrame({"values": [10, 11, 12, 13, 14, 1000], "other": [1, 2, 3, 4, 5, 6]})
        result = remove_outliers(data, columns=["values"])
        assert len(result) < len(data)
        assert 1000 not in result["values"].values


class TestGenerateQualityReport:
    """Tests for generate_quality_report function."""

    def test_generates_report(self):
        """Test that quality report is generated."""
        data = pd.DataFrame(
            {
                "close": [50000, 51000, 52000],
                "volume": [100, 200, 300],
                "rsi_14": [30, 50, 70],
            }
        )
        report = generate_quality_report(data)
        assert isinstance(report, DataQualityReport)
        assert report.total_records == 3
        assert report.valid_records == 3

    def test_report_captures_missing_values(self):
        """Test that missing values are reported."""
        data = pd.DataFrame({"close": [50000, None, 52000], "volume": [100, 200, 300]})
        report = generate_quality_report(data)
        assert "close" in report.missing_values_by_column


class TestValidateDataframeSchema:
    """Tests for validate_dataframe_schema function."""

    def test_valid_dataframe(self):
        """Test validation of valid DataFrame."""
        data = pd.DataFrame(
            {
                "window_start_ms": [1700000000000, 1700000001000],
                "open": [50000.0, 50100.0],
                "high": [51000.0, 51100.0],
                "low": [49000.0, 49100.0],
                "close": [50500.0, 50600.0],
                "volume": [1000000.0, 1100000.0],
            }
        )
        result = validate_dataframe_schema(data, OHLCVRecord)
        assert isinstance(result, ValidationResult)
        assert result.is_valid

    def test_invalid_dataframe(self):
        """Test validation of invalid DataFrame."""
        data = pd.DataFrame(
            {
                "window_start_ms": [1700000000000, 1700000001000],
                "open": [-100.0, 50100.0],  # Negative price
                "high": [51000.0, 51100.0],
                "low": [49000.0, 49100.0],
                "close": [50500.0, 50600.0],
                "volume": [1000000.0, 1100000.0],
            }
        )
        result = validate_dataframe_schema(data, OHLCVRecord)
        assert not result.is_valid
        assert result.invalid_rows > 0
