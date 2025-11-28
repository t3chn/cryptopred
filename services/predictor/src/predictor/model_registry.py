"""MLflow model registry utilities."""

from typing import Any

import mlflow
import pandas as pd
from loguru import logger
from mlflow.models import infer_signature


def get_model_name(pair: str, candle_seconds: int, prediction_horizon_seconds: int) -> str:
    """Generate standardized model name.

    Args:
        pair: Trading pair (e.g., "BTCUSDT")
        candle_seconds: Candle duration in seconds
        prediction_horizon_seconds: Prediction horizon in seconds

    Returns:
        Model name like "BTCUSDT_60_300"
    """
    return f"{pair}_{candle_seconds}_{prediction_horizon_seconds}"


def load_model(
    model_name: str,
    model_version: str | None = "latest",
) -> tuple[Any, list[str]]:
    """Load model from MLflow registry.

    Args:
        model_name: Name of the registered model
        model_version: Version to load ("latest" or version number)

    Returns:
        Tuple of (model, feature_names)
    """
    logger.info(f"Loading model {model_name} version {model_version}")

    model_uri = f"models:/{model_name}/{model_version}"
    model = mlflow.sklearn.load_model(model_uri=model_uri)

    # Get model signature to extract features
    model_info = mlflow.models.get_model_info(model_uri=model_uri)
    features = model_info.signature.inputs.input_names()

    logger.info(f"Model loaded with {len(features)} features")
    return model, features


def push_model(
    model: Any,
    X_test: pd.DataFrame,
    model_name: str,
) -> None:
    """Push model to MLflow registry.

    Args:
        model: Trained model object
        X_test: Test data for signature inference
        model_name: Name for model registration
    """
    logger.info(f"Pushing model {model_name} to registry")

    # Infer signature from test data
    y_pred = model.predict(X_test)
    signature = infer_signature(X_test, y_pred)

    # Log and register model
    mlflow.sklearn.log_model(
        sk_model=model,
        artifact_path="model",
        signature=signature,
        registered_model_name=model_name,
    )

    logger.info(f"Model {model_name} registered successfully")
