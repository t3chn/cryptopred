//! Prediction endpoints.

use axum::{
    extract::{Query, State},
    Json,
};
use serde::{Deserialize, Serialize};
use sqlx::PgPool;
use utoipa::{IntoParams, ToSchema};

use crate::db;
use crate::error::ApiError;

/// Query parameters for getting a prediction.
#[derive(Debug, Deserialize, IntoParams, ToSchema)]
pub struct PredictionQuery {
    /// Trading pair (e.g., "BTCUSDT")
    pub pair: String,
}

impl PredictionQuery {
    /// Validate the query parameters.
    pub fn validate(&self) -> Result<(), ApiError> {
        if self.pair.is_empty() {
            return Err(ApiError::BadRequest("pair cannot be empty".to_string()));
        }
        if self.pair.len() > 20 {
            return Err(ApiError::BadRequest("pair is too long".to_string()));
        }
        // Basic alphanumeric check
        if !self.pair.chars().all(|c| c.is_alphanumeric()) {
            return Err(ApiError::BadRequest(
                "pair must be alphanumeric".to_string(),
            ));
        }
        Ok(())
    }
}

/// Prediction response.
#[derive(Debug, Serialize, ToSchema)]
pub struct Prediction {
    /// Trading pair
    pub pair: String,
    /// Predicted price
    pub predicted_price: f64,
    /// Timestamp when prediction was made (ms)
    pub ts_ms: i64,
    /// Timestamp for which price is predicted (ms)
    pub predicted_ts_ms: i64,
    /// Model name used for prediction
    pub model_name: String,
    /// Model version
    pub model_version: String,
}

/// Get the latest prediction for a trading pair.
///
/// Returns the most recent price prediction for the specified trading pair.
#[utoipa::path(
    get,
    path = "/predictions",
    params(PredictionQuery),
    responses(
        (status = 200, description = "Prediction found", body = Prediction),
        (status = 400, description = "Invalid request"),
        (status = 404, description = "Prediction not found")
    ),
    tag = "predictions"
)]
#[tracing::instrument(skip(pool))]
pub async fn get_prediction(
    State(pool): State<PgPool>,
    Query(params): Query<PredictionQuery>,
) -> Result<Json<Prediction>, ApiError> {
    params.validate()?;

    tracing::info!(pair = %params.pair, "Fetching prediction");

    let prediction = db::get_latest_prediction(&pool, &params.pair).await?;

    match prediction {
        Some(p) => {
            tracing::debug!(pair = %p.pair, price = %p.predicted_price, "Prediction found");
            Ok(Json(p))
        }
        None => {
            tracing::warn!(pair = %params.pair, "Prediction not found");
            Err(ApiError::NotFound(params.pair))
        }
    }
}

/// Get the latest predictions for all trading pairs.
///
/// Returns the most recent price prediction for each trading pair.
#[utoipa::path(
    get,
    path = "/predictions/latest",
    responses(
        (status = 200, description = "List of latest predictions", body = Vec<Prediction>)
    ),
    tag = "predictions"
)]
#[tracing::instrument(skip(pool))]
pub async fn get_all_latest(State(pool): State<PgPool>) -> Result<Json<Vec<Prediction>>, ApiError> {
    tracing::info!("Fetching all latest predictions");

    let predictions = db::get_all_latest_predictions(&pool).await?;

    tracing::debug!(count = predictions.len(), "Predictions fetched");

    Ok(Json(predictions))
}
