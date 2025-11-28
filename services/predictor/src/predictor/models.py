"""Model definitions with hyperparameter tuning."""

import numpy as np
import optuna
import pandas as pd
from lightgbm import LGBMRegressor
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
        self.hyperparam_search_trials: int | None = None
        self.hyperparam_splits: int = 3

    def _get_pipeline(self, model_hyperparams: dict | None = None) -> Pipeline:
        """Create sklearn pipeline with preprocessing and model.

        Args:
            model_hyperparams: Optional hyperparameters for HuberRegressor

        Returns:
            sklearn Pipeline
        """
        if model_hyperparams is None:
            return Pipeline(steps=[("preprocessor", StandardScaler()), ("model", HuberRegressor())])
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
            logger.info(f"Running hyperparameter search with {hyperparam_search_trials} trials")
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
                "fit_intercept": trial.suggest_categorical("fit_intercept", [True, False]),
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
        study.optimize(objective, n_trials=self.hyperparam_search_trials, show_progress_bar=True)

        return study.best_trial.params


class LightGBMWithHyperparameterTuning:
    """LightGBM Regressor with Optuna hyperparameter tuning.

    LightGBM is known to perform 18% better than XGBoost for financial data
    according to research. It's faster and more memory efficient.
    """

    def __init__(self):
        """Initialize model with default pipeline."""
        self.pipeline = self._get_pipeline()
        self.hyperparam_search_trials: int | None = None
        self.hyperparam_splits: int = 3

    def _get_pipeline(self, model_hyperparams: dict | None = None) -> Pipeline:
        """Create sklearn pipeline with preprocessing and model.

        Args:
            model_hyperparams: Optional hyperparameters for LGBMRegressor

        Returns:
            sklearn Pipeline
        """
        default_params = {
            "verbosity": -1,
            "n_jobs": -1,
            "random_state": 42,
        }
        if model_hyperparams is None:
            return Pipeline(
                steps=[
                    ("preprocessor", StandardScaler()),
                    ("model", LGBMRegressor(**default_params)),
                ]
            )
        params = {**default_params, **model_hyperparams}
        return Pipeline(
            steps=[
                ("preprocessor", StandardScaler()),
                ("model", LGBMRegressor(**params)),
            ]
        )

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        hyperparam_search_trials: int = 0,
        hyperparam_splits: int = 3,
    ) -> "LightGBMWithHyperparameterTuning":
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
            logger.info("Fitting LightGBM with default hyperparameters")
            self.pipeline.fit(X, y)
        else:
            logger.info(
                f"Running LightGBM hyperparameter search with {hyperparam_search_trials} trials"
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
            """Optuna objective function for LightGBM."""
            params = {
                "num_leaves": trial.suggest_int("num_leaves", 20, 150),
                "max_depth": trial.suggest_int("max_depth", 3, 12),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                "n_estimators": trial.suggest_int("n_estimators", 50, 500),
                "min_child_samples": trial.suggest_int("min_child_samples", 5, 100),
                "subsample": trial.suggest_float("subsample", 0.5, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
                "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
                "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
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
        study.optimize(objective, n_trials=self.hyperparam_search_trials, show_progress_bar=True)

        return study.best_trial.params


def get_model_obj(
    model_name: str,
) -> HuberRegressorWithHyperparameterTuning | LightGBMWithHyperparameterTuning:
    """Factory function to get model by name.

    Args:
        model_name: Name of model class. Supported: HuberRegressor, LightGBM

    Returns:
        Model instance

    Raises:
        ValueError: If model not found
    """
    if model_name == "HuberRegressor":
        return HuberRegressorWithHyperparameterTuning()
    if model_name == "LightGBM":
        return LightGBMWithHyperparameterTuning()
    raise ValueError(f"Model {model_name} not found. Available: HuberRegressor, LightGBM")
