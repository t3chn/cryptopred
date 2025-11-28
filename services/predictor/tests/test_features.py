"""Tests for feature engineering module."""

import numpy as np
import pandas as pd
import pytest
from predictor.features import (
    add_lunarcrush_features,
    add_time_features,
    get_lunarcrush_feature_names,
    get_time_feature_names,
)


class TestAddTimeFeatures:
    """Tests for add_time_features function."""

    @pytest.fixture
    def sample_data(self) -> pd.DataFrame:
        """Create sample data with timestamps."""
        # Timestamps for 2024-01-15 at different hours (Monday)
        base_ts = 1705312800000  # 2024-01-15 10:00:00 UTC
        hour_ms = 3600 * 1000
        return pd.DataFrame(
            {
                "window_start_ms": [base_ts + i * hour_ms for i in range(24)],
                "close": [50000 + i * 100 for i in range(24)],
            }
        )

    def test_adds_time_features(self, sample_data):
        """Test that all time features are added."""
        result = add_time_features(sample_data)

        expected_cols = get_time_feature_names()
        for col in expected_cols:
            assert col in result.columns, f"Missing column: {col}"

    def test_hour_extraction(self, sample_data):
        """Test hour extraction from timestamp."""
        result = add_time_features(sample_data)

        # Should have hours 10 through 33 (wraps around)
        assert result["hour"].iloc[0] == 10
        assert result["hour"].iloc[14] == 0  # Wraps at midnight

    def test_day_of_week_extraction(self, sample_data):
        """Test day of week extraction."""
        result = add_time_features(sample_data)

        # 2024-01-15 is Monday (day_of_week = 0)
        assert result["day_of_week"].iloc[0] == 0

    def test_is_peak_hour(self, sample_data):
        """Test peak hour flag."""
        result = add_time_features(sample_data)

        # Peak hours are 15, 16, 17 UTC
        peak_hours = result[result["is_peak_hour"] == 1]["hour"].unique()
        assert set(peak_hours).issubset({15, 16, 17})

    def test_is_weekend(self, sample_data):
        """Test weekend flag."""
        result = add_time_features(sample_data)

        # Monday is not weekend
        assert result["is_weekend"].iloc[0] == 0

    def test_cyclical_encoding(self, sample_data):
        """Test cyclical encoding bounds."""
        result = add_time_features(sample_data)

        # Sin/cos should be in [-1, 1]
        for col in ["hour_sin", "hour_cos", "dow_sin", "dow_cos"]:
            assert result[col].min() >= -1
            assert result[col].max() <= 1


class TestAddLunarCrushFeatures:
    """Tests for add_lunarcrush_features function."""

    @pytest.fixture
    def sample_price_data(self) -> pd.DataFrame:
        """Create sample price data."""
        base_ts = 1705312800000  # 2024-01-15 10:00:00 UTC
        hour_ms = 3600 * 1000
        n = 48
        return pd.DataFrame(
            {
                "window_start_ms": [base_ts + i * hour_ms for i in range(n)],
                "close": [50000 + i * 100 for i in range(n)],
            }
        )

    @pytest.fixture
    def sample_lunarcrush_data(self) -> pd.DataFrame:
        """Create sample LunarCrush data."""
        base_ts = 1705312800000
        hour_ms = 3600 * 1000
        n = 48
        return pd.DataFrame(
            {
                "time_ms": [base_ts + i * hour_ms for i in range(n)],
                "sentiment": [50 + np.sin(i / 6) * 10 for i in range(n)],
                "galaxy_score": [60 + np.cos(i / 6) * 5 for i in range(n)],
                "alt_rank": [100 + i for i in range(n)],
                "interactions": [10000 + i * 100 for i in range(n)],
                "social_dominance": [5.0 + np.sin(i / 12) for i in range(n)],
            }
        )

    def test_merge_lunarcrush_features(self, sample_price_data, sample_lunarcrush_data):
        """Test merging LunarCrush data with price data."""
        result = add_lunarcrush_features(sample_price_data, sample_lunarcrush_data)

        # Should have sentiment and galaxy_score columns
        assert "sentiment" in result.columns
        assert "galaxy_score" in result.columns
        assert "alt_rank" in result.columns

    def test_lag_features_created(self, sample_price_data, sample_lunarcrush_data):
        """Test that lag features are created."""
        result = add_lunarcrush_features(sample_price_data, sample_lunarcrush_data)

        assert "sentiment_lag_1h" in result.columns
        assert "sentiment_lag_2h" in result.columns
        assert "sentiment_lag_4h" in result.columns
        assert "galaxy_score_lag_1h" in result.columns

    def test_rolling_features_created(self, sample_price_data, sample_lunarcrush_data):
        """Test that rolling features are created."""
        result = add_lunarcrush_features(sample_price_data, sample_lunarcrush_data)

        assert "sentiment_ma_24h" in result.columns
        assert "sentiment_std_24h" in result.columns
        assert "interactions_ma_24h" in result.columns

    def test_empty_lunarcrush_data(self, sample_price_data):
        """Test handling of empty LunarCrush data."""
        empty_lc = pd.DataFrame()
        result = add_lunarcrush_features(sample_price_data, empty_lc)

        # Should return original data unchanged
        assert len(result) == len(sample_price_data)
        assert "sentiment" not in result.columns


class TestFeatureNameGetters:
    """Tests for feature name getter functions."""

    def test_get_time_feature_names(self):
        """Test that time feature names list is complete."""
        names = get_time_feature_names()

        assert "hour" in names
        assert "day_of_week" in names
        assert "is_weekend" in names
        assert "is_peak_hour" in names
        assert "hour_sin" in names
        assert "hour_cos" in names
        assert len(names) == 10

    def test_get_lunarcrush_feature_names(self):
        """Test that LunarCrush feature names list is complete."""
        names = get_lunarcrush_feature_names()

        assert "sentiment" in names
        assert "galaxy_score" in names
        assert "sentiment_lag_1h" in names
        assert "sentiment_ma_24h" in names
        assert len(names) == 14
