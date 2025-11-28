"""Data models for news-sentiment service."""

from pydantic import BaseModel


class SentimentScore(BaseModel):
    """Sentiment score for a single cryptocurrency."""

    coin: str  # e.g., "BTC", "ETH"
    score: int  # -1 (bearish) or +1 (bullish)


class SentimentResult(BaseModel):
    """Result from sentiment extraction."""

    scores: list[SentimentScore]
    reason: str  # Explanation from LLM


class NewsSentimentMessage(BaseModel):
    """Kafka output message format."""

    coin: str
    score: int
    timestamp_ms: int

    def to_dict(self) -> dict:
        """Convert to dictionary for Kafka serialization."""
        return {
            "coin": self.coin,
            "score": self.score,
            "timestamp_ms": self.timestamp_ms,
        }
