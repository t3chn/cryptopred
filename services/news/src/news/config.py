"""Configuration for news service."""

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """News service configuration."""

    # Cryptopanic API
    cryptopanic_api_key: str

    # Kafka
    kafka_broker_address: str = "kafka-kafka-bootstrap.kafka.svc.cluster.local:9092"
    kafka_output_topic: str = "news"

    # Polling
    polling_interval_sec: int = 60

    model_config = {"env_file": ".env", "extra": "ignore"}


def get_config() -> Config:
    """Load configuration from environment."""
    return Config()
