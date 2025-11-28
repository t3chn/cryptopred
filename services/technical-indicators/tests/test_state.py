"""Tests for candle state management."""

from unittest.mock import MagicMock

from technical_indicators.state import is_same_window, update_candles_state


class TestIsSameWindow:
    """Tests for is_same_window function."""

    def test_same_window(self, sample_candle):
        """Test detection of same window candles."""
        candle1 = sample_candle.copy()
        candle2 = sample_candle.copy()
        candle2["close"] = 50300.0  # Different close, same window

        assert is_same_window(candle1, candle2) is True

    def test_different_window_time(self, sample_candle):
        """Test detection of different window by time."""
        candle1 = sample_candle.copy()
        candle2 = sample_candle.copy()
        candle2["window_start_ms"] = sample_candle["window_start_ms"] + 60000

        assert is_same_window(candle1, candle2) is False

    def test_different_pair(self, sample_candle):
        """Test detection of different pair."""
        candle1 = sample_candle.copy()
        candle2 = sample_candle.copy()
        candle2["pair"] = "ETHUSDT"

        assert is_same_window(candle1, candle2) is False


class TestUpdateCandlesState:
    """Tests for update_candles_state function."""

    def _create_mock_state(self, initial_candles=None):
        """Create a mock State object."""
        state = MagicMock()
        storage = {"candles": initial_candles or []}

        def get_side_effect(key, default=None):
            return storage.get(key, default)

        def set_side_effect(key, value):
            storage[key] = value

        state.get = MagicMock(side_effect=get_side_effect)
        state.set = MagicMock(side_effect=set_side_effect)
        state._storage = storage

        return state

    def test_first_candle(self, sample_candle):
        """Test adding first candle to empty state."""
        state = self._create_mock_state()

        result = update_candles_state(sample_candle, state, max_candles=100)

        assert len(result) == 1
        assert result[0] == sample_candle

    def test_update_same_window(self, sample_candle):
        """Test updating candle in same window."""
        initial = sample_candle.copy()
        state = self._create_mock_state([initial])

        updated_candle = sample_candle.copy()
        updated_candle["close"] = 50500.0

        result = update_candles_state(updated_candle, state, max_candles=100)

        assert len(result) == 1
        assert result[0]["close"] == 50500.0

    def test_append_new_window(self, sample_candle):
        """Test appending candle from new window."""
        initial = sample_candle.copy()
        state = self._create_mock_state([initial])

        new_candle = sample_candle.copy()
        new_candle["window_start_ms"] = sample_candle["window_start_ms"] + 60000
        new_candle["window_end_ms"] = sample_candle["window_end_ms"] + 60000

        result = update_candles_state(new_candle, state, max_candles=100)

        assert len(result) == 2

    def test_rolling_window_limit(self, sample_candle):
        """Test that rolling window respects max_candles limit."""
        # Create initial state with 5 candles
        candles = []
        for i in range(5):
            c = sample_candle.copy()
            c["window_start_ms"] = sample_candle["window_start_ms"] + i * 60000
            c["window_end_ms"] = sample_candle["window_end_ms"] + i * 60000
            candles.append(c)

        state = self._create_mock_state(candles)

        # Add new candle with max_candles=5
        new_candle = sample_candle.copy()
        new_candle["window_start_ms"] = sample_candle["window_start_ms"] + 5 * 60000
        new_candle["window_end_ms"] = sample_candle["window_end_ms"] + 5 * 60000

        result = update_candles_state(new_candle, state, max_candles=5)

        assert len(result) == 5
        # First candle should be removed
        assert result[0]["window_start_ms"] == sample_candle["window_start_ms"] + 60000
