"""Tests for trades.binance_client module."""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from trades.trade import Trade


# ============================================================================
# BinanceHistoricalClient Tests
# ============================================================================


class TestBinanceHistoricalClientInit:
    """Test BinanceHistoricalClient initialization."""

    def test_init_with_default_config(self, mock_settings):
        """Test initialization with default configuration."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceHistoricalClient

            client = BinanceHistoricalClient(mock_settings)
            assert client.config == mock_settings
            assert len(client.product_ids) == 2

    def test_init_product_ids_uppercase(self, mock_settings):
        """Test product_ids are converted to uppercase."""
        mock_settings.product_ids = ["btcusdt", "ethusdt"]
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceHistoricalClient

            client = BinanceHistoricalClient(mock_settings)
            assert client.product_ids == ["BTCUSDT", "ETHUSDT"]

    def test_init_time_range_calculation(self, mock_settings):
        """Test time range is calculated correctly."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceHistoricalClient

            client = BinanceHistoricalClient(mock_settings)
            assert client.end_time_ms > 0
            # Start time should be approximately last_n_days ago
            expected_start = int(
                (time.time() - mock_settings.last_n_days * 24 * 60 * 60) * 1000
            )
            for symbol, start in client._symbol_state.items():
                assert abs(start - expected_start) < 1000  # Within 1 second

    def test_init_symbol_state_initialized(self, mock_settings):
        """Test symbol state is initialized for all symbols."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceHistoricalClient

            client = BinanceHistoricalClient(mock_settings)
            assert len(client._symbol_state) == len(mock_settings.product_ids)
            for pid in mock_settings.product_ids:
                assert pid.upper() in client._symbol_state

    def test_init_is_done_false(self, mock_settings):
        """Test _is_done starts as False."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceHistoricalClient

            client = BinanceHistoricalClient(mock_settings)
            assert client._is_done is False

    def test_init_current_idx_zero(self, mock_settings):
        """Test _current_idx starts at 0."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceHistoricalClient

            client = BinanceHistoricalClient(mock_settings)
            assert client._current_idx == 0

    def test_init_consecutive_failures_zero(self, mock_settings):
        """Test _consecutive_failures starts at 0."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceHistoricalClient

            client = BinanceHistoricalClient(mock_settings)
            assert client._consecutive_failures == 0

    def test_init_with_api_credentials(self, mock_settings_with_credentials):
        """Test initialization with API credentials."""
        with patch(
            "trades.binance_client.DerivativesTradingUsdsFutures"
        ) as mock_client:
            from trades.binance_client import BinanceHistoricalClient

            _client = BinanceHistoricalClient(mock_settings_with_credentials)
            assert _client is not None
            assert mock_client.called

    def test_init_single_symbol(self, mock_settings_single_symbol):
        """Test initialization with single symbol."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceHistoricalClient

            client = BinanceHistoricalClient(mock_settings_single_symbol)
            assert len(client.product_ids) == 1
            assert client.product_ids[0] == "BTCUSDT"

    def test_init_many_symbols(self, mock_settings_many_symbols):
        """Test initialization with many symbols."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceHistoricalClient

            client = BinanceHistoricalClient(mock_settings_many_symbols)
            assert len(client.product_ids) == 10

    def test_init_last_n_days_affects_start_time(self, mock_settings):
        """Test last_n_days affects start time."""
        mock_settings.last_n_days = 7
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceHistoricalClient

            client = BinanceHistoricalClient(mock_settings)
            expected_start = int((time.time() - 7 * 24 * 60 * 60) * 1000)
            for start in client._symbol_state.values():
                assert abs(start - expected_start) < 1000


