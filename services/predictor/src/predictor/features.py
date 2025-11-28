"""Feature engineering for predictor service.

This module provides functions to add additional features to the training data:
- Time-based features (hour, day_of_week, peak hours)
- LunarCrush sentiment/social features integration
"""

import numpy as np
import pandas as pd
from loguru import logger


def add_time_features(df: pd.DataFrame, timestamp_col: str = "window_start_ms") -> pd.DataFrame:
    """Add time-based features to dataframe.

    Research shows crypto trading has patterns:
    - 16:00-17:00 UTC is peak activity
    - Monday and Wednesday tend to have stronger moves

    Args:
        df: Input dataframe with timestamp column
        timestamp_col: Name of timestamp column (milliseconds)

    Returns:
        DataFrame with additional time features
    """
    logger.info(f"Adding time features based on {timestamp_col}")

    # Convert milliseconds to datetime
    dt = pd.to_datetime(df[timestamp_col], unit="ms", utc=True)

    # Extract time components
    df["hour"] = dt.dt.hour
    df["day_of_week"] = dt.dt.dayofweek  # Monday=0, Sunday=6
    df["day_of_month"] = dt.dt.day
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

    # Peak trading hours (16:00-17:00 UTC)
    df["is_peak_hour"] = df["hour"].isin([15, 16, 17]).astype(int)

    # Strong days (Monday, Wednesday based on research)
    df["is_strong_day"] = df["day_of_week"].isin([0, 2]).astype(int)

    # Cyclical encoding for hour and day (sin/cos transform)
    # This helps models understand that hour 23 is close to hour 0
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    df["dow_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
    df["dow_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)

    logger.info("Added 10 time features")
    return df


def add_lunarcrush_features(
    df: pd.DataFrame,
    lunarcrush_df: pd.DataFrame,
    timestamp_col: str = "window_start_ms",
    lc_timestamp_col: str = "time_ms",
) -> pd.DataFrame:
    """Add LunarCrush sentiment/social features to dataframe.

    Research shows sentiment features can improve accuracy by 18-30%.

    Args:
        df: Input dataframe with timestamp column
        lunarcrush_df: LunarCrush metrics dataframe with columns:
            - time_ms: timestamp in milliseconds
            - sentiment: % positive posts (0-100)
            - galaxy_score: combined technical + social score
            - alt_rank: performance vs other assets
            - interactions: social engagement count
            - social_dominance: % of total social volume
        timestamp_col: Name of timestamp column in df (milliseconds)
        lc_timestamp_col: Name of timestamp column in lunarcrush_df

    Returns:
        DataFrame with additional LunarCrush features
    """
    if lunarcrush_df.empty:
        logger.warning("LunarCrush dataframe is empty, skipping sentiment features")
        return df

    logger.info(f"Adding LunarCrush features from {len(lunarcrush_df)} records")

    # Ensure timestamp columns are numeric
    df[timestamp_col] = pd.to_numeric(df[timestamp_col])
    lunarcrush_df = lunarcrush_df.copy()
    lunarcrush_df[lc_timestamp_col] = pd.to_numeric(lunarcrush_df[lc_timestamp_col])

    # Round to nearest hour for merging (LunarCrush provides hourly data)
    hour_ms = 3600 * 1000
    df["_merge_ts"] = (df[timestamp_col] // hour_ms) * hour_ms
    lunarcrush_df["_merge_ts"] = (lunarcrush_df[lc_timestamp_col] // hour_ms) * hour_ms

    # Select LunarCrush columns to merge
    lc_cols = ["_merge_ts"]
    for col in ["sentiment", "galaxy_score", "alt_rank", "interactions", "social_dominance"]:
        if col in lunarcrush_df.columns:
            lc_cols.append(col)

    # Merge on rounded timestamp
    df = df.merge(
        lunarcrush_df[lc_cols].drop_duplicates(subset=["_merge_ts"]),
        on="_merge_ts",
        how="left",
    )
    df.drop(columns=["_merge_ts"], inplace=True)

    # Add lag features (sentiment often leads price by 1-4 hours)
    if "sentiment" in df.columns:
        for lag in [1, 2, 4]:
            df[f"sentiment_lag_{lag}h"] = df["sentiment"].shift(lag)
            if "galaxy_score" in df.columns:
                df[f"galaxy_score_lag_{lag}h"] = df["galaxy_score"].shift(lag)

    # Add rolling features
    if "sentiment" in df.columns:
        df["sentiment_ma_24h"] = df["sentiment"].rolling(24, min_periods=1).mean()
        df["sentiment_std_24h"] = df["sentiment"].rolling(24, min_periods=1).std()

    if "interactions" in df.columns:
        df["interactions_ma_24h"] = df["interactions"].rolling(24, min_periods=1).mean()

    n_features = len(
        [
            c
            for c in df.columns
            if c.startswith(("sentiment", "galaxy", "alt_rank", "interactions", "social"))
        ]
    )
    logger.info(f"Added {n_features} LunarCrush features")

    return df


def get_time_feature_names() -> list[str]:
    """Get list of time feature column names.

    Returns:
        List of feature names added by add_time_features
    """
    return [
        "hour",
        "day_of_week",
        "day_of_month",
        "is_weekend",
        "is_peak_hour",
        "is_strong_day",
        "hour_sin",
        "hour_cos",
        "dow_sin",
        "dow_cos",
    ]


def get_lunarcrush_feature_names() -> list[str]:
    """Get list of LunarCrush feature column names.

    Returns:
        List of feature names added by add_lunarcrush_features
    """
    return [
        "sentiment",
        "galaxy_score",
        "alt_rank",
        "interactions",
        "social_dominance",
        "sentiment_lag_1h",
        "sentiment_lag_2h",
        "sentiment_lag_4h",
        "galaxy_score_lag_1h",
        "galaxy_score_lag_2h",
        "galaxy_score_lag_4h",
        "sentiment_ma_24h",
        "sentiment_std_24h",
        "interactions_ma_24h",
    ]
