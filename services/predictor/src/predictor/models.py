"""Model definitions with hyperparameter tuning."""

from typing import Optional

import numpy as np
import optuna
import pandas as pd
from loguru import logger
from sklearn.linear_model import HuberRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


class BaselineModel:
    """Baseline model: predicts current price as future price."""

    def __init__(self):
        """Initialize baseline model."""
        pass

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "BaselineModel":
        """Fit is a no-op for baseline."""
        return self

    def predict(self, X: pd.DataFrame) -> pd.Series:
        """Predict: return current close price."""
        return X["close"]


class HuberRegressorWithHyperparameterTuning:
    """HuberRegressor with Optuna hyperparameter tuning."""

    def __init__(self):
        """Initialize model with default pipeline."""
        self.pipeline = self._get_pipeline()
        self.hyperparam_search_trials: Optional[int] = None
        self.hyperparam_splits: int = 3

    def _get_pipeline(self, model_hyperparams: Optional[dict] = None) -> Pipeline:
        """Create sklearn pipeline with preprocessing and model.

        Args:
            model_hyperparams: Optional hyperparameters for HuberRegressor

        Returns:
            sklearn Pipeline
        """
        if model_hyperparams is None:
            return Pipeline(
                steps=[("preprocessor", StandardScaler()), ("model", HuberRegressor())]
            )
        return Pipeline(
            steps=[
                ("preprocessor", StandardScaler()),
                ("model", HuberRegressor(**model_hyperparams)),
            ]
        )

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        hyperparam_search_trials: int = 0,
        hyperparam_splits: int = 3,
    ) -> "HuberRegressorWithHyperparameterTuning":
        """Fit model with optional hyperparameter tuning.

        Args:
            X: Training features
            y: Training target
            hyperparam_search_trials: Number of Optuna trials (0 = no tuning)
            hyperparam_splits: Number of TimeSeriesSplit folds

        Returns:
            Self
        """
        self.hyperparam_search_trials = hyperparam_search_trials
        self.hyperparam_splits = hyperparam_splits

        if hyperparam_search_trials == 0:
            logger.info("Fitting with default hyperparameters")
            self.pipeline.fit(X, y)
        else:
            logger.info(
                f"Running hyperparameter search with {hyperparam_search_trials} trials"
            )
            best_hyperparams = self._find_best_hyperparams(X, y)
            logger.info(f"Best hyperparameters: {best_hyperparams}")
            self.pipeline = self._get_pipeline(best_hyperparams)
            self.pipeline.fit(X, y)

        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Generate predictions.

        Args:
            X: Features

        Returns:
            Predictions array
        """
        return self.pipeline.predict(X)

    def _find_best_hyperparams(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
    ) -> dict:
        """Find best hyperparameters using Optuna with TimeSeriesSplit.

        Args:
            X_train: Training features
            y_train: Training target

        Returns:
            Best hyperparameters dict
        """

        def objective(trial: optuna.Trial) -> float:
            """Optuna objective function."""
            params = {
                "epsilon": trial.suggest_float("epsilon", 1.0, 1e8, log=True),
                "alpha": trial.suggest_float("alpha", 1e-4, 1.0, log=True),
                "max_iter": trial.suggest_int("max_iter", 100, 1000),
                "tol": trial.suggest_float("tol", 1e-5, 1e-2, log=True),
                "fit_intercept": trial.suggest_categorical(
                    "fit_intercept", [True, False]
                ),
            }

            # TimeSeriesSplit cross-validation
            tscv = TimeSeriesSplit(n_splits=self.hyperparam_splits)
            mae_scores = []

            for train_idx, val_idx in tscv.split(X_train):
                X_train_fold = X_train.iloc[train_idx]
                X_val_fold = X_train.iloc[val_idx]
                y_train_fold = y_train.iloc[train_idx]
                y_val_fold = y_train.iloc[val_idx]

                pipeline = self._get_pipeline(model_hyperparams=params)
                pipeline.fit(X_train_fold, y_train_fold)

                y_pred = pipeline.predict(X_val_fold)
                mae = mean_absolute_error(y_val_fold, y_pred)
                mae_scores.append(mae)

            return np.mean(mae_scores)

        # Create and run study
        optuna.logging.set_verbosity(optuna.logging.WARNING)
        study = optuna.create_study(direction="minimize")
        study.optimize(
            objective, n_trials=self.hyperparam_search_trials, show_progress_bar=True
        )

        return study.best_trial.params


def get_model_obj(model_name: str) -> HuberRegressorWithHyperparameterTuning:
    """Factory function to get model by name.

    Args:
        model_name: Name of model class

    Returns:
        Model instance

    Raises:
        ValueError: If model not found
    """
    if model_name == "HuberRegressor":
        return HuberRegressorWithHyperparameterTuning()
    raise ValueError(f"Model {model_name} not found")
