"""Test fixtures for predictor service."""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_features():
    """Sample feature list."""
    return [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "window_start_ms",
        "sma_7",
        "ema_7",
        "rsi_14",
    ]


@pytest.fixture
def sample_training_data(sample_features):
    """Generate sample training data."""
    n_samples = 100
    np.random.seed(42)

    base_price = 50000
    data = {
        "open": base_price + np.random.randn(n_samples) * 100,
        "high": base_price + np.random.randn(n_samples) * 100 + 50,
        "low": base_price + np.random.randn(n_samples) * 100 - 50,
        "close": base_price + np.random.randn(n_samples) * 100,
        "volume": np.random.rand(n_samples) * 1000,
        "window_start_ms": np.arange(n_samples) * 60000,
        "sma_7": base_price + np.random.randn(n_samples) * 50,
        "ema_7": base_price + np.random.randn(n_samples) * 50,
        "rsi_14": 50 + np.random.randn(n_samples) * 10,
    }

    df = pd.DataFrame(data)
    # Add target (shifted close)
    df["target"] = df["close"].shift(-5)
    df = df.dropna()

    return df
