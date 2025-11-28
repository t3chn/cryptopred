from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="services/lunarcrush/settings.env", env_file_encoding="utf-8"
    )

    # LunarCrush API settings
    lunarcrush_api_key: str
    lunarcrush_base_url: str = "https://lunarcrush.com/api4"

    # Coins to track (symbols like BTC, ETH or numeric IDs)
    coins: list[str] = ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "AVAX", "LINK", "DOT"]

    # Kafka settings
    kafka_broker_address: str
    kafka_topic_name: str = "lunarcrush_metrics"

    # Data source mode
    live_or_historical: Literal["live", "historical"] = "historical"
    last_n_days: int = 60

    # Time series bucket (hour or day)
    bucket: Literal["hour", "day"] = "hour"

    # Rate limiting
    requests_per_minute: int = 30
    request_timeout: int = 30


config = Settings()
