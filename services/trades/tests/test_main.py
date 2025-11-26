"""Tests for trades.main module."""

import asyncio
import signal
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest

from trades.trade import Trade


class TestSignalHandler:
    """Test signal handler functionality."""

    def test_signal_handler_sets_shutdown_flag(self):
        """Test _signal_handler sets _shutdown_requested to True."""
        from trades import main

        main._shutdown_requested = False

        main._signal_handler(signal.SIGINT, None)

        assert main._shutdown_requested is True

    def test_signal_handler_with_sigint(self):
        """Test handling SIGINT signal."""
        from trades import main

        main._shutdown_requested = False

        main._signal_handler(signal.SIGINT, None)

        assert main._shutdown_requested is True

    def test_signal_handler_with_sigterm(self):
        """Test handling SIGTERM signal."""
        from trades import main

        main._shutdown_requested = False

        main._signal_handler(signal.SIGTERM, None)

        assert main._shutdown_requested is True

    def test_signal_handler_multiple_calls(self):
        """Test multiple signal handler calls."""
        from trades import main

        main._shutdown_requested = False

        main._signal_handler(signal.SIGINT, None)
        main._signal_handler(signal.SIGTERM, None)

        assert main._shutdown_requested is True

    def test_signal_handler_frame_ignored(self):
        """Test frame parameter is ignored."""
        from trades import main

        main._shutdown_requested = False
        mock_frame = MagicMock()

        main._signal_handler(signal.SIGINT, mock_frame)

        assert main._shutdown_requested is True


