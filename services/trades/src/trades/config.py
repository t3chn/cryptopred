from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="services/trades/settings.env", env_file_encoding="utf-8"
    )

    # Trading pairs to track
    product_ids: list[str] = [
        "BTCUSDT",
        "ETHUSDT",
        "SOLUSDT",
        "BNBUSDT",
        "XRPUSDT",
        "DOGEUSDT",
        "ADAUSDT",
        "AVAXUSDT",
        "LINKUSDT",
        "DOTUSDT",
    ]

    # Kafka settings
    kafka_broker_address: str
    kafka_topic_name: str

    # Data source mode
    live_or_historical: Literal["live", "historical"] = "live"
    last_n_days: int = 30

    # Binance API settings (optional, for authenticated endpoints)
    binance_api_key: str | None = None
    binance_api_secret: str | None = None

    # SDK configuration
    rest_api_timeout: int = 30000  # milliseconds
    rest_api_retries: int = 3
    websocket_reconnect_delay: int = 5000  # milliseconds


config = Settings()
