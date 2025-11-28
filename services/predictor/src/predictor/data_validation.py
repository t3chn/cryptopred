"""Data validation utilities with Pydantic schemas and quality checks.

This module provides comprehensive data validation for financial ML:
- Schema validation with Pydantic models
- Range checks for financial data (prices, volumes, indicators)
- Outlier detection using IQR method
- Data quality reporting
"""

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from loguru import logger
from pydantic import BaseModel, Field, field_validator


class OHLCVRecord(BaseModel):
    """Schema for OHLCV (candlestick) data."""

    window_start_ms: int = Field(ge=0, description="Window start timestamp in ms")
    open: float = Field(gt=0, description="Open price")
    high: float = Field(gt=0, description="High price")
    low: float = Field(gt=0, description="Low price")
    close: float = Field(gt=0, description="Close price")
    volume: float = Field(ge=0, description="Trading volume")

    @field_validator("high")
    @classmethod
    def high_gte_low(cls, v: float, info: Any) -> float:
        """Validate that high >= low."""
        if "low" in info.data and v < info.data["low"]:
            raise ValueError("high must be >= low")
        return v

    @field_validator("high")
    @classmethod
    def high_gte_open_close(cls, v: float, info: Any) -> float:
        """Validate that high >= open and high >= close."""
        for field_name in ["open", "close"]:
            if field_name in info.data and v < info.data[field_name]:
                raise ValueError(f"high must be >= {field_name}")
        return v

    @field_validator("low")
    @classmethod
    def low_lte_open_close(cls, v: float, info: Any) -> float:
        """Validate that low <= open and low <= close."""
        for field_name in ["open", "close"]:
            if field_name in info.data and v > info.data[field_name]:
                raise ValueError(f"low must be <= {field_name}")
        return v


class TechnicalIndicatorRecord(BaseModel):
    """Schema for technical indicator data."""

    window_start_ms: int = Field(ge=0)
    pair: str = Field(min_length=1)
    close: float = Field(gt=0)
    volume: float = Field(ge=0)

    # RSI bounds: 0-100
    rsi_14: float | None = Field(default=None, ge=0, le=100)

    # MACD: can be any value
    macd: float | None = None
    macd_signal: float | None = None
    macd_histogram: float | None = None

    # Bollinger Bands
    bb_upper: float | None = Field(default=None, gt=0)
    bb_middle: float | None = Field(default=None, gt=0)
    bb_lower: float | None = Field(default=None, gt=0)

    # ADX: 0-100
    adx_14: float | None = Field(default=None, ge=0, le=100)

    # Moving averages
    sma_20: float | None = Field(default=None, gt=0)
    ema_12: float | None = Field(default=None, gt=0)
    ema_26: float | None = Field(default=None, gt=0)


@dataclass
class ValidationResult:
    """Result of data validation."""

    is_valid: bool
    total_rows: int
    valid_rows: int
    invalid_rows: int
    missing_ratio: float
    outlier_ratio: float
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class DataQualityReport:
    """Comprehensive data quality report."""

    total_records: int
    valid_records: int
    missing_values_by_column: dict[str, int]
    outliers_by_column: dict[str, int]
    range_violations: dict[str, int]
    validation_errors: list[str]


def validate_data(
    data: pd.DataFrame,
    max_percentage_rows_with_missing_values: float = 0.01,
) -> pd.DataFrame:
    """Validate and clean training data.

    Args:
        data: Input DataFrame
        max_percentage_rows_with_missing_values: Max allowed missing value ratio

    Returns:
        Cleaned DataFrame

    Raises:
        ValueError: If data quality is below threshold
    """
    initial_rows = len(data)
    logger.info(f"Validating data with {initial_rows} rows")

    # Check for missing values
    missing_ratio = data.isnull().any(axis=1).sum() / len(data)
    logger.info(f"Missing value ratio: {missing_ratio:.4f}")

    if missing_ratio > max_percentage_rows_with_missing_values:
        logger.warning(
            f"Missing ratio {missing_ratio:.4f} exceeds threshold "
            f"{max_percentage_rows_with_missing_values}"
        )

    # Drop rows with missing values
    data = data.dropna()
    final_rows = len(data)

    logger.info(f"Rows after cleaning: {final_rows} (dropped {initial_rows - final_rows})")

    if final_rows == 0:
        raise ValueError("No valid rows remaining after cleaning")

    return data


def validate_features(
    data: pd.DataFrame,
    required_features: list[str],
) -> bool:
    """Validate that all required features are present.

    Args:
        data: Input DataFrame
        required_features: List of required column names

    Returns:
        True if all features present

    Raises:
        ValueError: If features are missing
    """
    missing = set(required_features) - set(data.columns)
    if missing:
        raise ValueError(f"Missing required features: {missing}")
    return True


