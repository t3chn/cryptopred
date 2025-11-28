# LunarCrush Service

Async client for LunarCrush API v4 to fetch sentiment and social metrics for cryptocurrencies.

## Features

- Async HTTP client with rate limiting and retry logic
- Pydantic models for API responses
- Kafka integration for streaming metrics
- Historical backfill support

## Usage

```python
from lunarcrush import LunarCrushClient

async with LunarCrushClient(api_key="your_key") as client:
    data = await client.get_coin_time_series("BTC", bucket="hour")
    for ts in data:
        print(f"Time: {ts.time}, Sentiment: {ts.sentiment}, Galaxy Score: {ts.galaxy_score}")
```

## Configuration

Set environment variables:

```bash
LUNARCRUSH_API_KEY=your_api_key
KAFKA_BROKER_ADDRESS=localhost:9092
KAFKA_TOPIC_NAME=lunarcrush_metrics
```

## Endpoints Used

- `/public/coins/:coin/time-series/v2` - Historical coin metrics
- `/public/topic/:topic/time-series/v2` - Historical topic metrics
- `/public/coins/list/v2` - List of coins with current metrics
