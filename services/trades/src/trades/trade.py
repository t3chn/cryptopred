import datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

if TYPE_CHECKING:
    from binance_sdk_derivatives_trading_usds_futures.rest_api.models import (
        CompressedAggregateTradesListResponseInner,
    )
    from binance_sdk_derivatives_trading_usds_futures.websocket_streams.models import (
        AggregateTradeStreamsResponse,
    )


class Trade(BaseModel):
    product_id: str
    price: float
    quantity: float
    timestamp: str
    timestamp_ms: int

    def to_dict(self) -> dict:
        return self.model_dump()

    @staticmethod
    def unix_seconds_to_iso_format(timestamp_sec: float) -> str:
        """
        Convert Unix timestamp in seconds to ISO 8601 format string with UTC timezone
        Example: "2025-04-24T11:35:42.856851Z"
        """
        dt = datetime.datetime.fromtimestamp(timestamp_sec, tz=datetime.UTC)
        return dt.isoformat().replace("+00:00", "Z")

    @staticmethod
    def iso_format_to_unix_seconds(iso_format: str) -> float:
        """
        Convert ISO 8601 format string with UTC timezone to Unix timestamp in seconds
        Example: "2025-04-24T11:35:42.856851Z" -> 1714084542.856851
        """
        return datetime.datetime.fromisoformat(iso_format).timestamp()

    @classmethod
    def from_sdk_rest_api(
        cls,
        product_id: str,
        data: "CompressedAggregateTradesListResponseInner",
    ) -> "Trade":
        """
        Create a Trade from SDK REST API response.

        SDK model fields:
        - a: Aggregate trade ID
        - p: Price (string)
        - q: Quantity (string)
        - T: Trade time (milliseconds)
        - m: Is buyer the market maker
        """
        timestamp_ms = data.T or 0
        return cls(
            product_id=product_id,
            price=float(data.p) if data.p else 0.0,
            quantity=float(data.q) if data.q else 0.0,
            timestamp=cls.unix_seconds_to_iso_format(timestamp_ms / 1000),
            timestamp_ms=timestamp_ms,
        )

    @classmethod
    def from_sdk_websocket(
        cls,
        data: "AggregateTradeStreamsResponse | Any",
    ) -> "Trade":
        """
        Create a Trade from SDK WebSocket stream response.

        SDK model fields:
        - e: Event type ("aggTrade")
        - E: Event time
        - s: Symbol
        - a: Aggregate trade ID
        - p: Price (string)
        - q: Quantity (string)
        - T: Trade time (milliseconds)
        - m: Is buyer the market maker
        """
        timestamp_ms = data.T or 0
        return cls(
            product_id=data.s or "",
            price=float(data.p) if data.p else 0.0,
            quantity=float(data.q) if data.q else 0.0,
            timestamp=cls.unix_seconds_to_iso_format(timestamp_ms / 1000),
            timestamp_ms=timestamp_ms,
        )

    # Legacy methods for backwards compatibility
    @classmethod
    def from_binance_websocket_response(
        cls,
        product_id: str,
        price: float,
        quantity: float,
        timestamp_ms: int,
    ) -> "Trade":
        """Create a Trade object from the Binance Futures websocket response (legacy)."""
        return cls(
            product_id=product_id,
            price=price,
            quantity=quantity,
            timestamp=cls.unix_seconds_to_iso_format(timestamp_ms / 1000),
            timestamp_ms=timestamp_ms,
        )

    @classmethod
    def from_binance_rest_api_response(
        cls,
        product_id: str,
        price: float,
        quantity: float,
        timestamp_ms: int,
    ) -> "Trade":
        """Create a Trade object from the Binance Futures REST API response (legacy)."""
        return cls(
            product_id=product_id,
            price=price,
            quantity=quantity,
            timestamp=cls.unix_seconds_to_iso_format(timestamp_ms / 1000),
            timestamp_ms=timestamp_ms,
        )
