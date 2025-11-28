"""Tests for model implementations."""

import numpy as np
import pandas as pd
import pytest
from predictor.models import (
    BaselineModel,
    EnsembleModel,
    HuberRegressorWithHyperparameterTuning,
    LightGBMWithHyperparameterTuning,
    get_model_obj,
)


class TestBaselineModel:
    """Tests for baseline model."""

    def test_predict_returns_close_price(self, sample_training_data):
        """Baseline should return close price as prediction."""
        X = sample_training_data.drop(columns=["target"])
        model = BaselineModel()
        predictions = model.predict(X)

        assert len(predictions) == len(X)
        pd.testing.assert_series_equal(
            predictions.reset_index(drop=True),
            X["close"].reset_index(drop=True),
        )

    def test_fit_is_noop(self, sample_training_data):
        """Fit should not raise and return self."""
        X = sample_training_data.drop(columns=["target"])
        y = sample_training_data["target"]

        model = BaselineModel()
        result = model.fit(X, y)

        assert result is model


class TestHuberRegressorWithHyperparameterTuning:
    """Tests for HuberRegressor with tuning."""

    def test_fit_without_tuning(self, sample_training_data):
        """Test fitting without hyperparameter tuning."""
        X = sample_training_data.drop(columns=["target"])
        y = sample_training_data["target"]

        model = HuberRegressorWithHyperparameterTuning()
        model.fit(X, y, hyperparam_search_trials=0)

        predictions = model.predict(X)
        assert len(predictions) == len(X)
        assert not np.any(np.isnan(predictions))

    def test_fit_with_tuning(self, sample_training_data):
        """Test fitting with hyperparameter tuning (few trials)."""
        X = sample_training_data.drop(columns=["target"])
        y = sample_training_data["target"]

        model = HuberRegressorWithHyperparameterTuning()
        model.fit(X, y, hyperparam_search_trials=2, hyperparam_splits=2)

        predictions = model.predict(X)
        assert len(predictions) == len(X)

    def test_predict_returns_array(self, sample_training_data):
        """Predictions should be numpy array."""
        X = sample_training_data.drop(columns=["target"])
        y = sample_training_data["target"]

        model = HuberRegressorWithHyperparameterTuning()
        model.fit(X, y, hyperparam_search_trials=0)

        predictions = model.predict(X)
        assert isinstance(predictions, np.ndarray)


class TestGetModelObj:
    """Tests for model factory."""

    def test_get_huber_regressor(self):
        """Should return HuberRegressor model."""
        model = get_model_obj("HuberRegressor")
        assert isinstance(model, HuberRegressorWithHyperparameterTuning)

    def test_unknown_model_raises(self):
        """Should raise for unknown model name."""
        with pytest.raises(ValueError, match="not found"):
            get_model_obj("UnknownModel")

    def test_get_lightgbm(self):
        """Should return LightGBM model."""
        model = get_model_obj("LightGBM")
        assert isinstance(model, LightGBMWithHyperparameterTuning)

    def test_get_ensemble(self):
        """Should return Ensemble model."""
        model = get_model_obj("Ensemble")
        assert isinstance(model, EnsembleModel)


class TestLightGBMWithHyperparameterTuning:
    """Tests for LightGBM model."""

    def test_fit_without_tuning(self, sample_training_data):
        """Test fitting without hyperparameter tuning."""
        X = sample_training_data.drop(columns=["target"])
        y = sample_training_data["target"]

        model = LightGBMWithHyperparameterTuning()
        model.fit(X, y, hyperparam_search_trials=0)

        predictions = model.predict(X)
        assert len(predictions) == len(X)
        assert not np.any(np.isnan(predictions))

    def test_predict_returns_array(self, sample_training_data):
        """Predictions should be numpy array."""
        X = sample_training_data.drop(columns=["target"])
        y = sample_training_data["target"]

        model = LightGBMWithHyperparameterTuning()
        model.fit(X, y, hyperparam_search_trials=0)

        predictions = model.predict(X)
        assert isinstance(predictions, np.ndarray)


class TestEnsembleModel:
    """Tests for Ensemble model."""

    def test_fit_and_predict(self, sample_training_data):
        """Test ensemble fit and predict."""
        X = sample_training_data.drop(columns=["target"])
        y = sample_training_data["target"]

        model = EnsembleModel()
        model.fit(X, y, hyperparam_search_trials=0)

        predictions = model.predict(X)
        assert len(predictions) == len(X)
        assert not np.any(np.isnan(predictions))

    def test_default_weights(self):
        """Default weights should be equal."""
        model = EnsembleModel()
        assert len(model.weights) == 2  # HuberRegressor + LightGBM
        assert model.weights[0] == model.weights[1] == 0.5

    def test_custom_weights(self):
        """Custom weights should be normalized."""
        model = EnsembleModel(weights=[1, 3])
        assert model.weights[0] == pytest.approx(0.25)
        assert model.weights[1] == pytest.approx(0.75)

    def test_single_model_ensemble(self):
        """Ensemble with single model should work."""
        model = EnsembleModel(use_huber=True, use_lightgbm=False)
        assert len(model.models) == 1
        assert model.weights == [1.0]

    def test_no_models_raises(self):
        """Should raise if no models enabled."""
        with pytest.raises(ValueError, match="At least one model"):
            EnsembleModel(use_huber=False, use_lightgbm=False)

    def test_predict_with_uncertainty(self, sample_training_data):
        """Test uncertainty estimation."""
        X = sample_training_data.drop(columns=["target"])
        y = sample_training_data["target"]

        model = EnsembleModel()
        model.fit(X, y, hyperparam_search_trials=0)

        predictions, uncertainties = model.predict_with_uncertainty(X)
        assert len(predictions) == len(X)
        assert len(uncertainties) == len(X)
        # Uncertainties should be non-negative
        assert np.all(uncertainties >= 0)