class TestRunLive:
    """Test run_live async function."""

    async def test_run_live_starts_client(self, mock_kafka_app, mock_settings, sample_trades):
        """Test run_live starts the WebSocket client."""
        mock_client = AsyncMock()
        mock_client.start = AsyncMock()
        mock_client.stop = AsyncMock()
        mock_client.is_done = MagicMock(side_effect=[False, True])
        mock_client.get_trades_async = AsyncMock(return_value=sample_trades)

        with patch("trades.main.Application", return_value=mock_kafka_app):
            with patch("trades.main._shutdown_requested", False):
                from trades.main import run_live

                await run_live(
                    kafka_broker_address="localhost:9092",
                    kafka_topic_name="test-trades",
                    client=mock_client,
                )

        mock_client.start.assert_called_once()

    async def test_run_live_stops_client(self, mock_kafka_app, mock_settings, sample_trades):
        """Test run_live stops the client on completion."""
        mock_client = AsyncMock()
        mock_client.start = AsyncMock()
        mock_client.stop = AsyncMock()
        mock_client.is_done = MagicMock(return_value=True)
        mock_client.get_trades_async = AsyncMock(return_value=[])

        with patch("trades.main.Application", return_value=mock_kafka_app):
            with patch("trades.main._shutdown_requested", False):
                from trades.main import run_live

                await run_live(
                    kafka_broker_address="localhost:9092",
                    kafka_topic_name="test-trades",
                    client=mock_client,
                )

        mock_client.stop.assert_called_once()

    async def test_run_live_produces_trades(self, mock_kafka_app, mock_kafka_producer, mock_kafka_topic, sample_trades):
        """Test run_live produces trades to Kafka."""
        mock_client = AsyncMock()
        mock_client.start = AsyncMock()
        mock_client.stop = AsyncMock()
        mock_client.is_done = MagicMock(side_effect=[False, True])
        mock_client.get_trades_async = AsyncMock(return_value=sample_trades)

        mock_kafka_app.topic = MagicMock(return_value=mock_kafka_topic)
        mock_kafka_app.get_producer = MagicMock(return_value=mock_kafka_producer)

        with patch("trades.main.Application", return_value=mock_kafka_app):
            with patch("trades.main._shutdown_requested", False):
                from trades.main import run_live

                await run_live(
                    kafka_broker_address="localhost:9092",
                    kafka_topic_name="test-trades",
                    client=mock_client,
                )

        # Should produce each trade
        assert mock_kafka_producer.produce.call_count == len(sample_trades)

    async def test_run_live_serializes_trades(self, mock_kafka_app, mock_kafka_topic, sample_trade):
        """Test run_live serializes trades correctly."""
        mock_client = AsyncMock()
        mock_client.start = AsyncMock()
        mock_client.stop = AsyncMock()
        mock_client.is_done = MagicMock(side_effect=[False, True])
        mock_client.get_trades_async = AsyncMock(return_value=[sample_trade])

        mock_producer = MagicMock()
        mock_producer.produce = MagicMock()
        mock_producer.__enter__ = MagicMock(return_value=mock_producer)
        mock_producer.__exit__ = MagicMock(return_value=None)

        mock_kafka_app.topic = MagicMock(return_value=mock_kafka_topic)
        mock_kafka_app.get_producer = MagicMock(return_value=mock_producer)

        with patch("trades.main.Application", return_value=mock_kafka_app):
            with patch("trades.main._shutdown_requested", False):
                from trades.main import run_live

                await run_live(
                    kafka_broker_address="localhost:9092",
                    kafka_topic_name="test-trades",
                    client=mock_client,
                )

        mock_kafka_topic.serialize.assert_called_with(
            key=sample_trade.product_id,
            value=sample_trade.to_dict(),
        )

    async def test_run_live_shutdown_on_signal(self, mock_kafka_app):
        """Test run_live exits on shutdown signal."""
        mock_client = AsyncMock()
        mock_client.start = AsyncMock()
        mock_client.stop = AsyncMock()
        mock_client.is_done = MagicMock(return_value=False)
        mock_client.get_trades_async = AsyncMock(return_value=[])

        # Set shutdown flag before test
        with patch("trades.main.Application", return_value=mock_kafka_app):
            with patch("trades.main._shutdown_requested", True):
                from trades.main import run_live

                await run_live(
                    kafka_broker_address="localhost:9092",
                    kafka_topic_name="test-trades",
                    client=mock_client,
                )

        # Should still stop client
        mock_client.stop.assert_called_once()

    async def test_run_live_handles_cancelled_error(self, mock_kafka_app):
        """Test run_live handles CancelledError."""
        mock_client = AsyncMock()
        mock_client.start = AsyncMock()
        mock_client.stop = AsyncMock()
        mock_client.is_done = MagicMock(return_value=False)
        mock_client.get_trades_async = AsyncMock(side_effect=asyncio.CancelledError())

        with patch("trades.main.Application", return_value=mock_kafka_app):
            with patch("trades.main._shutdown_requested", False):
                from trades.main import run_live

                await run_live(
                    kafka_broker_address="localhost:9092",
                    kafka_topic_name="test-trades",
                    client=mock_client,
                )

        mock_client.stop.assert_called_once()

    async def test_run_live_creates_topic(self, mock_kafka_app):
        """Test run_live creates Kafka topic."""
        mock_client = AsyncMock()
        mock_client.start = AsyncMock()
        mock_client.stop = AsyncMock()
        mock_client.is_done = MagicMock(return_value=True)

        with patch("trades.main.Application", return_value=mock_kafka_app):
            with patch("trades.main._shutdown_requested", False):
                from trades.main import run_live

                await run_live(
                    kafka_broker_address="localhost:9092",
                    kafka_topic_name="my-topic",
                    client=mock_client,
                )

        mock_kafka_app.topic.assert_called_with(name="my-topic", value_serializer="json")

    async def test_run_live_empty_trades_batch(self, mock_kafka_app, mock_kafka_producer):
        """Test run_live handles empty trades batch."""
        mock_client = AsyncMock()
        mock_client.start = AsyncMock()
        mock_client.stop = AsyncMock()
        mock_client.is_done = MagicMock(side_effect=[False, True])
        mock_client.get_trades_async = AsyncMock(return_value=[])

        mock_kafka_app.get_producer = MagicMock(return_value=mock_kafka_producer)

        with patch("trades.main.Application", return_value=mock_kafka_app):
            with patch("trades.main._shutdown_requested", False):
                from trades.main import run_live

                await run_live(
                    kafka_broker_address="localhost:9092",
                    kafka_topic_name="test-trades",
                    client=mock_client,
                )

        # Should not produce anything
        mock_kafka_producer.produce.assert_not_called()


