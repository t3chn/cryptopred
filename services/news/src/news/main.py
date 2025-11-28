"""News service main entry point."""

import signal
import sys
import time

from loguru import logger
from quixstreams import Application

from news.config import get_config
from news.cryptopanic import CryptoPanicClient

# Global flag for graceful shutdown
_running = True


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    global _running
    logger.info(f"Received signal {signum}, shutting down...")
    _running = False


def main():
    """Run news collector service."""
    global _running

    # Setup logging
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
    )

    # Load config
    config = get_config()
    logger.info(f"Starting news service, polling every {config.polling_interval_sec}s")
    logger.info(f"Kafka broker: {config.kafka_broker_address}")
    logger.info(f"Output topic: {config.kafka_output_topic}")

    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initialize Cryptopanic client
    client = CryptoPanicClient(config.cryptopanic_api_key)

    # Initialize Kafka producer
    app = Application(
        broker_address=config.kafka_broker_address,
        loglevel="WARNING",
    )
    topic = app.topic(
        name=config.kafka_output_topic,
        value_serializer="json",
    )

    try:
        with app.get_producer() as producer:
            logger.info("Connected to Kafka, starting polling loop")

            while _running:
                # Fetch news
                news_items = client.fetch_news()

                # Produce to Kafka
                for news in news_items:
                    message = topic.serialize(
                        key="news",
                        value=news.to_kafka_message(),
                    )
                    producer.produce(
                        topic=topic.name,
                        key=message.key,
                        value=message.value,
                    )
                    logger.debug(f"Produced: {news.title[:50]}...")

                if news_items:
                    producer.flush()
                    logger.info(f"Sent {len(news_items)} news to Kafka")

                # Wait for next poll
                for _ in range(config.polling_interval_sec):
                    if not _running:
                        break
                    time.sleep(1)

    except Exception as e:
        logger.error(f"Error in main loop: {e}")
        raise
    finally:
        client.close()
        logger.info("News service stopped")


if __name__ == "__main__":
    main()
