"""Configuration for technical indicators service."""

from pathlib import Path
from typing import Any

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Service configuration from environment variables."""

    model_config = SettingsConfigDict(
        env_file="services/technical_indicators/settings.env",
        env_file_encoding="utf-8",
    )

    kafka_broker_address: str
    kafka_input_topic: str = "candles"
    kafka_output_topic: str = "technical_indicators"
    kafka_consumer_group: str = "technical-indicators-group"
    candle_seconds: int = 60


def load_indicators_config(
    config_path: str | Path = "indicators.yaml",
) -> dict[str, Any]:
    """Load indicators configuration from YAML file.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        Dictionary with indicators configuration.
    """
    # Try relative to service directory first
    service_dir = Path(__file__).parent.parent.parent
    full_path = service_dir / config_path

    if not full_path.exists():
        # Try as absolute or cwd-relative path
        full_path = Path(config_path)

    with open(full_path) as f:
        return yaml.safe_load(f)


config = Settings()
