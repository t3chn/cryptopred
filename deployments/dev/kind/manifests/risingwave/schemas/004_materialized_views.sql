-- Materialized Views for real-time analytics

-- Latest indicators per pair (most recent candle with all indicators)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_latest_indicators AS
SELECT
    pair,
    close,
    volume,
    window_start_ms,
    sma_7,
    sma_14,
    sma_21,
    ema_7,
    ema_14,
    ema_21,
    rsi_7,
    rsi_14,
    macd,
    macd_signal,
    macd_hist,
    bb_lower,
    bb_middle,
    bb_upper,
    stoch_k,
    stoch_d,
    atr_14,
    obv
FROM (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY pair ORDER BY window_start_ms DESC) as rn
    FROM technical_indicators
    WHERE candle_seconds = 60
) t
WHERE rn = 1;

-- RSI signals: overbought (>70) and oversold (<30)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_rsi_signals AS
SELECT
    pair,
    close,
    rsi_14,
    window_start_ms,
    CASE
        WHEN rsi_14 > 70 THEN 'OVERBOUGHT'
        WHEN rsi_14 < 30 THEN 'OVERSOLD'
        ELSE 'NEUTRAL'
    END as rsi_signal
FROM technical_indicators
WHERE rsi_14 IS NOT NULL
  AND candle_seconds = 60;

-- MACD crossover signals
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_macd_signals AS
SELECT
    pair,
    close,
    macd,
    macd_signal,
    macd_hist,
    window_start_ms,
    CASE
        WHEN macd > macd_signal AND macd_hist > 0 THEN 'BULLISH'
        WHEN macd < macd_signal AND macd_hist < 0 THEN 'BEARISH'
        ELSE 'NEUTRAL'
    END as macd_trend
FROM technical_indicators
WHERE macd IS NOT NULL
  AND candle_seconds = 60;

-- Bollinger Band position (price relative to bands)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_bbands_position AS
SELECT
    pair,
    close,
    bb_lower,
    bb_middle,
    bb_upper,
    window_start_ms,
    CASE
        WHEN close > bb_upper THEN 'ABOVE_UPPER'
        WHEN close < bb_lower THEN 'BELOW_LOWER'
        WHEN close > bb_middle THEN 'UPPER_HALF'
        ELSE 'LOWER_HALF'
    END as bb_position,
    (close - bb_lower) / NULLIF(bb_upper - bb_lower, 0) as bb_percent
FROM technical_indicators
WHERE bb_upper IS NOT NULL
  AND candle_seconds = 60;

-- Trend analysis using multiple MAs
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_trend_analysis AS
SELECT
    pair,
    close,
    sma_7,
    sma_21,
    ema_7,
    ema_21,
    window_start_ms,
    CASE
        WHEN sma_7 > sma_21 AND ema_7 > ema_21 THEN 'UPTREND'
        WHEN sma_7 < sma_21 AND ema_7 < ema_21 THEN 'DOWNTREND'
        ELSE 'SIDEWAYS'
    END as trend,
    ((sma_7 - sma_21) / NULLIF(sma_21, 0)) * 100 as trend_strength_pct
FROM technical_indicators
WHERE sma_7 IS NOT NULL AND sma_21 IS NOT NULL
  AND candle_seconds = 60;
