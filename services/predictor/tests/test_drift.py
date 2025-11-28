"""Tests for drift detection module."""

import numpy as np
import pandas as pd
import pytest
from predictor.drift import DriftDetector, DriftResult, PerformanceResult, check_drift_alert


class TestDriftDetector:
    """Tests for DriftDetector class."""

    @pytest.fixture
    def detector(self) -> DriftDetector:
        """Create drift detector with default settings."""
        return DriftDetector(drift_threshold=0.1, performance_degradation_threshold=0.2)

    @pytest.fixture
    def reference_data(self) -> pd.DataFrame:
        """Create reference dataset."""
        np.random.seed(42)
        n = 500
        return pd.DataFrame(
            {
                "close": np.random.normal(50000, 1000, n),
                "volume": np.random.normal(1000000, 100000, n),
                "rsi_14": np.random.normal(50, 10, n),
                "target": np.random.normal(50500, 1000, n),
            }
        )

    @pytest.fixture
    def similar_current_data(self) -> pd.DataFrame:
        """Create current dataset similar to reference."""
        np.random.seed(123)
        n = 200
        return pd.DataFrame(
            {
                "close": np.random.normal(50000, 1000, n),
                "volume": np.random.normal(1000000, 100000, n),
                "rsi_14": np.random.normal(50, 10, n),
                "target": np.random.normal(50500, 1000, n),
            }
        )

    @pytest.fixture
    def drifted_current_data(self) -> pd.DataFrame:
        """Create current dataset with significant drift."""
        np.random.seed(456)
        n = 200
        return pd.DataFrame(
            {
                "close": np.random.normal(60000, 2000, n),
                "volume": np.random.normal(2000000, 200000, n),
                "rsi_14": np.random.normal(70, 15, n),
                "target": np.random.normal(60500, 2000, n),
            }
        )

    def test_no_data_drift_detected(
        self,
        detector: DriftDetector,
        reference_data: pd.DataFrame,
        similar_current_data: pd.DataFrame,
    ):
        """Test that similar data shows no drift."""
        result = detector.detect_data_drift(
            reference_data=reference_data,
            current_data=similar_current_data,
            feature_columns=["close", "volume", "rsi_14"],
        )

        assert isinstance(result, DriftResult)
        assert not result.is_drifted
        assert result.drift_score < 0.5

    def test_data_drift_detected(
        self,
        detector: DriftDetector,
        reference_data: pd.DataFrame,
        drifted_current_data: pd.DataFrame,
    ):
        """Test that significantly different data shows drift."""
        result = detector.detect_data_drift(
            reference_data=reference_data,
            current_data=drifted_current_data,
            feature_columns=["close", "volume", "rsi_14"],
        )

        assert isinstance(result, DriftResult)
        assert result.is_drifted
        assert result.drift_score > 0.1
        # Check that details contain drift info (structure may vary by API version)
        assert "number_of_drifted_columns" in result.details
        assert result.details["number_of_drifted_columns"] > 0

    def test_target_drift_no_drift(
        self,
        detector: DriftDetector,
        reference_data: pd.DataFrame,
        similar_current_data: pd.DataFrame,
    ):
        """Test target drift with similar distributions."""
        result = detector.detect_target_drift(
            reference_data=reference_data,
            current_data=similar_current_data,
            target_column="target",
        )

        assert isinstance(result, DriftResult)
        assert not result.is_drifted

    def test_target_drift_detected(
        self,
        detector: DriftDetector,
        reference_data: pd.DataFrame,
        drifted_current_data: pd.DataFrame,
    ):
        """Test target drift detection with different distribution."""
        result = detector.detect_target_drift(
            reference_data=reference_data,
            current_data=drifted_current_data,
            target_column="target",
        )

        assert isinstance(result, DriftResult)
        assert result.is_drifted

    def test_feature_drift_single_column(
        self,
        detector: DriftDetector,
        reference_data: pd.DataFrame,
        drifted_current_data: pd.DataFrame,
    ):
        """Test drift detection for a single feature."""
        result = detector.detect_feature_drift(
            reference_data=reference_data,
            current_data=drifted_current_data,
            feature_name="close",
        )

        assert isinstance(result, DriftResult)
        assert result.is_drifted
        assert "close" in result.drifted_features

    def test_performance_monitoring_no_degradation(
        self,
        detector: DriftDetector,
    ):
        """Test performance monitoring with stable metrics."""
        np.random.seed(42)
        n = 200

        reference = pd.DataFrame(
            {
                "target": np.random.normal(50000, 100, n),
                "prediction": np.random.normal(50000, 100, n),
            }
        )

        current = pd.DataFrame(
            {
                "target": np.random.normal(50000, 100, n),
                "prediction": np.random.normal(50000, 100, n),
            }
        )

        result = detector.monitor_performance(
            reference_data=reference,
            current_data=current,
            target_column="target",
            prediction_column="prediction",
        )

        assert isinstance(result, PerformanceResult)
        assert result.mae > 0
        assert result.rmse > 0
        assert not result.is_degraded

    def test_performance_monitoring_degradation(
        self,
        detector: DriftDetector,
    ):
        """Test performance monitoring with degraded predictions."""
        np.random.seed(42)
        n = 200

        reference = pd.DataFrame(
            {
                "target": np.random.normal(50000, 100, n),
                "prediction": np.random.normal(50000, 100, n),
            }
        )

        current = pd.DataFrame(
            {
                "target": np.random.normal(50000, 100, n),
                "prediction": np.random.normal(50500, 500, n),
            }
        )

        result = detector.monitor_performance(
            reference_data=reference,
            current_data=current,
            target_column="target",
            prediction_column="prediction",
        )

        assert isinstance(result, PerformanceResult)
        assert result.is_degraded
        assert result.degradation_pct is not None
        assert result.degradation_pct > 0.2

    def test_auto_detect_numeric_features(
        self,
        detector: DriftDetector,
        reference_data: pd.DataFrame,
        similar_current_data: pd.DataFrame,
    ):
        """Test that numeric features are auto-detected when not specified."""
        result = detector.detect_data_drift(
            reference_data=reference_data,
            current_data=similar_current_data,
            feature_columns=None,
        )

        assert isinstance(result, DriftResult)
        assert "details" in result.__dict__


class TestCheckDriftAlert:
    """Tests for check_drift_alert function."""

    def test_alert_triggered(self):
        """Test that alert is triggered when drift exceeds threshold."""
        result = DriftResult(
            is_drifted=True,
            drift_score=0.25,
            drifted_features=["close", "volume"],
            details={},
        )

        assert check_drift_alert(result, alert_threshold=0.15)

    def test_no_alert(self):
        """Test that alert is not triggered when drift is low."""
        result = DriftResult(
            is_drifted=False,
            drift_score=0.05,
            drifted_features=[],
            details={},
        )

        assert not check_drift_alert(result, alert_threshold=0.15)

    def test_alert_threshold_edge_case(self):
        """Test alert at exact threshold."""
        result = DriftResult(
            is_drifted=True,
            drift_score=0.15,
            drifted_features=["close"],
            details={},
        )

        assert not check_drift_alert(result, alert_threshold=0.15)
        assert check_drift_alert(result, alert_threshold=0.14)
