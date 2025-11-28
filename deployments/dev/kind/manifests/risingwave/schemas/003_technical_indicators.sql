-- Technical Indicators table: Candles enriched with technical indicators
-- Source: technical_indicators Kafka topic

CREATE TABLE IF NOT EXISTS technical_indicators (
    -- Base candle data
    pair VARCHAR,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    window_start_ms BIGINT,
    window_end_ms BIGINT,
    candle_seconds INT,

    -- Simple Moving Averages
    sma_7 DOUBLE PRECISION,
    sma_14 DOUBLE PRECISION,
    sma_21 DOUBLE PRECISION,
    sma_50 DOUBLE PRECISION,

    -- Exponential Moving Averages
    ema_7 DOUBLE PRECISION,
    ema_14 DOUBLE PRECISION,
    ema_21 DOUBLE PRECISION,
    ema_50 DOUBLE PRECISION,

    -- Relative Strength Index
    rsi_7 DOUBLE PRECISION,
    rsi_14 DOUBLE PRECISION,
    rsi_21 DOUBLE PRECISION,

    -- MACD (Moving Average Convergence Divergence)
    macd DOUBLE PRECISION,
    macd_signal DOUBLE PRECISION,
    macd_hist DOUBLE PRECISION,

    -- Bollinger Bands
    bb_lower DOUBLE PRECISION,
    bb_middle DOUBLE PRECISION,
    bb_upper DOUBLE PRECISION,

    -- Stochastic Oscillator
    stoch_k DOUBLE PRECISION,
    stoch_d DOUBLE PRECISION,

    -- Average True Range
    atr_14 DOUBLE PRECISION,

    -- On-Balance Volume
    obv DOUBLE PRECISION,

    PRIMARY KEY (pair, window_start_ms, candle_seconds)
) WITH (
    connector = 'kafka',
    topic = 'technical_indicators',
    properties.bootstrap.server = 'kafka-kafka-bootstrap.kafka.svc.cluster.local:9092',
    scan.startup.mode = 'latest'
) FORMAT PLAIN ENCODE JSON;
