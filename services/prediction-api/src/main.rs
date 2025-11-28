//! Prediction API - REST API for ML price predictions.
//!
//! A modern Rust API built with Axum, featuring:
//! - OpenAPI/Swagger documentation at /docs
//! - Rate limiting (100 req/sec per IP)
//! - Structured logging with tracing
//! - Proper error handling
//! - Graceful shutdown

use axum::{routing::get, Router};
use sqlx::postgres::PgPoolOptions;
use std::sync::Arc;
use tower_governor::{governor::GovernorConfigBuilder, GovernorLayer};
use tower_http::{cors::CorsLayer, trace::TraceLayer};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};
use utoipa::OpenApi;
use utoipa_swagger_ui::SwaggerUi;

mod config;
mod db;
mod error;
mod routes;

use routes::health::HealthResponse;
use routes::predictions::{Prediction, PredictionQuery};

#[derive(OpenApi)]
#[openapi(
    paths(
        routes::health::health,
        routes::predictions::get_prediction,
        routes::predictions::get_all_latest,
    ),
    components(schemas(HealthResponse, Prediction, PredictionQuery)),
    tags(
        (name = "health", description = "Health check endpoints"),
        (name = "predictions", description = "ML Price Predictions API")
    ),
    info(
        title = "Prediction API",
        version = "0.1.0",
        description = "REST API for ML cryptocurrency price predictions"
    )
)]
struct ApiDoc;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Load .env file if present
    dotenvy::dotenv().ok();

    // Setup tracing
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "prediction_api=debug,tower_http=debug".into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();

    // Load configuration
    let config = config::Config::from_env()?;
    tracing::info!("Configuration loaded");

    // Create database connection pool
    let pool = PgPoolOptions::new()
        .max_connections(10)
        .connect(&config.database_url())
        .await?;

    tracing::info!("Connected to database at {}:{}", config.pg_host, config.pg_port);

    // Rate limiting: 100 requests per second, burst of 50
    let governor_conf = Arc::new(
        GovernorConfigBuilder::default()
            .per_second(100)
            .burst_size(50)
            .finish()
            .expect("Failed to create rate limiter config"),
    );

    // Build router with all layers
    let app = Router::new()
        // API routes
        .route("/health", get(routes::health::health))
        .route("/predictions", get(routes::predictions::get_prediction))
        .route(
            "/predictions/latest",
            get(routes::predictions::get_all_latest),
        )
        // Swagger UI
        .merge(SwaggerUi::new("/docs").url("/api-docs/openapi.json", ApiDoc::openapi()))
        // Middleware layers
        .layer(GovernorLayer::new(governor_conf))
        .layer(TraceLayer::new_for_http())
        .layer(CorsLayer::permissive())
        // Shared state
        .with_state(pool);

    // Start server
    let addr = format!("0.0.0.0:{}", config.api_port);
    tracing::info!("Starting server on {}", addr);
    tracing::info!("Swagger UI available at http://{}/docs", addr);

    let listener = tokio::net::TcpListener::bind(&addr).await?;

    axum::serve(listener, app)
        .with_graceful_shutdown(shutdown_signal())
        .await?;

    tracing::info!("Server stopped");
    Ok(())
}

/// Handle graceful shutdown on SIGINT (Ctrl+C).
async fn shutdown_signal() {
    tokio::signal::ctrl_c()
        .await
        .expect("Failed to install CTRL+C handler");
    tracing::info!("Shutdown signal received, stopping server...");
}