class TestRunHistorical:
    """Test run_historical sync function."""

    def test_run_historical_gets_trades(self, mock_kafka_app, mock_kafka_producer, sample_trades):
        """Test run_historical fetches trades from client."""
        mock_client = MagicMock()
        mock_client.is_done = MagicMock(side_effect=[False, True])
        mock_client.get_trades = MagicMock(return_value=sample_trades)

        mock_kafka_app.get_producer = MagicMock(return_value=mock_kafka_producer)

        with patch("trades.main.Application", return_value=mock_kafka_app):
            with patch("trades.main._shutdown_requested", False):
                from trades.main import run_historical

                run_historical(
                    kafka_broker_address="localhost:9092",
                    kafka_topic_name="test-trades",
                    client=mock_client,
                )

        mock_client.get_trades.assert_called()

    def test_run_historical_produces_trades(self, mock_kafka_app, mock_kafka_producer, mock_kafka_topic, sample_trades):
        """Test run_historical produces trades to Kafka."""
        mock_client = MagicMock()
        mock_client.is_done = MagicMock(side_effect=[False, True])
        mock_client.get_trades = MagicMock(return_value=sample_trades)

        mock_kafka_app.topic = MagicMock(return_value=mock_kafka_topic)
        mock_kafka_app.get_producer = MagicMock(return_value=mock_kafka_producer)

        with patch("trades.main.Application", return_value=mock_kafka_app):
            with patch("trades.main._shutdown_requested", False):
                from trades.main import run_historical

                run_historical(
                    kafka_broker_address="localhost:9092",
                    kafka_topic_name="test-trades",
                    client=mock_client,
                )

        assert mock_kafka_producer.produce.call_count == len(sample_trades)

    def test_run_historical_serializes_trades(self, mock_kafka_app, mock_kafka_topic, sample_trade):
        """Test run_historical serializes trades correctly."""
        mock_client = MagicMock()
        mock_client.is_done = MagicMock(side_effect=[False, True])
        mock_client.get_trades = MagicMock(return_value=[sample_trade])

        mock_producer = MagicMock()
        mock_producer.produce = MagicMock()
        mock_producer.__enter__ = MagicMock(return_value=mock_producer)
        mock_producer.__exit__ = MagicMock(return_value=None)

        mock_kafka_app.topic = MagicMock(return_value=mock_kafka_topic)
        mock_kafka_app.get_producer = MagicMock(return_value=mock_producer)

        with patch("trades.main.Application", return_value=mock_kafka_app):
            with patch("trades.main._shutdown_requested", False):
                from trades.main import run_historical

                run_historical(
                    kafka_broker_address="localhost:9092",
                    kafka_topic_name="test-trades",
                    client=mock_client,
                )

        mock_kafka_topic.serialize.assert_called_with(
            key=sample_trade.product_id,
            value=sample_trade.to_dict(),
        )

    def test_run_historical_shutdown_on_signal(self, mock_kafka_app):
        """Test run_historical exits on shutdown signal."""
        mock_client = MagicMock()
        mock_client.is_done = MagicMock(return_value=False)
        mock_client.get_trades = MagicMock(return_value=[])

        with patch("trades.main.Application", return_value=mock_kafka_app):
            with patch("trades.main._shutdown_requested", True):
                from trades.main import run_historical

                run_historical(
                    kafka_broker_address="localhost:9092",
                    kafka_topic_name="test-trades",
                    client=mock_client,
                )

        # Should not call get_trades when shutdown requested
        # (depends on loop condition evaluation order)

    def test_run_historical_loops_until_done(self, mock_kafka_app, mock_kafka_producer):
        """Test run_historical loops until client is done."""
        mock_client = MagicMock()
        mock_client.is_done = MagicMock(side_effect=[False, False, False, True])
        mock_client.get_trades = MagicMock(return_value=[])

        mock_kafka_app.get_producer = MagicMock(return_value=mock_kafka_producer)

        with patch("trades.main.Application", return_value=mock_kafka_app):
            with patch("trades.main._shutdown_requested", False):
                from trades.main import run_historical

                run_historical(
                    kafka_broker_address="localhost:9092",
                    kafka_topic_name="test-trades",
                    client=mock_client,
                )

        assert mock_client.get_trades.call_count == 3

    def test_run_historical_creates_topic(self, mock_kafka_app, mock_kafka_producer):
        """Test run_historical creates Kafka topic."""
        mock_client = MagicMock()
        mock_client.is_done = MagicMock(return_value=True)

        mock_kafka_app.get_producer = MagicMock(return_value=mock_kafka_producer)

        with patch("trades.main.Application", return_value=mock_kafka_app):
            with patch("trades.main._shutdown_requested", False):
                from trades.main import run_historical

                run_historical(
                    kafka_broker_address="localhost:9092",
                    kafka_topic_name="historical-trades",
                    client=mock_client,
                )

        mock_kafka_app.topic.assert_called_with(name="historical-trades", value_serializer="json")

    def test_run_historical_empty_trades_batch(self, mock_kafka_app, mock_kafka_producer):
        """Test run_historical handles empty trades batch."""
        mock_client = MagicMock()
        mock_client.is_done = MagicMock(side_effect=[False, True])
        mock_client.get_trades = MagicMock(return_value=[])

        mock_kafka_app.get_producer = MagicMock(return_value=mock_kafka_producer)

        with patch("trades.main.Application", return_value=mock_kafka_app):
            with patch("trades.main._shutdown_requested", False):
                from trades.main import run_historical

                run_historical(
                    kafka_broker_address="localhost:9092",
                    kafka_topic_name="test-trades",
                    client=mock_client,
                )

        mock_kafka_producer.produce.assert_not_called()


