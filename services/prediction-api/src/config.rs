//! Configuration management for the prediction API.

use std::env;

use crate::error::ApiError;

/// Application configuration loaded from environment variables.
#[derive(Debug, Clone)]
pub struct Config {
    pub api_port: u16,
    pub pg_host: String,
    pub pg_port: u16,
    pub pg_database: String,
    pub pg_user: String,
    pub pg_password: String,
}

impl Config {
    /// Load configuration from environment variables.
    pub fn from_env() -> Result<Self, ApiError> {
        Ok(Self {
            api_port: env::var("API_PORT")
                .unwrap_or_else(|_| "3000".to_string())
                .parse()
                .map_err(|_| ApiError::Config("Invalid API_PORT".to_string()))?,
            pg_host: env::var("PG_HOST")
                .unwrap_or_else(|_| "localhost".to_string()),
            pg_port: env::var("PG_PORT")
                .unwrap_or_else(|_| "4567".to_string())
                .parse()
                .map_err(|_| ApiError::Config("Invalid PG_PORT".to_string()))?,
            pg_database: env::var("PG_DATABASE")
                .unwrap_or_else(|_| "dev".to_string()),
            pg_user: env::var("PG_USER")
                .unwrap_or_else(|_| "root".to_string()),
            pg_password: env::var("PG_PASSWORD")
                .unwrap_or_default(),
        })
    }

    /// Build PostgreSQL connection URL.
    pub fn database_url(&self) -> String {
        if self.pg_password.is_empty() {
            format!(
                "postgres://{}@{}:{}/{}",
                self.pg_user, self.pg_host, self.pg_port, self.pg_database
            )
        } else {
            format!(
                "postgres://{}:{}@{}:{}/{}",
                self.pg_user, self.pg_password, self.pg_host, self.pg_port, self.pg_database
            )
        }
    }
}
