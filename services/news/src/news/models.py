"""Data models for news service."""

from datetime import datetime

from pydantic import BaseModel


class News(BaseModel):
    """News article from Cryptopanic API."""

    id: int
    title: str
    description: str | None = None
    published_at: str  # ISO 8601 format
    created_at: str  # ISO 8601 format

    @property
    def timestamp_ms(self) -> int:
        """Convert published_at to Unix milliseconds."""
        # Parse ISO 8601 format (e.g., "2024-12-18T12:29:27Z")
        dt = datetime.fromisoformat(self.published_at.replace("Z", "+00:00"))
        return int(dt.timestamp() * 1000)

    def to_kafka_message(self) -> dict:
        """Convert to Kafka message format."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "published_at": self.published_at,
            "timestamp_ms": self.timestamp_ms,
        }