class TestBinanceHistoricalClientGetNextSymbol:
    """Test BinanceHistoricalClient._get_next_symbol method."""

    def test_get_next_symbol_round_robin(self, mock_settings):
        """Test round-robin symbol selection."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceHistoricalClient

            client = BinanceHistoricalClient(mock_settings)

            first = client._get_next_symbol()
            second = client._get_next_symbol()

            assert first == "BTCUSDT"
            assert second == "ETHUSDT"

    def test_get_next_symbol_wraps_around(self, mock_settings):
        """Test symbol selection wraps around."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceHistoricalClient

            client = BinanceHistoricalClient(mock_settings)

            # Get all symbols
            client._get_next_symbol()  # BTCUSDT
            client._get_next_symbol()  # ETHUSDT
            third = client._get_next_symbol()  # Should wrap to BTCUSDT

            assert third == "BTCUSDT"

    def test_get_next_symbol_skips_completed(self, mock_settings):
        """Test skipping completed symbols."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceHistoricalClient

            client = BinanceHistoricalClient(mock_settings)
            # Mark BTCUSDT as completed
            client._symbol_state["BTCUSDT"] = client.end_time_ms + 1000

            result = client._get_next_symbol()
            assert result == "ETHUSDT"

    def test_get_next_symbol_all_completed_returns_none(self, mock_settings):
        """Test returns None when all symbols completed."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceHistoricalClient

            client = BinanceHistoricalClient(mock_settings)
            # Mark all symbols as completed
            for symbol in client.product_ids:
                client._symbol_state[symbol] = client.end_time_ms + 1000

            result = client._get_next_symbol()
            assert result is None

    def test_get_next_symbol_single_symbol(self, mock_settings_single_symbol):
        """Test with single symbol."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceHistoricalClient

            client = BinanceHistoricalClient(mock_settings_single_symbol)

            first = client._get_next_symbol()
            second = client._get_next_symbol()

            assert first == "BTCUSDT"
            assert second == "BTCUSDT"

    def test_get_next_symbol_index_updates(self, mock_settings):
        """Test _current_idx updates correctly."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceHistoricalClient

            client = BinanceHistoricalClient(mock_settings)
            assert client._current_idx == 0

            client._get_next_symbol()
            assert client._current_idx == 1

            client._get_next_symbol()
            assert client._current_idx == 0  # Wrapped


