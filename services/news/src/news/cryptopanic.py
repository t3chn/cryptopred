"""Cryptopanic API client."""

import httpx
from loguru import logger

from news.models import News


class CryptoPanicClient:
    """Client for Cryptopanic news API."""

    BASE_URL = "https://cryptopanic.com/api/developer/v2/posts/"

    def __init__(self, api_key: str):
        """Initialize client with API key."""
        self.api_key = api_key
        self._client = httpx.Client(timeout=30.0)
        self._last_published_at: str | None = None

    def fetch_news(self) -> list[News]:
        """
        Fetch new news articles from Cryptopanic API.

        Returns news published after the last fetch (deduplication).
        """
        all_news: list[News] = []

        try:
            # Fetch first page
            url = self.BASE_URL
            params = {
                "auth_token": self.api_key,
                "public": "true",
            }

            response = self._client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Parse results
            for item in data.get("results", []):
                # Filter only news (not media, etc.)
                if item.get("kind") != "news":
                    continue

                news = News(
                    id=item["id"],
                    title=item["title"],
                    description=item.get("metadata", {}).get("description"),
                    published_at=item["published_at"],
                    created_at=item["created_at"],
                )
                all_news.append(news)

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching news: {e.response.status_code}")
            return []
        except httpx.RequestError as e:
            logger.error(f"Request error fetching news: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching news: {e}")
            return []

        # Sort by published_at ascending
        all_news.sort(key=lambda n: n.published_at)

        # Filter out already seen news
        if self._last_published_at:
            all_news = [n for n in all_news if n.published_at > self._last_published_at]

        # Update last seen timestamp
        if all_news:
            self._last_published_at = all_news[-1].published_at
            logger.info(f"Fetched {len(all_news)} new articles")

        return all_news

    def close(self):
        """Close HTTP client."""
        self._client.close()