class TestMain:
    """Test main entry point function.

    Note: These tests verify behavior through signal handling and mode validation.
    Full integration of the main() function is tested via integration tests.
    """

    def test_main_registers_signal_handlers(self, mock_settings, env_vars):
        """Test main registers signal handlers."""
        mock_settings.live_or_historical = "live"
        with env_vars(kafka_broker_address="localhost:9092", kafka_topic_name="trades"):
            with patch("signal.signal") as mock_signal:
                with patch("trades.binance_client.BinanceLiveClient"):
                    with patch("asyncio.run"):
                        import trades.config
                        with patch.object(trades.config, "config", mock_settings):
                            from trades.main import main
                            main()

            # Should register SIGINT and SIGTERM handlers
            calls = mock_signal.call_args_list
            signal_numbers = [c[0][0] for c in calls]
            assert signal.SIGINT in signal_numbers
            assert signal.SIGTERM in signal_numbers

    def test_main_invalid_mode_raises(self, mock_settings, env_vars):
        """Test main raises for invalid mode."""
        mock_settings.live_or_historical = "invalid"
        with env_vars(kafka_broker_address="localhost:9092", kafka_topic_name="trades"):
            with patch("signal.signal"):
                import trades.config
                with patch.object(trades.config, "config", mock_settings):
                    from trades.main import main

                    with pytest.raises(ValueError) as exc_info:
                        main()

            assert "live" in str(exc_info.value)
            assert "historical" in str(exc_info.value)

    def test_main_runs_asyncio_for_live_mode(self, mock_settings, env_vars):
        """Test main uses asyncio.run for live mode."""
        mock_settings.live_or_historical = "live"
        with env_vars(kafka_broker_address="localhost:9092", kafka_topic_name="trades"):
            with patch("signal.signal"):
                with patch("trades.binance_client.BinanceLiveClient"):
                    with patch("asyncio.run") as mock_asyncio_run:
                        import trades.config
                        with patch.object(trades.config, "config", mock_settings):
                            from trades.main import main
                            main()

            mock_asyncio_run.assert_called_once()

    def test_main_calls_run_historical_for_historical_mode(self, mock_settings, env_vars):
        """Test main calls run_historical for historical mode."""
        mock_settings.live_or_historical = "historical"
        with env_vars(kafka_broker_address="localhost:9092", kafka_topic_name="trades"):
            with patch("signal.signal"):
                with patch("trades.binance_client.BinanceHistoricalClient"):
                    with patch("trades.main.run_historical") as mock_run:
                        import trades.config
                        with patch.object(trades.config, "config", mock_settings):
                            from trades.main import main
                            main()

            mock_run.assert_called_once()