def validate_price_ranges(
    data: pd.DataFrame,
    price_columns: list[str] | None = None,
    min_price: float = 0.0,
    max_price: float = 1e9,
) -> ValidationResult:
    """Validate that price values are within expected ranges.

    Args:
        data: Input DataFrame
        price_columns: List of price columns to validate. Auto-detects if None.
        min_price: Minimum valid price
        max_price: Maximum valid price

    Returns:
        ValidationResult with details
    """
    if price_columns is None:
        price_columns = [c for c in data.columns if c in ["open", "high", "low", "close"]]

    errors = []
    warnings = []
    invalid_rows = 0

    for col in price_columns:
        if col not in data.columns:
            continue

        # Check negative prices
        negative_count = (data[col] < min_price).sum()
        if negative_count > 0:
            errors.append(f"{col}: {negative_count} rows with price < {min_price}")
            invalid_rows += negative_count

        # Check unrealistic prices
        high_count = (data[col] > max_price).sum()
        if high_count > 0:
            warnings.append(f"{col}: {high_count} rows with price > {max_price}")

    valid_rows = len(data) - invalid_rows
    is_valid = invalid_rows == 0

    return ValidationResult(
        is_valid=is_valid,
        total_rows=len(data),
        valid_rows=valid_rows,
        invalid_rows=invalid_rows,
        missing_ratio=0.0,
        outlier_ratio=invalid_rows / len(data) if len(data) > 0 else 0.0,
        errors=errors,
        warnings=warnings,
    )


def validate_indicator_ranges(
    data: pd.DataFrame,
) -> ValidationResult:
    """Validate that technical indicators are within expected ranges.

    RSI: 0-100
    ADX: 0-100
    Volume: >= 0
    Bollinger Bands: bb_upper >= bb_middle >= bb_lower

    Args:
        data: Input DataFrame with technical indicators

    Returns:
        ValidationResult with details
    """
    errors: list[str] = []
    warnings: list[str] = []
    invalid_count = 0

    # RSI validation (0-100)
    if "rsi_14" in data.columns:
        rsi_invalid = ((data["rsi_14"] < 0) | (data["rsi_14"] > 100)).sum()
        if rsi_invalid > 0:
            errors.append(f"rsi_14: {rsi_invalid} rows outside [0, 100]")
            invalid_count += rsi_invalid

    # ADX validation (0-100)
    if "adx_14" in data.columns:
        adx_invalid = ((data["adx_14"] < 0) | (data["adx_14"] > 100)).sum()
        if adx_invalid > 0:
            errors.append(f"adx_14: {adx_invalid} rows outside [0, 100]")
            invalid_count += adx_invalid

    # Volume validation (>= 0)
    if "volume" in data.columns:
        vol_invalid = (data["volume"] < 0).sum()
        if vol_invalid > 0:
            errors.append(f"volume: {vol_invalid} rows with negative volume")
            invalid_count += vol_invalid

    # Bollinger Bands validation
    bb_cols = ["bb_upper", "bb_middle", "bb_lower"]
    if all(c in data.columns for c in bb_cols):
        bb_invalid = (
            (data["bb_upper"] < data["bb_middle"]) | (data["bb_middle"] < data["bb_lower"])
        ).sum()
        if bb_invalid > 0:
            errors.append(f"Bollinger Bands: {bb_invalid} rows with invalid ordering")
            invalid_count += bb_invalid

    valid_rows = len(data) - invalid_count
    is_valid = invalid_count == 0

    return ValidationResult(
        is_valid=is_valid,
        total_rows=len(data),
        valid_rows=valid_rows,
        invalid_rows=invalid_count,
        missing_ratio=0.0,
        outlier_ratio=invalid_count / len(data) if len(data) > 0 else 0.0,
        errors=errors,
        warnings=warnings,
    )


def detect_outliers_iqr(
    data: pd.DataFrame,
    columns: list[str] | None = None,
    iqr_multiplier: float = 1.5,
) -> dict[str, np.ndarray]:
    """Detect outliers using the IQR (Interquartile Range) method.

    Outliers are defined as values outside [Q1 - k*IQR, Q3 + k*IQR]
    where k is the iqr_multiplier (default 1.5).

    Args:
        data: Input DataFrame
        columns: Columns to check. If None, checks all numeric columns.
        iqr_multiplier: Multiplier for IQR bounds (default 1.5)

    Returns:
        Dictionary mapping column names to boolean arrays (True = outlier)
    """
    if columns is None:
        columns = list(data.select_dtypes(include=["number"]).columns)

    outliers = {}

    for col in columns:
        if col not in data.columns:
            continue

        q1 = data[col].quantile(0.25)
        q3 = data[col].quantile(0.75)
        iqr = q3 - q1

        lower_bound = q1 - iqr_multiplier * iqr
        upper_bound = q3 + iqr_multiplier * iqr

        outliers[col] = (data[col] < lower_bound) | (data[col] > upper_bound)

    return outliers


