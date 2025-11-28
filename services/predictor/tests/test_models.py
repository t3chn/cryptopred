"""Tests for model implementations."""

import numpy as np
import pandas as pd
import pytest

from predictor.models import (
    BaselineModel,
    HuberRegressorWithHyperparameterTuning,
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
