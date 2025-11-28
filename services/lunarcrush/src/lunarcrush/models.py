"""Pydantic models for LunarCrush API responses."""

from pydantic import BaseModel, Field


class CoinTimeSeries(BaseModel):
    """Time series data point for a coin from /public/coins/:coin/time-series/v2."""

    time: int = Field(description="Unix timestamp in seconds")
    alt_rank: int | None = Field(default=None, description="Relative performance vs other assets")
    circulating_supply: float | None = Field(default=None)
    close: float | None = Field(default=None, description="Close price for the time period")
    galaxy_score: float | None = Field(
        default=None, description="Combined technical + social score"
    )
    high: float | None = Field(default=None)
    low: float | None = Field(default=None)
    market_cap: float | None = Field(default=None)
    market_dominance: float | None = Field(default=None, description="% of total market cap")
    open: float | None = Field(default=None)
    social_dominance: float | None = Field(default=None, description="% of total social volume")
    volume_24h: float | None = Field(default=None)
    contributors_active: int | None = Field(
        default=None, description="Unique social accounts with posts"
    )
    contributors_created: int | None = Field(
        default=None, description="Unique social accounts that created new posts"
    )
    interactions: int | None = Field(
        default=None, description="Total social engagement (views, likes, comments, etc.)"
    )
    posts_active: int | None = Field(
        default=None, description="Unique social posts with interactions"
    )
    posts_created: int | None = Field(default=None, description="Unique social posts created")
    sentiment: float | None = Field(
        default=None,
        description="% of posts (weighted by interactions) that are positive. 100% = all positive, 50% = half/half",
    )
    spam: int | None = Field(default=None, description="Posts considered spam")


class TopicTimeSeries(BaseModel):
    """Time series data point for a topic from /public/topic/:topic/time-series/v2."""

    time: int = Field(description="Unix timestamp in seconds")
    alt_rank: int | None = Field(default=None)
    circulating_supply: float | None = Field(default=None)
    close: float | None = Field(default=None)
    galaxy_score: float | None = Field(default=None)
    high: float | None = Field(default=None)
    low: float | None = Field(default=None)
    market_cap: float | None = Field(default=None)
    market_dominance: float | None = Field(default=None)
    open: float | None = Field(default=None)
    social_dominance: float | None = Field(default=None)
    volume_24h: float | None = Field(default=None)
    contributors_active: int | None = Field(default=None)
    contributors_created: int | None = Field(default=None)
    interactions: int | None = Field(default=None)
    posts_active: int | None = Field(default=None)
    posts_created: int | None = Field(default=None)
    sentiment: float | None = Field(default=None)
    spam: int | None = Field(default=None)


class CoinTimeSeriesConfig(BaseModel):
    """Config metadata from API response."""

    coin: str | None = Field(default=None)
    topic: str | None = Field(default=None)
    id: str | None = Field(default=None)
    name: str | None = Field(default=None)
    symbol: str | None = Field(default=None)
    interval: str | None = Field(default=None)
    start: int | None = Field(default=None)
    end: int | None = Field(default=None)
    bucket: str | None = Field(default=None)
    generated: int | None = Field(default=None)


class CoinTimeSeriesResponse(BaseModel):
    """Full response from /public/coins/:coin/time-series/v2."""

    config: CoinTimeSeriesConfig
    data: list[CoinTimeSeries]


class TopicTimeSeriesResponse(BaseModel):
    """Full response from /public/topic/:topic/time-series/v2."""

    config: CoinTimeSeriesConfig
    data: list[TopicTimeSeries]


class LunarCrushMetric(BaseModel):
    """Flattened metric record for Kafka output."""

    coin: str = Field(description="Coin symbol (BTC, ETH, etc.)")
    time: int = Field(description="Unix timestamp in seconds")
    time_ms: int = Field(description="Unix timestamp in milliseconds")
    sentiment: float | None = Field(default=None)
    galaxy_score: float | None = Field(default=None)
    alt_rank: int | None = Field(default=None)
    interactions: int | None = Field(default=None)
    social_dominance: float | None = Field(default=None)
    contributors_active: int | None = Field(default=None)
    posts_active: int | None = Field(default=None)
    spam: int | None = Field(default=None)
    close: float | None = Field(default=None)
    market_cap: float | None = Field(default=None)
    volume_24h: float | None = Field(default=None)

    @classmethod
    def from_coin_time_series(cls, coin: str, ts: CoinTimeSeries) -> "LunarCrushMetric":
        """Create metric from CoinTimeSeries data point."""
        return cls(
            coin=coin,
            time=ts.time,
            time_ms=ts.time * 1000,
            sentiment=ts.sentiment,
            galaxy_score=ts.galaxy_score,
            alt_rank=ts.alt_rank,
            interactions=ts.interactions,
            social_dominance=ts.social_dominance,
            contributors_active=ts.contributors_active,
            posts_active=ts.posts_active,
            spam=ts.spam,
            close=ts.close,
            market_cap=ts.market_cap,
            volume_24h=ts.volume_24h,
        )
