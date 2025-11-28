"""State management for rolling window of candles."""

from typing import Any


def is_same_window(candle: dict[str, Any], previous: dict[str, Any]) -> bool:
    """Check if two candles belong to the same time window.

    Args:
        candle: Current candle.
        previous: Previous candle in state.

    Returns:
        True if candles are from the same window.
    """
    return (
        candle["pair"] == previous["pair"]
        and candle["window_start_ms"] == previous["window_start_ms"]
        and candle["window_end_ms"] == previous["window_end_ms"]
    )


def update_candles_state(
    candle: dict[str, Any],
    state: Any,
    max_candles: int,
) -> list[dict[str, Any]]:
    """Update the rolling window of candles in state.

    Handles three cases:
    1. First candle - initialize state
    2. Same window - update existing candle (for intermediate updates)
    3. New window - append new candle

    Args:
        candle: Incoming candle data.
        state: Quixstreams State object.
        max_candles: Maximum number of candles to keep in state.

    Returns:
        Updated list of candles.
    """
    candles: list[dict[str, Any]] = state.get("candles", default=[])

    if not candles:
        # Case 1: First candle ever
        candles.append(candle)
    elif is_same_window(candle, candles[-1]):
        # Case 2: Same window - update with latest data
        candles[-1] = candle
    else:
        # Case 3: New window - append
        candles.append(candle)

    # Maintain rolling window size
    while len(candles) > max_candles:
        candles.pop(0)

    state.set("candles", candles)
    return candles
