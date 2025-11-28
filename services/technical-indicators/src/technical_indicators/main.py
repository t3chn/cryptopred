"""Technical indicators service entry point.

Consumes candles from Kafka, computes technical indicators,
and produces enriched messages to output topic.
"""

import signal
from typing import Any

from loguru import logger
from quixstreams import Application

from technical_indicators.config import config, load_indicators_config
from technical_indicators.indicators import compute_indicators
from technical_indicators.state import update_candles_state

# Global shutdown flag
_shutdown_requested = False


def _signal_handler(signum: int, frame: Any) -> None:
    """Handle shutdown signals gracefully."""
    global _shutdown_requested
    sig_name = signal.Signals(signum).name
    logger.info(f"Received {sig_name}, initiating graceful shutdown...")
    _shutdown_requested = True


def main() -> None:
    """Main entry point for technical indicators service."""
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    # Load indicators configuration
    indicators_config = load_indicators_config()
    max_candles = indicators_config.get("max_candles", 100)

    logger.info(
        f"Starting technical indicators service "
        f"(input: {config.kafka_input_topic}, "
        f"output: {config.kafka_output_topic}, "
        f"candle_seconds: {config.candle_seconds}, "
        f"max_candles: {max_candles})"
    )

    # Log enabled indicators
    enabled = [
        name
        for name, cfg in indicators_config.get("indicators", {}).items()
        if cfg.get("enabled", False)
    ]
    logger.info(f"Enabled indicators: {', '.join(enabled)}")

    app = Application(
        broker_address=config.kafka_broker_address,
        consumer_group=config.kafka_consumer_group,
    )

    # Input topic (candles)
    input_topic = app.topic(
        config.kafka_input_topic,
        value_deserializer="json",
    )

    # Output topic (technical_indicators)
    output_topic = app.topic(
        config.kafka_output_topic,
        value_serializer="json",
    )

    # Create streaming dataframe
    sdf = app.dataframe(topic=input_topic)

    # Filter by candle duration
    sdf = sdf[sdf["candle_seconds"] == config.candle_seconds]

    # Update candles state and compute indicators
    def process_candle(candle: dict[str, Any], state: Any) -> dict[str, Any]:
        """Process a candle: update state and compute indicators."""
        # Update rolling window
        candles = update_candles_state(candle, state, max_candles)

        # Compute indicators
        indicators = compute_indicators(candles, indicators_config)

        # Merge candle with indicators
        return {**candle, **indicators}

    sdf = sdf.apply(process_candle, stateful=True)

    # Log output
    sdf = sdf.update(lambda msg: logger.debug(f"Indicators: {msg['pair']} - {len(msg)} fields"))

    # Produce to output topic
    sdf = sdf.to_topic(output_topic)

    # Start the application
    app.run()


if __name__ == "__main__":
    main()
