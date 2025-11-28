"""Data drift detection using Evidently.

This module provides tools to detect:
- Data drift: Changes in feature distributions over time
- Target drift: Changes in prediction/target distributions
- Performance drift: Model performance degradation over time
"""

from dataclasses import dataclass
from typing import Any

import pandas as pd
from evidently.legacy.metric_preset import DataDriftPreset, TargetDriftPreset
from evidently.legacy.metrics import (
    ColumnDriftMetric,
    DatasetDriftMetric,
    RegressionQualityMetric,
)
from evidently.legacy.pipeline.column_mapping import ColumnMapping
from evidently.legacy.report import Report
from loguru import logger


@dataclass
class DriftResult:
    """Result of drift detection analysis."""

    is_drifted: bool
    drift_score: float
    drifted_features: list[str]
    details: dict[str, Any]


@dataclass
class PerformanceResult:
    """Result of performance monitoring."""

    mae: float
    rmse: float
    mape: float | None
    r2: float
    is_degraded: bool
    degradation_pct: float | None


class DriftDetector:
    """Detect data and target drift using Evidently.

    Data drift in financial ML is critical because market regimes change:
    - Bull vs bear markets have different feature distributions
    - Volatility regimes affect price movement patterns
    - Sentiment correlations shift during market events

    Detecting drift early enables:
    - Automatic model retraining triggers
    - Alert generation for manual review
    - Performance degradation root cause analysis
    """

    def __init__(
        self,
        drift_threshold: float = 0.1,
        performance_degradation_threshold: float = 0.2,
    ):
        """Initialize drift detector.

        Args:
            drift_threshold: Dataset drift share threshold (0-1).
                If share of drifted features exceeds this, dataset is considered drifted.
            performance_degradation_threshold: MAE increase threshold (0-1).
                If MAE increases by this percentage, performance is degraded.
        """
        self.drift_threshold = drift_threshold
        self.performance_degradation_threshold = performance_degradation_threshold

    def detect_data_drift(
        self,
        reference_data: pd.DataFrame,
        current_data: pd.DataFrame,
        feature_columns: list[str] | None = None,
    ) -> DriftResult:
        """Detect data drift between reference and current datasets.

        Uses statistical tests (KS test for numerical, chi-square for categorical)
        to detect distribution changes in features.

        Args:
            reference_data: Historical/training data (baseline)
            current_data: Recent/production data (to compare)
            feature_columns: List of feature columns to analyze.
                If None, analyzes all numeric columns.

        Returns:
            DriftResult with drift status and details
        """
        if feature_columns is None:
            feature_columns = list(reference_data.select_dtypes(include=["number"]).columns)

        logger.info(f"Detecting data drift for {len(feature_columns)} features")

        column_mapping = ColumnMapping()
        column_mapping.numerical_features = feature_columns

        report = Report(metrics=[DataDriftPreset()])
        report.run(
            reference_data=reference_data[feature_columns],
            current_data=current_data[feature_columns],
            column_mapping=column_mapping,
        )

        result_dict = report.as_dict()
        drift_metrics = result_dict["metrics"][0]["result"]

        drift_share = drift_metrics.get("share_of_drifted_columns", 0)
        number_of_drifted = drift_metrics.get("number_of_drifted_columns", 0)
        drifted_features = []

        # Try different API structures for getting drifted columns
        drift_by_columns = drift_metrics.get("drift_by_columns", {})
        for col, col_result in drift_by_columns.items():
            if col_result.get("drift_detected", False):
                drifted_features.append(col)

        # Fallback: if drift detected but no features extracted, check other metrics
        if number_of_drifted > 0 and not drifted_features:
            for metric in result_dict.get("metrics", []):
                result = metric.get("result", {})
                col_name = result.get("column_name")
                if col_name and result.get("drift_detected", False):
                    drifted_features.append(col_name)

        is_drifted = drift_share > self.drift_threshold

        if is_drifted:
            logger.warning(
                f"Data drift detected! Share: {drift_share:.2%}, "
                f"threshold: {self.drift_threshold:.2%}, "
                f"drifted features: {drifted_features}"
            )
        else:
            logger.info(f"No significant drift. Share: {drift_share:.2%}")

        return DriftResult(
            is_drifted=is_drifted,
            drift_score=drift_share,
            drifted_features=drifted_features,
            details=drift_metrics,
        )

    def detect_target_drift(
        self,
        reference_data: pd.DataFrame,
        current_data: pd.DataFrame,
        target_column: str,
    ) -> DriftResult:
        """Detect drift in target/prediction distribution.

        Important for detecting regime changes in the target variable
        which may indicate market condition shifts.

        Args:
            reference_data: Historical data with target column
            current_data: Recent data with target column
            target_column: Name of the target column

        Returns:
            DriftResult with target drift analysis
        """
        logger.info(f"Detecting target drift for column '{target_column}'")

        column_mapping = ColumnMapping()
        column_mapping.target = target_column

        report = Report(metrics=[TargetDriftPreset()])
        report.run(
            reference_data=reference_data[[target_column]],
            current_data=current_data[[target_column]],
            column_mapping=column_mapping,
        )

        result_dict = report.as_dict()

        drift_detected = False
        drift_score = 0.0

        for metric in result_dict["metrics"]:
            if "drift_detected" in metric.get("result", {}):
                drift_detected = metric["result"]["drift_detected"]
                drift_score = metric["result"].get("drift_score", 0.0)
                break

        if drift_detected:
            logger.warning(f"Target drift detected! Score: {drift_score:.4f}")
        else:
            logger.info(f"No target drift. Score: {drift_score:.4f}")

        return DriftResult(
            is_drifted=drift_detected,
            drift_score=drift_score,
            drifted_features=[target_column] if drift_detected else [],
            details=result_dict,
        )

    def detect_feature_drift(
        self,
        reference_data: pd.DataFrame,
        current_data: pd.DataFrame,
        feature_name: str,
    ) -> DriftResult:
        """Detect drift for a single feature.

        Useful for monitoring specific high-importance features.

        Args:
            reference_data: Historical data
            current_data: Recent data
            feature_name: Name of the feature to analyze

        Returns:
            DriftResult for the single feature
        """
        logger.debug(f"Detecting drift for feature '{feature_name}'")

        report = Report(metrics=[ColumnDriftMetric(column_name=feature_name)])
        report.run(
            reference_data=reference_data[[feature_name]],
            current_data=current_data[[feature_name]],
        )

        result_dict = report.as_dict()
        metric_result = result_dict["metrics"][0]["result"]

        drift_detected = metric_result.get("drift_detected", False)
        drift_score = metric_result.get("drift_score", 0.0)

        return DriftResult(
            is_drifted=drift_detected,
            drift_score=drift_score,
            drifted_features=[feature_name] if drift_detected else [],
            details=metric_result,
        )

    def monitor_performance(
        self,
        reference_data: pd.DataFrame,
        current_data: pd.DataFrame,
        target_column: str,
        prediction_column: str,
        baseline_mae: float | None = None,
    ) -> PerformanceResult:
        """Monitor model performance and detect degradation.

        Compares current performance against reference or baseline.

        Args:
            reference_data: Historical data with actual and predicted values
            current_data: Recent data with actual and predicted values
            target_column: Name of actual target column
            prediction_column: Name of prediction column
            baseline_mae: Optional baseline MAE to compare against.
                If None, uses reference data MAE as baseline.

        Returns:
            PerformanceResult with metrics and degradation status
        """
        logger.info("Monitoring model performance")

        column_mapping = ColumnMapping()
        column_mapping.target = target_column
        column_mapping.prediction = prediction_column

        report = Report(metrics=[RegressionQualityMetric()])
        report.run(
            reference_data=reference_data,
            current_data=current_data,
            column_mapping=column_mapping,
        )

        result_dict = report.as_dict()
        current_metrics = result_dict["metrics"][0]["result"]["current"]

        current_mae = current_metrics["mean_abs_error"]
        current_rmse = current_metrics["rmse"]
        current_r2 = current_metrics["r2_score"]
        current_mape = current_metrics.get("mean_abs_perc_error")

        if baseline_mae is None:
            ref_metrics = result_dict["metrics"][0]["result"].get("reference", {})
            baseline_mae = ref_metrics.get("mean_abs_error", current_mae)

        degradation_pct = None
        is_degraded = False

        if baseline_mae > 0:
            degradation_pct = (current_mae - baseline_mae) / baseline_mae
            is_degraded = degradation_pct > self.performance_degradation_threshold

        if is_degraded:
            logger.warning(
                f"Performance degradation detected! "
                f"MAE: {current_mae:.4f} (baseline: {baseline_mae:.4f}), "
                f"degradation: {degradation_pct:.2%}"
            )
        else:
            logger.info(f"Performance stable. MAE: {current_mae:.4f}")

        return PerformanceResult(
            mae=current_mae,
            rmse=current_rmse,
            mape=current_mape,
            r2=current_r2,
            is_degraded=is_degraded,
            degradation_pct=degradation_pct,
        )

    def generate_drift_report(
        self,
        reference_data: pd.DataFrame,
        current_data: pd.DataFrame,
        feature_columns: list[str],
        target_column: str | None = None,
        output_path: str | None = None,
    ) -> Report:
        """Generate comprehensive drift report.

        Creates an HTML report with visualizations for data drift analysis.

        Args:
            reference_data: Historical/training data
            current_data: Recent/production data
            feature_columns: List of feature columns to analyze
            target_column: Optional target column to include
            output_path: Optional path to save HTML report

        Returns:
            Evidently Report object
        """
        logger.info("Generating comprehensive drift report")

        column_mapping = ColumnMapping()
        column_mapping.numerical_features = feature_columns
        if target_column:
            column_mapping.target = target_column

        metrics = [DataDriftPreset(), DatasetDriftMetric()]
        if target_column:
            metrics.append(TargetDriftPreset())

        report = Report(metrics=metrics)

        cols_to_use = feature_columns.copy()
        if target_column and target_column not in cols_to_use:
            cols_to_use.append(target_column)

        report.run(
            reference_data=reference_data[cols_to_use],
            current_data=current_data[cols_to_use],
            column_mapping=column_mapping,
        )

        if output_path:
            report.save_html(output_path)
            logger.info(f"Drift report saved to {output_path}")

        return report


def check_drift_alert(
    drift_result: DriftResult,
    alert_threshold: float = 0.15,
) -> bool:
    """Check if drift exceeds alert threshold.

    Args:
        drift_result: Result from drift detection
        alert_threshold: Threshold for generating alert

    Returns:
        True if alert should be generated
    """
    return drift_result.drift_score > alert_threshold