class TestBinanceHistoricalClientGetTrades:
    """Test BinanceHistoricalClient.get_trades method."""

    def test_get_trades_returns_empty_when_done(self, mock_settings):
        """Test returns empty list when is_done."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceHistoricalClient

            client = BinanceHistoricalClient(mock_settings)
            client._is_done = True

            result = client.get_trades()
            assert result == []

    def test_get_trades_successful_fetch(self, mock_settings, mock_sdk_rest_api):
        """Test successful trade fetch."""
        with patch(
            "trades.binance_client.DerivativesTradingUsdsFutures"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.rest_api = mock_sdk_rest_api
            mock_client_class.return_value = mock_client

            from trades.binance_client import BinanceHistoricalClient

            client = BinanceHistoricalClient(mock_settings)
            client.client = mock_client

            result = client.get_trades()

            assert len(result) == 2
            assert all(isinstance(t, Trade) for t in result)

    def test_get_trades_empty_response(self, mock_settings):
        """Test handling empty response."""
        with patch(
            "trades.binance_client.DerivativesTradingUsdsFutures"
        ) as mock_client_class:
            mock_client = MagicMock()
            response = MagicMock()
            response.rate_limits = {}
            response.data = MagicMock(return_value=[])
            mock_client.rest_api.compressed_aggregate_trades_list.return_value = (
                response
            )
            mock_client_class.return_value = mock_client

            from trades.binance_client import BinanceHistoricalClient

            client = BinanceHistoricalClient(mock_settings)
            client.client = mock_client
            old_state = client._symbol_state["BTCUSDT"]

            result = client.get_trades()

            assert result == []
            # State should be updated
            assert client._symbol_state["BTCUSDT"] > old_state

    def test_get_trades_rate_limit_error(self, mock_settings):
        """Test handling TooManyRequestsError."""
        with patch(
            "trades.binance_client.DerivativesTradingUsdsFutures"
        ) as mock_client_class:
            from trades.binance_client import TooManyRequestsError

            mock_client = MagicMock()
            mock_client.rest_api.compressed_aggregate_trades_list.side_effect = (
                TooManyRequestsError("Rate limit")
            )
            mock_client_class.return_value = mock_client

            from trades.binance_client import BinanceHistoricalClient

            client = BinanceHistoricalClient(mock_settings)
            client.client = mock_client

            with patch("time.sleep"):  # Don't actually sleep
                result = client.get_trades()

            assert result == []
            assert client._consecutive_failures == 1

    def test_get_trades_ip_ban_error(self, mock_settings):
        """Test handling RateLimitBanError."""
        with patch(
            "trades.binance_client.DerivativesTradingUsdsFutures"
        ) as mock_client_class:
            from trades.binance_client import RateLimitBanError

            mock_client = MagicMock()
            mock_client.rest_api.compressed_aggregate_trades_list.side_effect = (
                RateLimitBanError("IP banned")
            )
            mock_client_class.return_value = mock_client

            from trades.binance_client import BinanceHistoricalClient

            client = BinanceHistoricalClient(mock_settings)
            client.client = mock_client

            with patch("time.sleep"):  # Don't actually sleep
                result = client.get_trades()

            assert result == []

    def test_get_trades_generic_exception(self, mock_settings):
        """Test handling generic exceptions."""
        with patch(
            "trades.binance_client.DerivativesTradingUsdsFutures"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.rest_api.compressed_aggregate_trades_list.side_effect = (
                Exception("Unknown error")
            )
            mock_client_class.return_value = mock_client

            from trades.binance_client import BinanceHistoricalClient

            client = BinanceHistoricalClient(mock_settings)
            client.client = mock_client

            with patch("time.sleep"):  # Don't actually sleep
                result = client.get_trades()

            assert result == []
            assert client._consecutive_failures == 1

    def test_get_trades_exponential_backoff(self, mock_settings):
        """Test exponential backoff on failures."""
        with patch(
            "trades.binance_client.DerivativesTradingUsdsFutures"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.rest_api.compressed_aggregate_trades_list.side_effect = (
                Exception("Error")
            )
            mock_client_class.return_value = mock_client

            from trades.binance_client import BinanceHistoricalClient

            client = BinanceHistoricalClient(mock_settings)
            client.client = mock_client
            client._consecutive_failures = 3

            with patch("time.sleep") as mock_sleep:
                client.get_trades()
                # Delay should be min(2^3, 60) = 8
                mock_sleep.assert_called_with(8)

    def test_get_trades_backoff_capped_at_60(self, mock_settings):
        """Test backoff is capped at 60 seconds."""
        with patch(
            "trades.binance_client.DerivativesTradingUsdsFutures"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.rest_api.compressed_aggregate_trades_list.side_effect = (
                Exception("Error")
            )
            mock_client_class.return_value = mock_client

            from trades.binance_client import BinanceHistoricalClient

            client = BinanceHistoricalClient(mock_settings)
            client.client = mock_client
            client._consecutive_failures = 10  # 2^10 = 1024 > 60

            with patch("time.sleep") as mock_sleep:
                client.get_trades()
                mock_sleep.assert_called_with(60)

    def test_get_trades_resets_consecutive_failures(
        self, mock_settings, mock_sdk_rest_api
    ):
        """Test successful fetch resets consecutive failures."""
        with patch(
            "trades.binance_client.DerivativesTradingUsdsFutures"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.rest_api = mock_sdk_rest_api
            mock_client_class.return_value = mock_client

            from trades.binance_client import BinanceHistoricalClient

            client = BinanceHistoricalClient(mock_settings)
            client.client = mock_client
            client._consecutive_failures = 5

            client.get_trades()

            assert client._consecutive_failures == 0

    def test_get_trades_updates_cursor(self, mock_settings, mock_sdk_rest_api):
        """Test cursor is updated from last trade."""
        with patch(
            "trades.binance_client.DerivativesTradingUsdsFutures"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.rest_api = mock_sdk_rest_api
            mock_client_class.return_value = mock_client

            from trades.binance_client import BinanceHistoricalClient

            client = BinanceHistoricalClient(mock_settings)
            client.client = mock_client

            client.get_trades()

            # Cursor should be updated to last trade time + 1
            assert client._symbol_state["BTCUSDT"] == 1732636801001

    def test_get_trades_sets_done_when_all_complete(self, mock_settings):
        """Test is_done is set when all symbols complete."""
        with patch(
            "trades.binance_client.DerivativesTradingUsdsFutures"
        ) as mock_client_class:
            mock_client_class.return_value = MagicMock()

            from trades.binance_client import BinanceHistoricalClient

            client = BinanceHistoricalClient(mock_settings)
            # Mark all symbols as completed
            for symbol in client.product_ids:
                client._symbol_state[symbol] = client.end_time_ms + 1000

            client.get_trades()

            assert client._is_done is True


class TestBinanceHistoricalClientIsDone:
    """Test BinanceHistoricalClient.is_done method."""

    def test_is_done_initially_false(self, mock_settings):
        """Test is_done returns False initially."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceHistoricalClient

            client = BinanceHistoricalClient(mock_settings)
            assert client.is_done() is False

    def test_is_done_returns_true_when_done(self, mock_settings):
        """Test is_done returns True when _is_done is True."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceHistoricalClient

            client = BinanceHistoricalClient(mock_settings)
            client._is_done = True
            assert client.is_done() is True


# ============================================================================
# BinanceLiveClient Tests
# ============================================================================


class TestBinanceLiveClientInit:
    """Test BinanceLiveClient initialization."""

    def test_init_with_default_config(self, mock_settings):
        """Test initialization with default configuration."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceLiveClient

            client = BinanceLiveClient(mock_settings)
            assert client.config == mock_settings

    def test_init_product_ids_lowercase(self, mock_settings):
        """Test product_ids are converted to lowercase."""
        mock_settings.product_ids = ["BTCUSDT", "ETHUSDT"]
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceLiveClient

            client = BinanceLiveClient(mock_settings)
            assert client.product_ids == ["btcusdt", "ethusdt"]

    def test_init_trade_queue_created(self, mock_settings):
        """Test trade queue is created."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceLiveClient

            client = BinanceLiveClient(mock_settings)
            assert isinstance(client._trade_queue, asyncio.Queue)

    def test_init_is_running_false(self, mock_settings):
        """Test _is_running starts as False."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceLiveClient

            client = BinanceLiveClient(mock_settings)
            assert client._is_running is False

    def test_init_connection_none(self, mock_settings):
        """Test _connection starts as None."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceLiveClient

            client = BinanceLiveClient(mock_settings)
            assert client._connection is None

    def test_init_streams_empty(self, mock_settings):
        """Test _streams starts empty."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceLiveClient

            client = BinanceLiveClient(mock_settings)
            assert client._streams == []

    def test_init_single_symbol(self, mock_settings_single_symbol):
        """Test initialization with single symbol."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceLiveClient

            client = BinanceLiveClient(mock_settings_single_symbol)
            assert len(client.product_ids) == 1

    def test_init_many_symbols(self, mock_settings_many_symbols):
        """Test initialization with many symbols."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceLiveClient

            client = BinanceLiveClient(mock_settings_many_symbols)
            assert len(client.product_ids) == 10


