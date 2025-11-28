"""
Candles aggregation service.

Transforms a stream of trades into OHLCV candles using tumbling windows.
"""

import signal
from datetime import timedelta
from typing import Any

from loguru import logger
from quixstreams import Application
from quixstreams.models import TimestampType

# Global shutdown flag for graceful termination
_shutdown_requested = False


def _signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global _shutdown_requested
    sig_name = signal.Signals(signum).name
    logger.info(f"Received {sig_name}, initiating graceful shutdown...")
    _shutdown_requested = True


def custom_ts_extractor(
    value: Any,
    headers: list[tuple[str, bytes]] | None,
    timestamp: float,
    timestamp_type: TimestampType,
) -> int:
    """
    Extract timestamp from message payload instead of Kafka timestamp.
    """
    return value["timestamp_ms"]


def init_candle(trade: dict) -> dict:
    """
    Initialize a candle with the first trade.

    Args:
        trade: The first trade in the window.

    Returns:
        Initial candle state with OHLCV data.
    """
    return {
        "open": trade["price"],
        "high": trade["price"],
        "low": trade["price"],
        "close": trade["price"],
        "volume": trade["quantity"],
        "pair": trade["product_id"],
    }


def update_candle(candle: dict, trade: dict) -> dict:
    """
    Update candle state with a new trade.

    Args:
        candle: Current candle state.
        trade: New trade to incorporate.

    Returns:
        Updated candle state.
    """
    candle["high"] = max(candle["high"], trade["price"])
    candle["low"] = min(candle["low"], trade["price"])
    candle["close"] = trade["price"]
    candle["volume"] += trade["quantity"]
    return candle


def main():
    """Main entry point for the candles service."""
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    from candles.config import config

    logger.info(
        f"Starting candles aggregation service "
        f"(window: {config.candle_seconds}s, "
        f"input: {config.kafka_input_topic}, "
        f"output: {config.kafka_output_topic})"
    )

    app = Application(
        broker_address=config.kafka_broker_address,
        consumer_group=config.kafka_consumer_group,
    )

    # Input topic (trades)
    trades_topic = app.topic(
        config.kafka_input_topic,
        value_deserializer="json",
        timestamp_extractor=custom_ts_extractor,
    )

    # Output topic (candles)
    candles_topic = app.topic(
        config.kafka_output_topic,
        value_serializer="json",
    )

    # Create streaming dataframe from input topic
    sdf = app.dataframe(topic=trades_topic)

    # Aggregate trades into candles using tumbling windows
    sdf = (
        sdf.tumbling_window(timedelta(seconds=config.candle_seconds))
        .reduce(reducer=update_candle, initializer=init_candle)
        .current()  # Emit intermediate candles for responsiveness
    )

    # Extract fields from aggregation result
    sdf["open"] = sdf["value"]["open"]
    sdf["high"] = sdf["value"]["high"]
    sdf["low"] = sdf["value"]["low"]
    sdf["close"] = sdf["value"]["close"]
    sdf["volume"] = sdf["value"]["volume"]
    sdf["pair"] = sdf["value"]["pair"]
    sdf["window_start_ms"] = sdf["start"]
    sdf["window_end_ms"] = sdf["end"]
    sdf["candle_seconds"] = config.candle_seconds

    # Keep only relevant columns
    sdf = sdf[
        [
            "pair",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "window_start_ms",
            "window_end_ms",
            "candle_seconds",
        ]
    ]

    sdf = sdf.update(lambda value: logger.debug(f"Candle: {value}"))

    # Produce candles to output topic
    sdf = sdf.to_topic(candles_topic)

    # Start the streaming application
    app.run()


if __name__ == "__main__":
    main()
