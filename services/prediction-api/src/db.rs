//! Database operations for predictions.

use sqlx::{PgPool, Row};

use crate::error::ApiError;
use crate::routes::predictions::Prediction;

/// Get the latest prediction for a specific trading pair.
pub async fn get_latest_prediction(
    pool: &PgPool,
    pair: &str,
) -> Result<Option<Prediction>, ApiError> {
    let row = sqlx::query(
        r#"
        SELECT pair, predicted_price, ts_ms, predicted_ts_ms, model_name, model_version
        FROM predictions
        WHERE pair = $1
        ORDER BY ts_ms DESC
        LIMIT 1
        "#,
    )
    .bind(pair)
    .fetch_optional(pool)
    .await?;

    match row {
        Some(row) => Ok(Some(Prediction {
            pair: row.get("pair"),
            predicted_price: row.get("predicted_price"),
            ts_ms: row.get("ts_ms"),
            predicted_ts_ms: row.get("predicted_ts_ms"),
            model_name: row.get("model_name"),
            model_version: row.get("model_version"),
        })),
        None => Ok(None),
    }
}

/// Get the latest predictions for all trading pairs.
pub async fn get_all_latest_predictions(pool: &PgPool) -> Result<Vec<Prediction>, ApiError> {
    let rows = sqlx::query(
        r#"
        SELECT DISTINCT ON (pair)
            pair, predicted_price, ts_ms, predicted_ts_ms, model_name, model_version
        FROM predictions
        ORDER BY pair, ts_ms DESC
        "#,
    )
    .fetch_all(pool)
    .await?;

    let predictions = rows
        .into_iter()
        .map(|row| Prediction {
            pair: row.get("pair"),
            predicted_price: row.get("predicted_price"),
            ts_ms: row.get("ts_ms"),
            predicted_ts_ms: row.get("predicted_ts_ms"),
            model_name: row.get("model_name"),
            model_version: row.get("model_version"),
        })
        .collect();

    Ok(predictions)
}