def remove_outliers(
    data: pd.DataFrame,
    columns: list[str] | None = None,
    iqr_multiplier: float = 1.5,
    max_outlier_ratio: float = 0.05,
) -> pd.DataFrame:
    """Remove rows containing outliers.

    Args:
        data: Input DataFrame
        columns: Columns to check for outliers
        iqr_multiplier: IQR multiplier for outlier detection
        max_outlier_ratio: Maximum acceptable outlier ratio (raises warning if exceeded)

    Returns:
        DataFrame with outlier rows removed
    """
    initial_rows = len(data)
    outliers = detect_outliers_iqr(data, columns, iqr_multiplier)

    # Create mask for any outlier in any column
    outlier_mask = pd.DataFrame(outliers).any(axis=1)
    outlier_count = outlier_mask.sum()
    outlier_ratio = outlier_count / initial_rows if initial_rows > 0 else 0

    if outlier_ratio > max_outlier_ratio:
        logger.warning(
            f"Outlier ratio {outlier_ratio:.2%} exceeds threshold {max_outlier_ratio:.2%}"
        )

    data_clean = data[~outlier_mask].copy()
    logger.info(f"Removed {outlier_count} outlier rows ({outlier_ratio:.2%})")

    return data_clean


def generate_quality_report(
    data: pd.DataFrame,
    price_columns: list[str] | None = None,
) -> DataQualityReport:
    """Generate comprehensive data quality report.

    Args:
        data: Input DataFrame
        price_columns: Price columns for range validation

    Returns:
        DataQualityReport with detailed metrics
    """
    total_records = len(data)

    # Missing values by column
    missing_by_col = data.isnull().sum().to_dict()
    missing_by_col = {k: v for k, v in missing_by_col.items() if v > 0}

    # Outliers by column
    outliers = detect_outliers_iqr(data)
    outliers_by_col = {col: int(mask.sum()) for col, mask in outliers.items() if mask.sum() > 0}

    # Range violations
    range_violations: dict[str, int] = {}
    validation_errors: list[str] = []

    # Price range validation
    price_result = validate_price_ranges(data, price_columns)
    validation_errors.extend(price_result.errors)

    # Indicator range validation
    indicator_result = validate_indicator_ranges(data)
    validation_errors.extend(indicator_result.errors)

    # Count valid records (no missing values)
    valid_records = len(data.dropna())

    return DataQualityReport(
        total_records=total_records,
        valid_records=valid_records,
        missing_values_by_column=missing_by_col,
        outliers_by_column=outliers_by_col,
        range_violations=range_violations,
        validation_errors=validation_errors,
    )


def validate_dataframe_schema(
    data: pd.DataFrame,
    schema: type[BaseModel],
    sample_size: int = 100,
) -> ValidationResult:
    """Validate DataFrame rows against a Pydantic schema.

    Args:
        data: Input DataFrame
        schema: Pydantic BaseModel class to validate against
        sample_size: Number of rows to validate (for large datasets)

    Returns:
        ValidationResult with validation details
    """
    errors: list[str] = []
    invalid_count = 0

    # Sample data if large
    if len(data) > sample_size:
        sample_data = data.sample(sample_size, random_state=42)
        logger.info(f"Validating sample of {sample_size} rows from {len(data)} total")
    else:
        sample_data = data

    for idx, row in sample_data.iterrows():
        try:
            schema.model_validate(row.to_dict())
        except Exception as e:
            invalid_count += 1
            if len(errors) < 10:  # Limit error messages
                errors.append(f"Row {idx}: {e!s}")

    # Extrapolate to full dataset
    if len(data) > sample_size:
        estimated_invalid = int((invalid_count / sample_size) * len(data))
        logger.info(f"Estimated {estimated_invalid} invalid rows in full dataset")
    else:
        estimated_invalid = invalid_count

    valid_rows = len(data) - estimated_invalid
    is_valid = invalid_count == 0

    return ValidationResult(
        is_valid=is_valid,
        total_rows=len(data),
        valid_rows=valid_rows,
        invalid_rows=estimated_invalid,
        missing_ratio=0.0,
        outlier_ratio=estimated_invalid / len(data) if len(data) > 0 else 0.0,
        errors=errors,
        warnings=[],
    )
