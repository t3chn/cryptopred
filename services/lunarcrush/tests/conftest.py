"""Pytest configuration and fixtures for LunarCrush tests."""

import pytest


@pytest.fixture
def sample_coin_time_series_response() -> dict:
    """Sample response from /public/coins/:coin/time-series/v2."""
    return {
        "config": {
            "coin": "1",
            "topic": "bitcoin",
            "id": "coins:1",
            "name": "Bitcoin",
            "symbol": "BTC",
            "interval": "1w",
            "start": 1763424000,
            "end": 1764115200,
            "bucket": "hour",
            "metrics": [],
            "generated": 1764112848,
        },
        "data": [
            {
                "time": 1763424000,
                "alt_rank": 150,
                "circulating_supply": 19950215,
                "close": 91913,
                "galaxy_score": 53,
                "high": 91913,
                "low": 91161.89,
                "market_cap": 1831844921030,
                "market_dominance": 58.7325,
                "open": 91913,
                "social_dominance": 37.7476,
                "volume_24h": 94214589868,
                "contributors_active": 31448,
                "contributors_created": 2314,
                "interactions": 5075541,
                "posts_active": 61441,
                "posts_created": 3505,
                "sentiment": 75,
                "spam": 5990,
            },
            {
                "time": 1763427600,
                "alt_rank": 148,
                "circulating_supply": 19950220,
                "close": 92100,
                "galaxy_score": 55,
                "high": 92200,
                "low": 91800,
                "market_cap": 1835000000000,
                "market_dominance": 58.8,
                "open": 91913,
                "social_dominance": 38.0,
                "volume_24h": 95000000000,
                "contributors_active": 32000,
                "contributors_created": 2400,
                "interactions": 5100000,
                "posts_active": 62000,
                "posts_created": 3600,
                "sentiment": 77,
                "spam": 6100,
            },
        ],
    }


@pytest.fixture
def sample_topic_time_series_response() -> dict:
    """Sample response from /public/topic/:topic/time-series/v2."""
    return {
        "config": {
            "topic": "bitcoin",
            "id": "bitcoin",
            "name": "Bitcoin",
            "symbol": "BTC",
            "interval": "1w",
            "start": 1763424000,
            "end": 1764115200,
            "bucket": "hour",
            "generated": 1764112845,
        },
        "data": [
            {
                "time": 1763424000,
                "alt_rank": 150,
                "galaxy_score": 53,
                "social_dominance": 37.7476,
                "contributors_active": 31448,
                "interactions": 5075541,
                "posts_active": 61441,
                "sentiment": 75,
                "spam": 5990,
            },
        ],
    }
