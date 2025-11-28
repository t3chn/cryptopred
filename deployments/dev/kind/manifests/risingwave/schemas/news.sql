-- News and sentiment tables for RisingWave

-- Raw news from Cryptopanic API
CREATE TABLE IF NOT EXISTS news (
    id BIGINT,
    title VARCHAR,
    description VARCHAR,
    published_at VARCHAR,
    timestamp_ms BIGINT,
    PRIMARY KEY (id)
) WITH (
    connector = 'kafka',
    topic = 'news',
    properties.bootstrap.server = 'kafka-kafka-bootstrap.kafka.svc.cluster.local:9092',
    scan.startup.mode = 'earliest'
) FORMAT PLAIN ENCODE JSON;

-- Sentiment scores from OpenAI analysis
CREATE TABLE IF NOT EXISTS news_sentiment (
    coin VARCHAR,
    score INT,
    timestamp_ms BIGINT,
    PRIMARY KEY (coin, timestamp_ms)
) WITH (
    connector = 'kafka',
    topic = 'news_sentiment',
    properties.bootstrap.server = 'kafka-kafka-bootstrap.kafka.svc.cluster.local:9092',
    scan.startup.mode = 'earliest'
) FORMAT PLAIN ENCODE JSON;

-- Materialized view: Latest sentiment per coin
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_latest_sentiment AS
SELECT DISTINCT ON (coin)
    coin,
    score,
    timestamp_ms
FROM news_sentiment
ORDER BY coin, timestamp_ms DESC;

-- Materialized view: Aggregated sentiment over sliding window (last 24h)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_sentiment_24h AS
SELECT
    coin,
    AVG(score::FLOAT) as avg_sentiment,
    SUM(CASE WHEN score > 0 THEN 1 ELSE 0 END) as bullish_count,
    SUM(CASE WHEN score < 0 THEN 1 ELSE 0 END) as bearish_count,
    COUNT(*) as total_count
FROM news_sentiment
WHERE timestamp_ms > (EXTRACT(EPOCH FROM NOW()) * 1000 - 86400000)::BIGINT
GROUP BY coin;

-- Materialized view: Recent news count
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_news_stats AS
SELECT
    COUNT(*) as total_news,
    COUNT(DISTINCT DATE_TRUNC('day', TO_TIMESTAMP(timestamp_ms / 1000))) as days_collected
FROM news;
