"""
Binance SDK client wrappers for historical and live trade data.

Uses binance-sdk-derivatives-trading-usds-futures for:
- REST API (historical data)
- WebSocket Streams (live data)
"""

import asyncio
import time
from typing import TYPE_CHECKING

from loguru import logger

from binance_sdk_derivatives_trading_usds_futures import (
    DerivativesTradingUsdsFutures,
    DERIVATIVES_TRADING_USDS_FUTURES_REST_API_PROD_URL,
    DERIVATIVES_TRADING_USDS_FUTURES_WS_STREAMS_PROD_URL,
    TooManyRequestsError,
    RateLimitBanError,
)
from binance_common.configuration import (
    ConfigurationRestAPI,
    ConfigurationWebSocketStreams,
)

from trades.trade import Trade

if TYPE_CHECKING:
    from trades.config import Settings


class BinanceHistoricalClient:
    """
    REST API client for fetching historical aggregate trades.

    Features:
    - Multi-symbol support with round-robin fetching
    - Rate limit handling via SDK
    - Time-based pagination (1-hour chunks)
    - Exponential backoff on errors
    """

    def __init__(self, config: "Settings"):
        self.config = config
        self.product_ids = [p.upper() for p in config.product_ids]
        self.last_n_days = config.last_n_days
        self._is_done = False

        # Calculate time range
        self.end_time_ms = int(time.time() * 1000)
        base_start = int((time.time() - self.last_n_days * 24 * 60 * 60) * 1000)

        # State for each symbol: {symbol: start_time_ms}
        self._symbol_state = {pid: base_start for pid in self.product_ids}
        self._current_idx = 0
        self._consecutive_failures = 0

        # Initialize SDK client
        rest_config = ConfigurationRestAPI(
            api_key=config.binance_api_key or "",
            api_secret=config.binance_api_secret or "",
            base_path=DERIVATIVES_TRADING_USDS_FUTURES_REST_API_PROD_URL,
            timeout=config.rest_api_timeout,
            retries=config.rest_api_retries,
        )
        self.client = DerivativesTradingUsdsFutures(config_rest_api=rest_config)

    def _get_next_symbol(self) -> str | None:
        """Get next symbol to fetch using round-robin, skip completed."""
        start_idx = self._current_idx
        while True:
            symbol = self.product_ids[self._current_idx]
            self._current_idx = (self._current_idx + 1) % len(self.product_ids)

            if self._symbol_state[symbol] < self.end_time_ms:
                return symbol

            # Checked all symbols
            if self._current_idx == start_idx:
                return None

    def get_trades(self) -> list[Trade]:
        """
        Fetch aggregate trades with rate limit handling.

        Returns:
            list[Trade]: List of trades (may be empty on error/no data)
        """
        if self._is_done:
            return []

        symbol = self._get_next_symbol()
        if symbol is None:
            self._is_done = True
            logger.info("Completed fetching historical data for all symbols")
            return []

        start_time = self._symbol_state[symbol]
        end_time = min(start_time + 3600000, self.end_time_ms)  # 1 hour chunk

        try:
            response = self.client.rest_api.compressed_aggregate_trades_list(
                symbol=symbol,
                start_time=start_time,
                end_time=end_time,
                limit=1000,
            )

            # Log rate limits
            rate_limits = response.rate_limits
            if rate_limits:
                logger.debug(f"Rate limits: {rate_limits}")

            data = response.data()
            self._consecutive_failures = 0

            if not data:
                # No data in this time range, move forward
                self._symbol_state[symbol] = end_time
                return []

            trades = [Trade.from_sdk_rest_api(symbol, item) for item in data]

            # Update cursor to continue from last trade
            if trades:
                last_trade_time = data[-1].T
                if last_trade_time:
                    self._symbol_state[symbol] = last_trade_time + 1

            return trades

        except TooManyRequestsError as e:
            logger.warning(f"Rate limit exceeded: {e}")
            time.sleep(60)
            self._consecutive_failures += 1
            return []

        except RateLimitBanError as e:
            logger.error(f"IP banned due to rate limits: {e}")
            time.sleep(120)  # Minimum ban is 2 minutes
            return []

        except Exception as e:
            logger.error(f"Error fetching trades for {symbol}: {e}")
            delay = min(2**self._consecutive_failures, 60)
            time.sleep(delay)
            self._consecutive_failures += 1
            return []

    def is_done(self) -> bool:
        return self._is_done


class BinanceLiveClient:
    """
    WebSocket Streams client for real-time aggregate trades.

    Features:
    - Async WebSocket with automatic reconnection (via SDK)
    - Multi-symbol support
    - Thread-safe trade queue
    - Graceful shutdown
    """

    def __init__(self, config: "Settings"):
        self.config = config
        self.product_ids = [p.lower() for p in config.product_ids]
        self._trade_queue: asyncio.Queue[Trade] = asyncio.Queue()
        self._is_running = False
        self._connection = None
        self._streams: list = []

        # Initialize SDK client
        ws_config = ConfigurationWebSocketStreams(
            stream_url=DERIVATIVES_TRADING_USDS_FUTURES_WS_STREAMS_PROD_URL,
            reconnect_delay=config.websocket_reconnect_delay,
        )
        self.client = DerivativesTradingUsdsFutures(config_ws_streams=ws_config)

    async def start(self):
        """Start WebSocket connection and subscribe to aggregate trade streams."""
        logger.info(
            f"Connecting to Binance Futures WebSocket for {len(self.product_ids)} symbols"
        )

        self._connection = await self.client.websocket_streams.create_connection()
        self._is_running = True

        for symbol in self.product_ids:
            stream = await self._connection.aggregate_trade_streams(symbol=symbol)
            stream.on("message", lambda data, s=symbol: self._handle_trade(data, s))
            self._streams.append(stream)
            logger.debug(f"Subscribed to {symbol}@aggTrade")

        logger.info(f"Connected to {len(self.product_ids)} aggregate trade streams")

    def _handle_trade(self, data, symbol: str):
        """Callback for incoming trade messages."""
        try:
            trade = Trade.from_sdk_websocket(data)
            self._trade_queue.put_nowait(trade)
        except asyncio.QueueFull:
            logger.warning("Trade queue full, dropping trade")
        except Exception as e:
            logger.error(f"Error processing trade: {e}")

    async def get_trades_async(self) -> list[Trade]:
        """
        Get available trades from the queue.

        Returns:
            list[Trade]: List of trades received since last call
        """
        trades = []

        # Drain all available trades
        while not self._trade_queue.empty():
            try:
                trade = self._trade_queue.get_nowait()
                trades.append(trade)
            except asyncio.QueueEmpty:
                break

        # If no trades available, wait briefly for at least one
        if not trades:
            try:
                trade = await asyncio.wait_for(self._trade_queue.get(), timeout=1.0)
                trades.append(trade)
            except asyncio.TimeoutError:
                pass

        return trades

    async def stop(self):
        """Stop WebSocket connection gracefully."""
        logger.info("Stopping WebSocket connection")
        self._is_running = False

        for stream in self._streams:
            try:
                await stream.unsubscribe()
            except Exception as e:
                logger.warning(f"Error unsubscribing from stream: {e}")

        if self._connection:
            try:
                await self._connection.close_connection(close_session=True)
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")

        logger.info("WebSocket connection closed")

    def is_done(self) -> bool:
        return not self._is_running
