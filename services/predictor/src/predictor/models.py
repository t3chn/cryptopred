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


class EnsembleModel:
    """Ensemble model combining multiple base models.

    Combines HuberRegressor and LightGBM predictions using weighted averaging.
    Ensemble methods typically improve prediction accuracy by:
    - Reducing variance (averaging smooths predictions)
    - Capturing different patterns (each model has different inductive biases)
    - Improving robustness (single model failures are diluted)
    """

    def __init__(
        self,
        weights: list[float] | None = None,
        use_huber: bool = True,
        use_lightgbm: bool = True,
    ):
        """Initialize ensemble model.

        Args:
            weights: Optional list of weights for [huber, lightgbm].
                If None, uses equal weights.
            use_huber: Include HuberRegressor in ensemble
            use_lightgbm: Include LightGBM in ensemble
        """
        self.models: list[
            HuberRegressorWithHyperparameterTuning | LightGBMWithHyperparameterTuning
        ] = []
        self.model_names: list[str] = []

        if use_huber:
            self.models.append(HuberRegressorWithHyperparameterTuning())
            self.model_names.append("HuberRegressor")
        if use_lightgbm:
            self.models.append(LightGBMWithHyperparameterTuning())
            self.model_names.append("LightGBM")

        if len(self.models) == 0:
            raise ValueError("At least one model must be enabled")

        if weights is None:
            self.weights = [1.0 / len(self.models)] * len(self.models)
        else:
            if len(weights) != len(self.models):
                raise ValueError(f"Expected {len(self.models)} weights, got {len(weights)}")
            total = sum(weights)
            self.weights = [w / total for w in weights]  # Normalize to sum to 1

        self.hyperparam_search_trials: int = 0
        self.hyperparam_splits: int = 3

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        hyperparam_search_trials: int = 0,
        hyperparam_splits: int = 3,
    ) -> "EnsembleModel":
        """Fit all models in ensemble.

        Args:
            X: Training features
            y: Training target
            hyperparam_search_trials: Number of Optuna trials per model (0 = no tuning)
            hyperparam_splits: Number of TimeSeriesSplit folds

        Returns:
            Self
        """
        self.hyperparam_search_trials = hyperparam_search_trials
        self.hyperparam_splits = hyperparam_splits

        logger.info(f"Fitting ensemble with {len(self.models)} models: {self.model_names}")

        for i, model in enumerate(self.models):
            logger.info(f"Fitting model {i + 1}/{len(self.models)}: {self.model_names[i]}")
            model.fit(X, y, hyperparam_search_trials, hyperparam_splits)

        logger.info(f"Ensemble weights: {dict(zip(self.model_names, self.weights, strict=True))}")
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Generate weighted ensemble predictions.

        Args:
            X: Features

        Returns:
            Weighted average predictions
        """
        predictions = []
        for model in self.models:
            pred = model.predict(X)
            predictions.append(pred)

        # Weighted average
        ensemble_pred = np.zeros(len(X))
        for pred, weight in zip(predictions, self.weights, strict=True):
            ensemble_pred += weight * np.array(pred)

        return ensemble_pred

    def predict_with_uncertainty(self, X: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        """Generate predictions with uncertainty estimates.

        Uses disagreement between models as uncertainty measure.

        Args:
            X: Features

        Returns:
            Tuple of (predictions, standard_deviations)
        """
        predictions = []
        for model in self.models:
            pred = model.predict(X)
            predictions.append(np.array(pred))

        predictions_array = np.array(predictions)  # Shape: (n_models, n_samples)

        # Weighted mean
        mean_pred = np.average(predictions_array, axis=0, weights=self.weights)

        # Standard deviation across models (uncertainty)
        std_pred = np.std(predictions_array, axis=0)

        return mean_pred, std_pred


ModelType = (
    HuberRegressorWithHyperparameterTuning | LightGBMWithHyperparameterTuning | EnsembleModel
)


def get_model_obj(
    model_name: str,
) -> ModelType:
    """Factory function to get model by name.

    Args:
        model_name: Name of model class. Supported: HuberRegressor, LightGBM, Ensemble

    Returns:
        Model instance

    Raises:
        ValueError: If model not found
    """
    if model_name == "HuberRegressor":
        return HuberRegressorWithHyperparameterTuning()
    if model_name == "LightGBM":
        return LightGBMWithHyperparameterTuning()
    if model_name == "Ensemble":
        return EnsembleModel()
    raise ValueError(f"Model {model_name} not found. Available: HuberRegressor, LightGBM, Ensemble")
