"""
Trades service entry point.

Fetches trade data from Binance Futures API and pushes to Kafka.
Supports both live (WebSocket) and historical (REST API) modes.
"""

import asyncio
import signal

from loguru import logger
from quixstreams import Application

from trades.binance_client import BinanceHistoricalClient, BinanceLiveClient

# Global shutdown flag for graceful termination
_shutdown_requested = False


def _signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global _shutdown_requested
    sig_name = signal.Signals(signum).name
    logger.info(f"Received {sig_name}, initiating graceful shutdown...")
    _shutdown_requested = True


async def run_live(
    kafka_broker_address: str,
    kafka_topic_name: str,
    client: BinanceLiveClient,
):
    """
    Async main loop for live WebSocket data.

    Fetches trades from WebSocket and pushes to Kafka.
    """
    app = Application(broker_address=kafka_broker_address)
    topic = app.topic(name=kafka_topic_name, value_serializer="json")

    await client.start()

    try:
        with app.get_producer() as producer:
            while not client.is_done() and not _shutdown_requested:
                trades = await client.get_trades_async()

                for trade in trades:
                    message = topic.serialize(key=trade.product_id, value=trade.to_dict())
                    producer.produce(topic=topic.name, value=message.value, key=message.key)
                    logger.debug(f"Trade pushed to Kafka: {trade.product_id} @ {trade.price}")

    except asyncio.CancelledError:
        logger.info("Task cancelled")
    finally:
        await client.stop()


def run_historical(
    kafka_broker_address: str,
    kafka_topic_name: str,
    client: BinanceHistoricalClient,
):
    """
    Sync main loop for historical REST API data.

    Fetches trades from REST API and pushes to Kafka.
    """
    app = Application(broker_address=kafka_broker_address)
    topic = app.topic(name=kafka_topic_name, value_serializer="json")

    with app.get_producer() as producer:
        while not client.is_done() and not _shutdown_requested:
            trades = client.get_trades()

            for trade in trades:
                message = topic.serialize(key=trade.product_id, value=trade.to_dict())
                producer.produce(topic=topic.name, value=message.value, key=message.key)
                logger.debug(f"Trade pushed to Kafka: {trade.product_id} @ {trade.price}")

    logger.info("Historical data ingestion complete")


def main():
    """Main entry point."""
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    from trades.config import config

    if config.live_or_historical == "live":
        logger.info(f"Starting live data ingestion for {len(config.product_ids)} symbols")
        client = BinanceLiveClient(config)
        asyncio.run(
            run_live(
                kafka_broker_address=config.kafka_broker_address,
                kafka_topic_name=config.kafka_topic_name,
                client=client,
            )
        )

    elif config.live_or_historical == "historical":
        logger.info(
            f"Starting historical data ingestion for {len(config.product_ids)} symbols, "
            f"last {config.last_n_days} days"
        )
        client = BinanceHistoricalClient(config)
        run_historical(
            kafka_broker_address=config.kafka_broker_address,
            kafka_topic_name=config.kafka_topic_name,
            client=client,
        )

    else:
        raise ValueError('Invalid value for live_or_historical. Must be "live" or "historical".')


if __name__ == "__main__":
    main()
