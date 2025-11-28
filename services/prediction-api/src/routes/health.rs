//! Health check endpoint.

use axum::Json;
use serde::Serialize;
use utoipa::ToSchema;

/// Health check response.
#[derive(Serialize, ToSchema)]
pub struct HealthResponse {
    pub status: String,
}

/// Health check endpoint.
///
/// Returns the health status of the API service.
#[utoipa::path(
    get,
    path = "/health",
    responses(
        (status = 200, description = "Service is healthy", body = HealthResponse)
    ),
    tag = "health"
)]
pub async fn health() -> Json<HealthResponse> {
    Json(HealthResponse {
        status: "healthy".to_string(),
    })
}
