"""Configuration for news-sentiment service."""

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """News-sentiment service configuration."""

    # Kafka
    kafka_broker_address: str = "kafka-kafka-bootstrap.kafka.svc.cluster.local:9092"
    kafka_input_topic: str = "news"
    kafka_output_topic: str = "news_sentiment"
    kafka_consumer_group: str = "news_sentiment_consumer"

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"

    model_config = {"env_file": ".env", "extra": "ignore"}


def get_config() -> Config:
    """Load configuration from environment."""
    return Config()
