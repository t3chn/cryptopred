-- Candles table: OHLCV candle data
-- Source: candles Kafka topic

CREATE TABLE IF NOT EXISTS candles (
    pair VARCHAR,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    window_start_ms BIGINT,
    window_end_ms BIGINT,
    candle_seconds INT,
    PRIMARY KEY (pair, window_start_ms, candle_seconds)
) WITH (
    connector = 'kafka',
    topic = 'candles',
    properties.bootstrap.server = 'kafka-kafka-bootstrap.kafka.svc.cluster.local:9092',
    scan.startup.mode = 'latest'
) FORMAT PLAIN ENCODE JSON;