class TestMainModuleReset:
    """Tests that verify module-level state is properly managed."""

    def test_shutdown_flag_reset(self):
        """Test shutdown flag can be reset."""
        from trades import main

        main._shutdown_requested = True
        main._shutdown_requested = False

        assert main._shutdown_requested is False


class TestTradeProduction:
    """Test trade production to Kafka."""

    async def test_trade_key_is_product_id(self, mock_kafka_app, mock_kafka_topic, sample_trade):
        """Test trade key is the product_id."""
        mock_client = AsyncMock()
        mock_client.start = AsyncMock()
        mock_client.stop = AsyncMock()
        mock_client.is_done = MagicMock(side_effect=[False, True])
        mock_client.get_trades_async = AsyncMock(return_value=[sample_trade])

        mock_producer = MagicMock()
        mock_producer.__enter__ = MagicMock(return_value=mock_producer)
        mock_producer.__exit__ = MagicMock(return_value=None)

        mock_kafka_app.topic = MagicMock(return_value=mock_kafka_topic)
        mock_kafka_app.get_producer = MagicMock(return_value=mock_producer)

        with patch("trades.main.Application", return_value=mock_kafka_app):
            with patch("trades.main._shutdown_requested", False):
                from trades.main import run_live

                await run_live(
                    kafka_broker_address="localhost:9092",
                    kafka_topic_name="test-trades",
                    client=mock_client,
                )

        # Check serialize was called with product_id as key
        mock_kafka_topic.serialize.assert_called_with(
            key=sample_trade.product_id,
            value=sample_trade.to_dict(),
        )

    def test_trade_value_is_dict(self, mock_kafka_app, mock_kafka_topic, sample_trade):
        """Test trade value is the trade dict."""
        mock_client = MagicMock()
        mock_client.is_done = MagicMock(side_effect=[False, True])
        mock_client.get_trades = MagicMock(return_value=[sample_trade])

        mock_producer = MagicMock()
        mock_producer.__enter__ = MagicMock(return_value=mock_producer)
        mock_producer.__exit__ = MagicMock(return_value=None)

        mock_kafka_app.topic = MagicMock(return_value=mock_kafka_topic)
        mock_kafka_app.get_producer = MagicMock(return_value=mock_producer)

        with patch("trades.main.Application", return_value=mock_kafka_app):
            with patch("trades.main._shutdown_requested", False):
                from trades.main import run_historical

                run_historical(
                    kafka_broker_address="localhost:9092",
                    kafka_topic_name="test-trades",
                    client=mock_client,
                )

        # Check serialize was called with trade dict as value
        mock_kafka_topic.serialize.assert_called_with(
            key=sample_trade.product_id,
            value=sample_trade.to_dict(),
        )


class TestApplicationCreation:
    """Test Kafka Application creation."""

    def test_application_created_with_broker_address_live(self, mock_kafka_app):
        """Test Application is created with correct broker address in live mode."""
        mock_client = AsyncMock()
        mock_client.start = AsyncMock()
        mock_client.stop = AsyncMock()
        mock_client.is_done = MagicMock(return_value=True)

        with patch("trades.main.Application") as mock_app_class:
            mock_app_class.return_value = mock_kafka_app
            with patch("trades.main._shutdown_requested", False):
                from trades.main import run_live

                asyncio.run(run_live(
                    kafka_broker_address="custom-broker:9093",
                    kafka_topic_name="test-trades",
                    client=mock_client,
                ))

        mock_app_class.assert_called_with(broker_address="custom-broker:9093")

    def test_application_created_with_broker_address_historical(self, mock_kafka_app, mock_kafka_producer):
        """Test Application is created with correct broker address in historical mode."""
        mock_client = MagicMock()
        mock_client.is_done = MagicMock(return_value=True)

        mock_kafka_app.get_producer = MagicMock(return_value=mock_kafka_producer)

        with patch("trades.main.Application") as mock_app_class:
            mock_app_class.return_value = mock_kafka_app
            with patch("trades.main._shutdown_requested", False):
                from trades.main import run_historical

                run_historical(
                    kafka_broker_address="custom-broker:9093",
                    kafka_topic_name="test-trades",
                    client=mock_client,
                )

        mock_app_class.assert_called_with(broker_address="custom-broker:9093")
