"""Main entry points for LunarCrush service."""

import asyncio
import time

from loguru import logger
from quixstreams import Application

from lunarcrush.client import LunarCrushClient
from lunarcrush.config import config
from lunarcrush.models import LunarCrushMetric


async def backfill_coin_to_kafka(
    client: LunarCrushClient,
    app: Application,
    coin: str,
    last_n_days: int,
    bucket: str = "hour",
) -> int:
    """
    Fetch historical data for a coin and send to Kafka.

    Args:
        client: LunarCrush API client
        app: Quix Streams application
        coin: Coin symbol (BTC, ETH, etc.)
        last_n_days: Number of days to backfill
        bucket: Time bucket (hour or day)

    Returns:
        Number of records sent
    """
    end_ts = int(time.time())
    start_ts = end_ts - (last_n_days * 24 * 60 * 60)

    logger.info(f"Backfilling {coin} from {start_ts} to {end_ts} ({last_n_days} days)")

    try:
        data = await client.get_coin_time_series(
            coin=coin,
            bucket=bucket,
            start=start_ts,
            end=end_ts,
        )
    except Exception as e:
        logger.error(f"Failed to fetch data for {coin}: {e}")
        return 0

    if not data:
        logger.warning(f"No data returned for {coin}")
        return 0

    # Create producer and send records
    with app.get_producer() as producer:
        topic = app.topic(name=config.kafka_topic_name)

        for ts in data:
            metric = LunarCrushMetric.from_coin_time_series(coin, ts)
            message = topic.serialize(
                key=f"{coin}:{ts.time}",
                value=metric.model_dump(),
            )
            producer.produce(
                topic=topic.name,
                key=message.key,
                value=message.value,
            )

        producer.flush()

    logger.info(f"Sent {len(data)} records for {coin} to Kafka")
    return len(data)


async def backfill_all_coins(
    client: LunarCrushClient,
    app: Application,
    coins: list[str],
    last_n_days: int,
    bucket: str = "hour",
) -> dict[str, int]:
    """
    Backfill historical data for all coins.

    Args:
        client: LunarCrush API client
        app: Quix Streams application
        coins: List of coin symbols
        last_n_days: Number of days to backfill
        bucket: Time bucket

    Returns:
        Dictionary of {coin: records_sent}
    """
    results = {}

    for coin in coins:
        count = await backfill_coin_to_kafka(client, app, coin, last_n_days, bucket)
        results[coin] = count
        # Small delay between coins to avoid rate limiting
        await asyncio.sleep(2)

    return results


async def run_backfill():
    """Run the backfill process."""
    logger.info(f"Starting LunarCrush backfill for {len(config.coins)} coins")
    logger.info(f"Kafka broker: {config.kafka_broker_address}")
    logger.info(f"Topic: {config.kafka_topic_name}")
    logger.info(f"Last {config.last_n_days} days, bucket: {config.bucket}")

    app = Application(
        broker_address=config.kafka_broker_address,
        loglevel="WARNING",
    )

    async with LunarCrushClient.from_config(config) as client:
        results = await backfill_all_coins(
            client=client,
            app=app,
            coins=config.coins,
            last_n_days=config.last_n_days,
            bucket=config.bucket,
        )

    total = sum(results.values())
    logger.info(f"Backfill complete. Total records: {total}")
    for coin, count in results.items():
        logger.info(f"  {coin}: {count} records")


async def run_live():
    """
    Run live mode - periodically fetch latest data and send to Kafka.

    This fetches the last hour of data every hour to keep metrics up to date.
    """
    logger.info(f"Starting LunarCrush live mode for {len(config.coins)} coins")

    app = Application(
        broker_address=config.kafka_broker_address,
        loglevel="WARNING",
    )

    async with LunarCrushClient.from_config(config) as client:
        while True:
            try:
                # Fetch last 2 hours to ensure overlap
                for coin in config.coins:
                    await backfill_coin_to_kafka(
                        client=client,
                        app=app,
                        coin=coin,
                        last_n_days=0,  # Will use interval instead
                        bucket="hour",
                    )
                    await asyncio.sleep(2)

                # Wait 1 hour before next fetch
                logger.info("Sleeping for 1 hour before next fetch")
                await asyncio.sleep(3600)

            except Exception as e:
                logger.error(f"Error in live mode: {e}")
                await asyncio.sleep(60)


def backfill_main():
    """Entry point for backfill command."""
    asyncio.run(run_backfill())


def main():
    """Main entry point - runs in configured mode."""
    if config.live_or_historical == "historical":
        asyncio.run(run_backfill())
    else:
        asyncio.run(run_live())


if __name__ == "__main__":
    main()
