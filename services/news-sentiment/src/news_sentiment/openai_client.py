"""OpenAI client for sentiment extraction."""

import json

from loguru import logger
from openai import OpenAI

from news_sentiment.models import SentimentResult, SentimentScore

SYSTEM_PROMPT = """You are an expert crypto financial analyst. Analyze the news headline and extract sentiment scores for mentioned cryptocurrencies.

Rules:
- Only include coins explicitly mentioned or directly affected by the news
- Score: +1 for bullish/positive news, -1 for bearish/negative news
- If no crypto relevance or unclear sentiment, return empty scores list
- Be conservative - don't over-interpret or speculate
- Use standard ticker symbols (BTC, ETH, SOL, XRP, etc.)

You must respond with valid JSON in this exact format:
{"scores": [{"coin": "BTC", "score": 1}], "reason": "Brief explanation"}

Examples:
- "Bitcoin ETF approved" -> {"scores": [{"coin": "BTC", "score": 1}], "reason": "ETF approval is bullish for BTC adoption"}
- "Ethereum network fees hit new lows" -> {"scores": [{"coin": "ETH", "score": 1}], "reason": "Lower fees increase ETH usability"}
- "Major exchange hacked" -> {"scores": [], "reason": "General market news, no specific coin impact"}"""


class OpenAISentimentClient:
    """Client for extracting sentiment using OpenAI."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """Initialize OpenAI client."""
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def extract_sentiment(self, title: str, description: str | None = None) -> SentimentResult:
        """
        Extract sentiment scores from news text.

        Args:
            title: News headline
            description: Optional news description

        Returns:
            SentimentResult with scores and reason
        """
        # Combine title and description
        text = title
        if description:
            text = f"{title}\n\n{description}"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                response_format={"type": "json_object"},
                max_tokens=200,
                temperature=0.1,  # Low temperature for consistent results
            )

            # Parse response
            content = response.choices[0].message.content
            if not content:
                logger.warning("Empty response from OpenAI")
                return SentimentResult(scores=[], reason="No response")

            data = json.loads(content)

            # Validate and create result
            scores = [
                SentimentScore(coin=s["coin"].upper(), score=int(s["score"]))
                for s in data.get("scores", [])
                if s.get("coin") and s.get("score") in [-1, 1, "-1", "1"]
            ]

            return SentimentResult(
                scores=scores,
                reason=data.get("reason", ""),
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response: {e}")
            return SentimentResult(scores=[], reason=f"Parse error: {e}")
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return SentimentResult(scores=[], reason=f"API error: {e}")
