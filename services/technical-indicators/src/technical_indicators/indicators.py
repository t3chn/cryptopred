"""Technical indicators calculation using pandas-ta."""

from typing import Any

import numpy as np
import pandas as pd
import pandas_ta as ta
from loguru import logger


def compute_indicators(
    candles: list[dict[str, Any]],
    indicators_config: dict[str, Any],
) -> dict[str, float | None]:
    """Compute all enabled technical indicators from candle data.

    Args:
        candles: List of OHLCV candle dictionaries.
        indicators_config: Configuration with enabled indicators and their parameters.

    Returns:
        Dictionary of indicator names to their computed values.
    """
    if len(candles) < 2:
        logger.debug(f"Not enough candles for indicators: {len(candles)}")
        return {}

    # Convert to DataFrame
    df = pd.DataFrame(candles)

    # Ensure numeric types
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    result: dict[str, float | None] = {}
    indicators = indicators_config.get("indicators", {})

    # SMA - Simple Moving Average
    if indicators.get("sma", {}).get("enabled", False):
        for period in indicators["sma"].get("periods", []):
            if len(df) >= period:
                sma = ta.sma(df["close"], length=period)
                result[f"sma_{period}"] = _safe_last(sma)

    # EMA - Exponential Moving Average
    if indicators.get("ema", {}).get("enabled", False):
        for period in indicators["ema"].get("periods", []):
            if len(df) >= period:
                ema = ta.ema(df["close"], length=period)
                result[f"ema_{period}"] = _safe_last(ema)

    # RSI - Relative Strength Index
    if indicators.get("rsi", {}).get("enabled", False):
        for period in indicators["rsi"].get("periods", []):
            if len(df) >= period + 1:
                rsi = ta.rsi(df["close"], length=period)
                result[f"rsi_{period}"] = _safe_last(rsi)

    # MACD - Moving Average Convergence Divergence
    if indicators.get("macd", {}).get("enabled", False):
        macd_config = indicators["macd"]
        fast = macd_config.get("fast", 12)
        slow = macd_config.get("slow", 26)
        signal = macd_config.get("signal", 9)

        if len(df) >= slow:
            macd_df = ta.macd(df["close"], fast=fast, slow=slow, signal=signal)
            if macd_df is not None and not macd_df.empty:
                result["macd"] = _safe_last(macd_df.iloc[:, 0])
                result["macd_hist"] = _safe_last(macd_df.iloc[:, 1])
                result["macd_signal"] = _safe_last(macd_df.iloc[:, 2])

    # Bollinger Bands
    if indicators.get("bbands", {}).get("enabled", False):
        bbands_config = indicators["bbands"]
        period = bbands_config.get("period", 20)
        std = bbands_config.get("std", 2.0)

        if len(df) >= period:
            bbands = ta.bbands(df["close"], length=period, std=std)
            if bbands is not None and not bbands.empty:
                result["bb_lower"] = _safe_last(bbands.iloc[:, 0])
                result["bb_middle"] = _safe_last(bbands.iloc[:, 1])
                result["bb_upper"] = _safe_last(bbands.iloc[:, 2])

    # Stochastic Oscillator
    if indicators.get("stoch", {}).get("enabled", False):
        stoch_config = indicators["stoch"]
        k = stoch_config.get("k", 14)
        d = stoch_config.get("d", 3)

        if len(df) >= k:
            stoch = ta.stoch(df["high"], df["low"], df["close"], k=k, d=d)
            if stoch is not None and not stoch.empty:
                result["stoch_k"] = _safe_last(stoch.iloc[:, 0])
                result["stoch_d"] = _safe_last(stoch.iloc[:, 1])

    # ATR - Average True Range
    if indicators.get("atr", {}).get("enabled", False):
        period = indicators["atr"].get("period", 14)

        if len(df) >= period:
            atr = ta.atr(df["high"], df["low"], df["close"], length=period)
            result[f"atr_{period}"] = _safe_last(atr)

    # OBV - On-Balance Volume
    if indicators.get("obv", {}).get("enabled", False):
        if len(df) >= 2:
            obv = ta.obv(df["close"], df["volume"])
            result["obv"] = _safe_last(obv)

    return result


def _safe_last(series: pd.Series | None) -> float | None:
    """Safely get the last value from a pandas Series.

    Args:
        series: Pandas Series or None.

    Returns:
        Last value as float, or None if not available.
    """
    if series is None or series.empty:
        return None

    last_value = series.iloc[-1]

    if pd.isna(last_value) or np.isinf(last_value):
        return None

    return float(last_value)
