"""Real-time prediction generator service."""

import os
import time
from datetime import UTC, datetime

import pandas as pd
import psycopg2
from loguru import logger

from predictor.model_registry import get_model_name, load_model


def get_latest_indicators(
    conn,
    table: str,
    pair: str,
    candle_seconds: int,
    features: list[str],
) -> pd.DataFrame | None:
    """Fetch latest technical indicators from RisingWave.

    Args:
        conn: Database connection
        table: Table name
        pair: Trading pair
        candle_seconds: Candle duration
        features: List of feature columns

    Returns:
        DataFrame with latest row or None
    """
    feature_cols = ", ".join(features)
    query = f"""
    SELECT {feature_cols}, window_start_ms
    FROM {table}
    WHERE pair = '{pair}'
      AND candle_seconds = {candle_seconds}
    ORDER BY window_start_ms DESC
    LIMIT 1
    """

    df = pd.read_sql(query, conn)
    if df.empty:
        return None
    return df


def write_prediction(
    conn,
    table: str,
    predicted_price: float,
    pair: str,
    ts_ms: int,
    model_name: str,
    model_version: str,
    predicted_ts_ms: int,
) -> None:
    """Write prediction to RisingWave.

    Args:
        conn: Database connection
        table: Output table name
        predicted_price: Predicted price
        pair: Trading pair
        ts_ms: Prediction timestamp (ms)
        model_name: Model name
        model_version: Model version
        predicted_ts_ms: Predicted timestamp (ms)
    """
    cursor = conn.cursor()
    query = f"""
    INSERT INTO {table} (predicted_price, pair, ts_ms, model_name, model_version, predicted_ts_ms)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (pair, ts_ms, model_name) DO UPDATE
    SET predicted_price = EXCLUDED.predicted_price,
        model_version = EXCLUDED.model_version,
        predicted_ts_ms = EXCLUDED.predicted_ts_ms
    """
    cursor.execute(
        query,
        (predicted_price, pair, ts_ms, model_name, model_version, predicted_ts_ms),
    )
    conn.commit()
    cursor.close()


def predict(
    mlflow_tracking_uri: str,
    risingwave_host: str,
    risingwave_port: int,
    risingwave_user: str,
    risingwave_password: str,
    risingwave_database: str,
    risingwave_input_table: str,
    risingwave_output_table: str,
    pair: str,
    prediction_horizon_seconds: int,
    candle_seconds: int,
    model_version: str,
    poll_interval_seconds: int = 10,
) -> None:
    """Run prediction loop.

    Continuously polls for new data and generates predictions.

    Args:
        mlflow_tracking_uri: MLflow server URI
        risingwave_host: RisingWave host
        risingwave_port: RisingWave port
        risingwave_user: Database user
        risingwave_password: Database password
        risingwave_database: Database name
        risingwave_input_table: Input table name
        risingwave_output_table: Output table name
        pair: Trading pair
        prediction_horizon_seconds: Prediction horizon
        candle_seconds: Candle duration
        model_version: Model version to use
        poll_interval_seconds: Polling interval
    """
    # Load model from registry
    model_name = get_model_name(pair, candle_seconds, prediction_horizon_seconds)
    logger.info(f"Loading model {model_name} version {model_version}")

    import mlflow

    mlflow.set_tracking_uri(mlflow_tracking_uri)
    model, features = load_model(model_name, model_version)

    logger.info(f"Model loaded with features: {features}")

    # Connect to RisingWave
    logger.info(f"Connecting to RisingWave at {risingwave_host}:{risingwave_port}")
    conn = psycopg2.connect(
        host=risingwave_host,
        port=risingwave_port,
        user=risingwave_user,
        password=risingwave_password,
        database=risingwave_database,
    )

    last_window_start_ms = 0

    logger.info("Starting prediction loop")
    while True:
        try:
            # Get latest indicators
            data = get_latest_indicators(
                conn=conn,
                table=risingwave_input_table,
                pair=pair,
                candle_seconds=candle_seconds,
                features=features,
            )

            if data is not None:
                window_start_ms = int(data["window_start_ms"].iloc[0])

                # Only predict on new data
                if window_start_ms > last_window_start_ms:
                    last_window_start_ms = window_start_ms

                    # Prepare features
                    X = data[features]

                    # Generate prediction
                    prediction = model.predict(X)[0]

                    # Calculate timestamps
                    ts_ms = int(datetime.now(UTC).timestamp() * 1000)
                    predicted_ts_ms = (
                        window_start_ms + (candle_seconds + prediction_horizon_seconds) * 1000
                    )

                    # Write prediction
                    write_prediction(
                        conn=conn,
                        table=risingwave_output_table,
                        predicted_price=float(prediction),
                        pair=pair,
                        ts_ms=ts_ms,
                        model_name=model_name,
                        model_version=model_version,
                        predicted_ts_ms=predicted_ts_ms,
                    )

                    logger.info(
                        f"Prediction: {pair} @ {prediction:.2f} "
                        f"(window: {window_start_ms}, predicted_ts: {predicted_ts_ms})"
                    )

        except Exception as e:
            logger.error(f"Prediction error: {e}")
            # Reconnect on error
            try:
                conn.close()
            except Exception:
                pass
            conn = psycopg2.connect(
                host=risingwave_host,
                port=risingwave_port,
                user=risingwave_user,
                password=risingwave_password,
                database=risingwave_database,
            )

        time.sleep(poll_interval_seconds)


def main():
    """Main entry point for prediction service."""
    from predictor.config import predictor_config as config

    # Set MLflow credentials
    os.environ["MLFLOW_TRACKING_USERNAME"] = config.mlflow_tracking_username
    os.environ["MLFLOW_TRACKING_PASSWORD"] = config.mlflow_tracking_password

    predict(
        mlflow_tracking_uri=config.mlflow_tracking_uri,
        risingwave_host=config.risingwave_host,
        risingwave_port=config.risingwave_port,
        risingwave_user=config.risingwave_user,
        risingwave_password=config.risingwave_password,
        risingwave_database=config.risingwave_database,
        risingwave_input_table=config.risingwave_input_table,
        risingwave_output_table=config.risingwave_output_table,
        pair=config.pair,
        prediction_horizon_seconds=config.prediction_horizon_seconds,
        candle_seconds=config.candle_seconds,
        model_version=config.model_version,
    )


if __name__ == "__main__":
    main()
