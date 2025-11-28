-- LunarCrush Sentiment Metrics table
-- Source: lunarcrush_metrics Kafka topic
-- Contains social sentiment data for crypto assets

CREATE TABLE IF NOT EXISTS lunarcrush_metrics (
    -- Identification
    coin VARCHAR,
    time BIGINT,  -- Unix timestamp in seconds
    time_ms BIGINT,  -- Unix timestamp in milliseconds

    -- Sentiment metrics
    sentiment DOUBLE PRECISION,  -- % positive posts (0-100)
    galaxy_score DOUBLE PRECISION,  -- Combined technical + social score
    alt_rank INT,  -- Relative performance vs other assets

    -- Social metrics
    interactions BIGINT,  -- Total social engagement
    social_dominance DOUBLE PRECISION,  -- % of total social volume
    contributors_active INT,  -- Unique social accounts with posts
    posts_active INT,  -- Unique social posts with interactions
    spam INT,  -- Posts considered spam

    -- Price data (from LunarCrush)
    close DOUBLE PRECISION,
    market_cap DOUBLE PRECISION,
    volume_24h DOUBLE PRECISION,

    PRIMARY KEY (coin, time_ms)
) WITH (
    connector = 'kafka',
    topic = 'lunarcrush_metrics',
    properties.bootstrap.server = 'kafka-kafka-bootstrap.kafka.svc.cluster.local:9092',
    scan.startup.mode = 'earliest'
) FORMAT PLAIN ENCODE JSON;

-- Materialized view: Latest sentiment per coin (for quick lookups)
CREATE MATERIALIZED VIEW IF NOT EXISTS lunarcrush_latest AS
SELECT DISTINCT ON (coin)
    coin,
    time_ms,
    sentiment,
    galaxy_score,
    alt_rank,
    interactions,
    social_dominance
FROM lunarcrush_metrics
ORDER BY coin, time_ms DESC;
