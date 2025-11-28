"""Data validation utilities."""

import pandas as pd
from loguru import logger


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
