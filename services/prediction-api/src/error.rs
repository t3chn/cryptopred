//! Error types for the prediction API.

use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use serde_json::json;

/// API error types with proper HTTP status codes.
#[derive(thiserror::Error, Debug)]
pub enum ApiError {
    #[error("Prediction not found for pair: {0}")]
    NotFound(String),

    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),

    #[error("Invalid request: {0}")]
    BadRequest(String),

    #[error("Configuration error: {0}")]
    Config(String),

    #[error("Internal server error")]
    Internal,
}

impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        let (status, message) = match &self {
            ApiError::NotFound(pair) => (
                StatusCode::NOT_FOUND,
                format!("Prediction not found for pair: {}", pair),
            ),
            ApiError::Database(e) => {
                tracing::error!("Database error: {}", e);
                (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    "Database error".to_string(),
                )
            }
            ApiError::BadRequest(msg) => (StatusCode::BAD_REQUEST, msg.clone()),
            ApiError::Config(msg) => {
                tracing::error!("Config error: {}", msg);
                (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    "Configuration error".to_string(),
                )
            }
            ApiError::Internal => (
                StatusCode::INTERNAL_SERVER_ERROR,
                "Internal server error".to_string(),
            ),
        };

        (status, Json(json!({ "error": message }))).into_response()
    }
}
