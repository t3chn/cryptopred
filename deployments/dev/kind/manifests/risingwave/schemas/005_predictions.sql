-- Predictions table: ML model price predictions
-- Written by predictor service via psycopg2

CREATE TABLE IF NOT EXISTS predictions (
    -- Prediction identifier
    pair VARCHAR,
    ts_ms BIGINT,                  -- Timestamp when prediction was made (ms)
    model_name VARCHAR,            -- Model name (e.g., "BTCUSDT_60s_300s")

    -- Prediction details
    predicted_price DOUBLE PRECISION,
    model_version VARCHAR,
    predicted_ts_ms BIGINT,        -- Timestamp of predicted price (ms)

    PRIMARY KEY (pair, ts_ms, model_name)
);

-- Index for efficient queries by pair and time range
CREATE INDEX IF NOT EXISTS idx_predictions_pair_time
ON predictions (pair, predicted_ts_ms DESC);
