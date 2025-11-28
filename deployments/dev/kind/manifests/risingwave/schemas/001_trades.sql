-- Trades table: Raw trade data from Binance
-- Source: trades Kafka topic

CREATE TABLE IF NOT EXISTS trades (
    pair VARCHAR,
    price DOUBLE PRECISION,
    quantity DOUBLE PRECISION,
    timestamp_ms BIGINT,
    is_buyer_maker BOOLEAN,
    PRIMARY KEY (pair, timestamp_ms)
) WITH (
    connector = 'kafka',
    topic = 'trades',
    properties.bootstrap.server = 'kafka-kafka-bootstrap.kafka.svc.cluster.local:9092',
    scan.startup.mode = 'latest'
) FORMAT PLAIN ENCODE JSON;
