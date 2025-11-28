"""Configuration for predictor service."""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class TrainingConfig(BaseSettings):
    """Training pipeline configuration."""

    model_config = SettingsConfigDict(
        env_file="services/predictor/settings.env",
        env_file_encoding="utf-8",
    )

    # MLflow settings
    mlflow_tracking_uri: str = "http://mlflow-tracking.mlflow.svc.cluster.local:80"
    mlflow_tracking_username: str = "admin"
    mlflow_tracking_password: str = "mlflow123"

    # RisingWave connection
    risingwave_host: str = "risingwave.risingwave.svc.cluster.local"
    risingwave_port: int = 4567
    risingwave_user: str = "root"
    risingwave_password: str = ""
    risingwave_database: str = "dev"
    risingwave_table: str = "technical_indicators"

    # Training parameters
    pair: str = "BTCUSDT"
    training_data_horizon_days: int = 60
    candle_seconds: int = 60
    prediction_horizon_seconds: int = 300  # 5 minutes

    # Features for model
    features: list[str] = [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "window_start_ms",
        "sma_7",
        "sma_14",
        "sma_21",
        "sma_50",
        "ema_7",
        "ema_14",
        "ema_21",
        "ema_50",
        "rsi_7",
        "rsi_14",
        "rsi_21",
        "macd",
        "macd_signal",
        "macd_hist",
        "obv",
    ]

    # Hyperparameter tuning
    hyperparam_search_trials: int = 10
    model_name: Optional[str] = "HuberRegressor"
    n_model_candidates: int = 1

    # Training settings
    train_test_split_ratio: float = 0.8
    max_percentage_rows_with_missing_values: float = 0.01
    max_percentage_diff_mae_wrt_baseline: float = 0.50


class PredictorConfig(BaseSettings):
    """Prediction generator configuration."""

    model_config = SettingsConfigDict(
        env_file="services/predictor/settings.env",
        env_file_encoding="utf-8",
    )

    # MLflow settings
    mlflow_tracking_uri: str = "http://mlflow-tracking.mlflow.svc.cluster.local:80"
    mlflow_tracking_username: str = "admin"
    mlflow_tracking_password: str = "mlflow123"

    # RisingWave connection
    risingwave_host: str = "risingwave.risingwave.svc.cluster.local"
    risingwave_port: int = 4567
    risingwave_user: str = "root"
    risingwave_password: str = ""
    risingwave_database: str = "dev"
    risingwave_schema: str = "public"
    risingwave_input_table: str = "technical_indicators"
    risingwave_output_table: str = "predictions"

    # Prediction parameters
    pair: str = "BTCUSDT"
    candle_seconds: int = 60
    prediction_horizon_seconds: int = 300
    model_version: str = "latest"


training_config = TrainingConfig()
predictor_config = PredictorConfig()
