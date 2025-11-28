"""Training pipeline for crypto price prediction model."""

import os

import mlflow
import pandas as pd
import psycopg2
from loguru import logger
from sklearn.metrics import mean_absolute_error

from predictor.data_validation import validate_data, validate_features
from predictor.model_registry import get_model_name, push_model
from predictor.models import BaselineModel, get_model_obj


def load_ts_data_from_risingwave(
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
    table: str,
    pair: str,
    training_data_horizon_days: int,
    candle_seconds: int,
) -> pd.DataFrame:
    """Fetch technical indicators data from RisingWave.

    Args:
        host: RisingWave host
        port: RisingWave port
        user: Database user
        password: Database password
        database: Database name
        table: Table name
        pair: Trading pair (e.g., "BTCUSDT")
        training_data_horizon_days: Days of historical data
        candle_seconds: Candle duration

    Returns:
        DataFrame with technical indicators
    """
    logger.info(f"Connecting to RisingWave at {host}:{port}")

    conn = psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
    )

    query = f"""
    SELECT *
    FROM {table}
    WHERE pair = '{pair}'
      AND candle_seconds = {candle_seconds}
      AND to_timestamp(window_start_ms / 1000) > now() - interval '{training_data_horizon_days} days'
    ORDER BY window_start_ms
    """

    logger.info(f"Fetching data for {pair}, last {training_data_horizon_days} days")
    df = pd.read_sql(query, conn)
    conn.close()

    logger.info(f"Fetched {len(df)} rows")
    return df


def train(
    mlflow_tracking_uri: str,
    risingwave_host: str,
    risingwave_port: int,
    risingwave_user: str,
    risingwave_password: str,
    risingwave_database: str,
    risingwave_table: str,
    pair: str,
    training_data_horizon_days: int,
    candle_seconds: int,
    prediction_horizon_seconds: int,
    train_test_split_ratio: float,
    max_percentage_rows_with_missing_values: float,
    features: list[str],
    hyperparam_search_trials: int,
    model_name: str,
    max_percentage_diff_mae_wrt_baseline: float,
) -> None:
    """Train a price prediction model.

    Steps:
    1. Load data from RisingWave
    2. Add target column (future price)
    3. Validate data
    4. Train/test split
    5. Train baseline model
    6. Train model with hyperparameter tuning
    7. Evaluate and push to registry if good
    """
    logger.info("Starting training pipeline")

    # Setup MLflow
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    experiment_name = get_model_name(pair, candle_seconds, prediction_horizon_seconds)
    mlflow.set_experiment(experiment_name)

    with mlflow.start_run():
        # Log parameters
        mlflow.log_param("pair", pair)
        mlflow.log_param("candle_seconds", candle_seconds)
        mlflow.log_param("prediction_horizon_seconds", prediction_horizon_seconds)
        mlflow.log_param("training_data_horizon_days", training_data_horizon_days)
        mlflow.log_param("model_name", model_name)
        mlflow.log_param("hyperparam_search_trials", hyperparam_search_trials)
        mlflow.log_param("features", features)

        # Step 1: Load data
        ts_data = load_ts_data_from_risingwave(
            host=risingwave_host,
            port=risingwave_port,
            user=risingwave_user,
            password=risingwave_password,
            database=risingwave_database,
            table=risingwave_table,
            pair=pair,
            training_data_horizon_days=training_data_horizon_days,
            candle_seconds=candle_seconds,
        )

        # Validate features exist
        validate_features(ts_data, features)

        # Keep only needed features
        ts_data = ts_data[features].copy()

        # Step 2: Add target (future close price)
        shift_periods = prediction_horizon_seconds // candle_seconds
        ts_data["target"] = ts_data["close"].shift(-shift_periods)

        # Log dataset info
        mlflow.log_param("raw_data_shape", ts_data.shape)

        # Step 3: Validate data
        ts_data = validate_data(ts_data, max_percentage_rows_with_missing_values)
        mlflow.log_param("clean_data_shape", ts_data.shape)

        # Step 4: Train/test split (time-series aware - no shuffle)
        train_size = int(len(ts_data) * train_test_split_ratio)
        train_data = ts_data[:train_size]
        test_data = ts_data[train_size:]

        X_train = train_data.drop(columns=["target"])
        y_train = train_data["target"]
        X_test = test_data.drop(columns=["target"])
        y_test = test_data["target"]

        mlflow.log_param("train_size", len(X_train))
        mlflow.log_param("test_size", len(X_test))

        # Step 5: Baseline model
        logger.info("Training baseline model")
        baseline = BaselineModel()
        baseline.fit(X_train, y_train)
        baseline_pred = baseline.predict(X_test)
        baseline_mae = mean_absolute_error(y_test, baseline_pred)
        mlflow.log_metric("test_mae_baseline", baseline_mae)
        logger.info(f"Baseline MAE: {baseline_mae:.4f}")

        # Step 6: Train model with hyperparameter tuning
        logger.info(f"Training {model_name} with {hyperparam_search_trials} trials")
        model = get_model_obj(model_name)
        model.fit(X_train, y_train, hyperparam_search_trials=hyperparam_search_trials)

        # Step 7: Evaluate
        y_pred = model.predict(X_test)
        test_mae = mean_absolute_error(y_test, y_pred)
        mlflow.log_metric("test_mae", test_mae)
        logger.info(f"Model MAE: {test_mae:.4f}")

        # Calculate improvement over baseline
        mae_diff = (test_mae - baseline_mae) / baseline_mae
        mlflow.log_metric("mae_improvement_vs_baseline", -mae_diff)

        # Step 8: Push to registry if better than threshold
        if mae_diff <= max_percentage_diff_mae_wrt_baseline:
            logger.info(f"Model improvement {-mae_diff:.4f} exceeds threshold")
            model_registry_name = get_model_name(pair, candle_seconds, prediction_horizon_seconds)
            push_model(model, X_test, model_registry_name)
            logger.info("Model pushed to registry")
        else:
            logger.warning(
                f"Model improvement {-mae_diff:.4f} below threshold "
                f"{max_percentage_diff_mae_wrt_baseline}, NOT pushing to registry"
            )


def main():
    """Main entry point for training."""
    from predictor.config import training_config as config

    # Set MLflow credentials
    os.environ["MLFLOW_TRACKING_USERNAME"] = config.mlflow_tracking_username
    os.environ["MLFLOW_TRACKING_PASSWORD"] = config.mlflow_tracking_password

    train(
        mlflow_tracking_uri=config.mlflow_tracking_uri,
        risingwave_host=config.risingwave_host,
        risingwave_port=config.risingwave_port,
        risingwave_user=config.risingwave_user,
        risingwave_password=config.risingwave_password,
        risingwave_database=config.risingwave_database,
        risingwave_table=config.risingwave_table,
        pair=config.pair,
        training_data_horizon_days=config.training_data_horizon_days,
        candle_seconds=config.candle_seconds,
        prediction_horizon_seconds=config.prediction_horizon_seconds,
        train_test_split_ratio=config.train_test_split_ratio,
        max_percentage_rows_with_missing_values=config.max_percentage_rows_with_missing_values,
        features=config.features,
        hyperparam_search_trials=config.hyperparam_search_trials,
        model_name=config.model_name,
        max_percentage_diff_mae_wrt_baseline=config.max_percentage_diff_mae_wrt_baseline,
    )


if __name__ == "__main__":
    main()
