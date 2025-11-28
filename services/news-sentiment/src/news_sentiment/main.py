"""News-sentiment service main entry point."""

import sys

from loguru import logger
from quixstreams import Application

from news_sentiment.config import get_config
from news_sentiment.models import NewsSentimentMessage
from news_sentiment.openai_client import OpenAISentimentClient


def main():
    """Run news-sentiment service."""
    # Setup logging
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
    )

    # Load config
    config = get_config()
    logger.info("Starting news-sentiment service")
    logger.info(f"Kafka broker: {config.kafka_broker_address}")
    logger.info(f"Input topic: {config.kafka_input_topic}")
    logger.info(f"Output topic: {config.kafka_output_topic}")
    logger.info(f"OpenAI model: {config.openai_model}")

    # Initialize OpenAI client
    openai_client = OpenAISentimentClient(
        api_key=config.openai_api_key,
        model=config.openai_model,
    )

    # Initialize Kafka application
    app = Application(
        broker_address=config.kafka_broker_address,
        consumer_group=config.kafka_consumer_group,
        auto_offset_reset="earliest",
        loglevel="WARNING",
    )

    input_topic = app.topic(
        name=config.kafka_input_topic,
        value_deserializer="json",
    )
    output_topic = app.topic(
        name=config.kafka_output_topic,
        value_serializer="json",
    )

    # Process messages
    sdf = app.dataframe(topic=input_topic)

    def process_news(message: dict) -> list[dict]:
        """Extract sentiment from news and return list of sentiment messages."""
        title = message.get("title", "")
        description = message.get("description")
        timestamp_ms = message.get("timestamp_ms", 0)

        if not title:
            logger.warning("Empty title in message")
            return []

        # Extract sentiment
        result = openai_client.extract_sentiment(title, description)

        if result.scores:
            logger.info(
                f"Extracted {len(result.scores)} sentiments from: {title[:50]}... "
                f"Reason: {result.reason}"
            )

        # Create output messages
        messages = []
        for score in result.scores:
            msg = NewsSentimentMessage(
                coin=score.coin,
                score=score.score,
                timestamp_ms=timestamp_ms,
            )
            messages.append(msg.to_dict())

        return messages

    # Apply processing and expand results
    sdf = sdf.apply(process_news, expand=True)

    # Output to topic
    sdf = sdf.to_topic(output_topic)

    logger.info("Starting Kafka consumer...")
    app.run()


if __name__ == "__main__":
    main()