class TestBinanceLiveClientStart:
    """Test BinanceLiveClient.start method."""

    async def test_start_creates_connection(
        self, mock_settings, mock_websocket_connection
    ):
        """Test start creates WebSocket connection."""
        with patch(
            "trades.binance_client.DerivativesTradingUsdsFutures"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.websocket_streams.create_connection = AsyncMock(
                return_value=mock_websocket_connection
            )
            mock_client_class.return_value = mock_client

            from trades.binance_client import BinanceLiveClient

            client = BinanceLiveClient(mock_settings)
            client.client = mock_client

            await client.start()

            mock_client.websocket_streams.create_connection.assert_called_once()

    async def test_start_sets_is_running(
        self, mock_settings, mock_websocket_connection
    ):
        """Test start sets _is_running to True."""
        with patch(
            "trades.binance_client.DerivativesTradingUsdsFutures"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.websocket_streams.create_connection = AsyncMock(
                return_value=mock_websocket_connection
            )
            mock_client_class.return_value = mock_client

            from trades.binance_client import BinanceLiveClient

            client = BinanceLiveClient(mock_settings)
            client.client = mock_client

            await client.start()

            assert client._is_running is True

    async def test_start_subscribes_to_streams(
        self, mock_settings, mock_websocket_connection
    ):
        """Test start subscribes to aggregate trade streams."""
        with patch(
            "trades.binance_client.DerivativesTradingUsdsFutures"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.websocket_streams.create_connection = AsyncMock(
                return_value=mock_websocket_connection
            )
            mock_client_class.return_value = mock_client

            from trades.binance_client import BinanceLiveClient

            client = BinanceLiveClient(mock_settings)
            client.client = mock_client

            await client.start()

            # Should subscribe for each symbol
            assert mock_websocket_connection.aggregate_trade_streams.call_count == 2

    async def test_start_registers_handlers(
        self, mock_settings, mock_websocket_connection
    ):
        """Test start registers message handlers."""
        stream = AsyncMock()
        stream.on = MagicMock()
        mock_websocket_connection.aggregate_trade_streams = AsyncMock(
            return_value=stream
        )

        with patch(
            "trades.binance_client.DerivativesTradingUsdsFutures"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.websocket_streams.create_connection = AsyncMock(
                return_value=mock_websocket_connection
            )
            mock_client_class.return_value = mock_client

            from trades.binance_client import BinanceLiveClient

            client = BinanceLiveClient(mock_settings)
            client.client = mock_client

            await client.start()

            # Handler should be registered for each stream
            assert stream.on.call_count == 2

    async def test_start_stores_streams(self, mock_settings, mock_websocket_connection):
        """Test start stores streams in _streams list."""
        with patch(
            "trades.binance_client.DerivativesTradingUsdsFutures"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.websocket_streams.create_connection = AsyncMock(
                return_value=mock_websocket_connection
            )
            mock_client_class.return_value = mock_client

            from trades.binance_client import BinanceLiveClient

            client = BinanceLiveClient(mock_settings)
            client.client = mock_client

            await client.start()

            assert len(client._streams) == 2


class TestBinanceLiveClientHandleTrade:
    """Test BinanceLiveClient._handle_trade method."""

    def test_handle_trade_normal(self, mock_settings, mock_websocket_response):
        """Test normal trade handling."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceLiveClient

            client = BinanceLiveClient(mock_settings)

            client._handle_trade(mock_websocket_response, "btcusdt")

            assert client._trade_queue.qsize() == 1

    def test_handle_trade_queue_full(self, mock_settings, mock_websocket_response):
        """Test handling when queue is full."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceLiveClient

            client = BinanceLiveClient(mock_settings)
            # Create queue with max size 0 to force full
            client._trade_queue = asyncio.Queue(maxsize=1)
            client._trade_queue.put_nowait(
                Trade(
                    product_id="TEST",
                    price=1.0,
                    quantity=1.0,
                    timestamp="2024-01-01T00:00:00Z",
                    timestamp_ms=0,
                )
            )

            # Should not raise, just log warning
            client._handle_trade(mock_websocket_response, "btcusdt")

    def test_handle_trade_exception(self, mock_settings):
        """Test handling trade processing exception."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceLiveClient

            client = BinanceLiveClient(mock_settings)

            # Pass invalid data that will cause exception
            invalid_data = MagicMock()
            invalid_data.s = None
            invalid_data.p = (
                "invalid"  # Will cause float conversion error if not handled
            )
            invalid_data.q = None
            invalid_data.T = None

            # Should not raise
            client._handle_trade(invalid_data, "btcusdt")

    def test_handle_trade_creates_correct_trade(
        self, mock_settings, mock_websocket_response
    ):
        """Test created trade has correct values."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceLiveClient

            client = BinanceLiveClient(mock_settings)

            client._handle_trade(mock_websocket_response, "btcusdt")

            trade = client._trade_queue.get_nowait()
            assert trade.product_id == "BTCUSDT"
            assert trade.price == 97500.50


class TestBinanceLiveClientGetTradesAsync:
    """Test BinanceLiveClient.get_trades_async method."""

    async def test_get_trades_async_drains_queue(self, mock_settings):
        """Test drains all available trades from queue."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceLiveClient

            client = BinanceLiveClient(mock_settings)
            # Add some trades to queue
            for i in range(5):
                client._trade_queue.put_nowait(
                    Trade(
                        product_id=f"TEST{i}",
                        price=float(i),
                        quantity=1.0,
                        timestamp="2024-01-01T00:00:00Z",
                        timestamp_ms=0,
                    )
                )

            result = await client.get_trades_async()

            assert len(result) == 5
            assert client._trade_queue.empty()

    async def test_get_trades_async_waits_for_trade(self, mock_settings):
        """Test waits for trade when queue empty."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceLiveClient

            client = BinanceLiveClient(mock_settings)

            # Add trade after a delay
            async def add_trade():
                await asyncio.sleep(0.1)
                client._trade_queue.put_nowait(
                    Trade(
                        product_id="TEST",
                        price=1.0,
                        quantity=1.0,
                        timestamp="2024-01-01T00:00:00Z",
                        timestamp_ms=0,
                    )
                )

            asyncio.create_task(add_trade())
            result = await client.get_trades_async()

            assert len(result) == 1

    async def test_get_trades_async_timeout_returns_empty(self, mock_settings):
        """Test returns empty list on timeout."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceLiveClient

            client = BinanceLiveClient(mock_settings)

            # Don't add any trades, should timeout and return empty
            result = await client.get_trades_async()

            assert result == []

    async def test_get_trades_async_multiple_trades(self, mock_settings):
        """Test returns multiple trades."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceLiveClient

            client = BinanceLiveClient(mock_settings)

            # Add multiple trades
            client._trade_queue.put_nowait(
                Trade(
                    product_id="BTCUSDT",
                    price=97500.0,
                    quantity=1.0,
                    timestamp="2024-01-01T00:00:00Z",
                    timestamp_ms=0,
                )
            )
            client._trade_queue.put_nowait(
                Trade(
                    product_id="ETHUSDT",
                    price=3500.0,
                    quantity=1.0,
                    timestamp="2024-01-01T00:00:00Z",
                    timestamp_ms=0,
                )
            )

            result = await client.get_trades_async()

            assert len(result) == 2


class TestBinanceLiveClientStop:
    """Test BinanceLiveClient.stop method."""

    async def test_stop_sets_is_running_false(self, mock_settings):
        """Test stop sets _is_running to False."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceLiveClient

            client = BinanceLiveClient(mock_settings)
            client._is_running = True

            await client.stop()

            assert client._is_running is False

    async def test_stop_unsubscribes_streams(self, mock_settings):
        """Test stop unsubscribes from all streams."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceLiveClient

            client = BinanceLiveClient(mock_settings)
            mock_stream1 = AsyncMock()
            mock_stream2 = AsyncMock()
            client._streams = [mock_stream1, mock_stream2]

            await client.stop()

            mock_stream1.unsubscribe.assert_called_once()
            mock_stream2.unsubscribe.assert_called_once()

    async def test_stop_closes_connection(self, mock_settings):
        """Test stop closes connection."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceLiveClient

            client = BinanceLiveClient(mock_settings)
            mock_connection = AsyncMock()
            client._connection = mock_connection

            await client.stop()

            mock_connection.close_connection.assert_called_once_with(close_session=True)

    async def test_stop_handles_unsubscribe_error(self, mock_settings):
        """Test stop handles unsubscribe errors gracefully."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceLiveClient

            client = BinanceLiveClient(mock_settings)
            mock_stream = AsyncMock()
            mock_stream.unsubscribe.side_effect = Exception("Unsubscribe error")
            client._streams = [mock_stream]

            # Should not raise
            await client.stop()

    async def test_stop_handles_close_error(self, mock_settings):
        """Test stop handles connection close errors gracefully."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceLiveClient

            client = BinanceLiveClient(mock_settings)
            mock_connection = AsyncMock()
            mock_connection.close_connection.side_effect = Exception("Close error")
            client._connection = mock_connection

            # Should not raise
            await client.stop()

    async def test_stop_without_connection(self, mock_settings):
        """Test stop works when connection is None."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceLiveClient

            client = BinanceLiveClient(mock_settings)
            client._connection = None

            # Should not raise
            await client.stop()

    async def test_stop_with_empty_streams(self, mock_settings):
        """Test stop works with empty streams list."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceLiveClient

            client = BinanceLiveClient(mock_settings)
            client._streams = []

            # Should not raise
            await client.stop()


class TestBinanceLiveClientIsDone:
    """Test BinanceLiveClient.is_done method."""

    def test_is_done_returns_false_when_running(self, mock_settings):
        """Test is_done returns False when running."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceLiveClient

            client = BinanceLiveClient(mock_settings)
            client._is_running = True

            assert client.is_done() is False

    def test_is_done_returns_true_when_not_running(self, mock_settings):
        """Test is_done returns True when not running."""
        with patch("trades.binance_client.DerivativesTradingUsdsFutures"):
            from trades.binance_client import BinanceLiveClient

            client = BinanceLiveClient(mock_settings)
            client._is_running = False

            assert client.is_done() is True


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.integration
class TestBinanceHistoricalClientIntegration:
    """Integration tests for BinanceHistoricalClient with real Binance API."""

    def test_fetch_btcusdt_trades(self, real_historical_client):
        """Test fetching real BTCUSDT trades."""
        trades = real_historical_client.get_trades()

        assert isinstance(trades, list)
        if trades:  # May be empty if no trades in time range
            assert all(isinstance(t, Trade) for t in trades)
            assert all(t.product_id == "BTCUSDT" for t in trades)
            assert all(t.price > 0 for t in trades)
            assert all(t.quantity > 0 for t in trades)

    def test_fetch_trades_response_structure(self, real_historical_client):
        """Test response structure from real API."""
        trades = real_historical_client.get_trades()

        if trades:
            trade = trades[0]
            assert hasattr(trade, "product_id")
            assert hasattr(trade, "price")
            assert hasattr(trade, "quantity")
            assert hasattr(trade, "timestamp")
            assert hasattr(trade, "timestamp_ms")

    def test_multiple_fetches(self, real_historical_client):
        """Test multiple consecutive fetches."""
        trades1 = real_historical_client.get_trades()
        trades2 = real_historical_client.get_trades()

        # Both should return lists (may be empty)
        assert isinstance(trades1, list)
        assert isinstance(trades2, list)


@pytest.mark.integration
class TestBinanceLiveClientIntegration:
    """Integration tests for BinanceLiveClient with real Binance WebSocket."""

    async def test_connect_and_receive_trades(self, real_live_client):
        """Test connecting and receiving live trades."""
        await real_live_client.start()

        # Wait for some trades
        await asyncio.sleep(3)

        trades = await real_live_client.get_trades_async()

        # Should have received some trades
        assert isinstance(trades, list)

        await real_live_client.stop()

    async def test_graceful_shutdown(self, real_live_client):
        """Test graceful shutdown."""
        await real_live_client.start()
        assert real_live_client._is_running is True

        await real_live_client.stop()
        assert real_live_client._is_running is False
