import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

from services.data_fetcher import DataFetcher, MARKET_SUFFIXES


class TestBuildTickerSymbol:
    """Tests for _build_ticker_symbol method"""

    def test_us_market_no_suffix(self):
        fetcher = DataFetcher()
        result = fetcher._build_ticker_symbol("AAPL", "US")
        assert result == "AAPL"

    def test_ar_market_adds_ba_suffix(self):
        fetcher = DataFetcher()
        result = fetcher._build_ticker_symbol("YPF", "AR")
        assert result == "YPF.BA"

    def test_ar_market_symbol_already_has_suffix(self):
        fetcher = DataFetcher()
        result = fetcher._build_ticker_symbol("YPF.BA", "AR")
        assert result == "YPF.BA"

    def test_jp_market_no_suffix(self):
        fetcher = DataFetcher()
        result = fetcher._build_ticker_symbol("TM", "JP")
        assert result == "TM"

    def test_eu_market_no_suffix(self):
        fetcher = DataFetcher()
        result = fetcher._build_ticker_symbol("SAP.DE", "EU")
        assert result == "SAP.DE"

    def test_lowercase_market_works(self):
        fetcher = DataFetcher()
        result = fetcher._build_ticker_symbol("YPF", "ar")
        assert result == "YPF.BA"

    def test_unknown_market_no_suffix(self):
        fetcher = DataFetcher()
        result = fetcher._build_ticker_symbol("AAPL", "XX")
        assert result == "AAPL"


class TestFetchData:
    """Tests for fetch_data method"""

    def _create_sample_df(self, days=60):
        """Create a sample DataFrame for testing"""
        dates = [datetime(2026, 4, 25) - timedelta(days=i) for i in range(days, 0, -1)]
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(days) * 2)

        return pd.DataFrame({
            'Date': dates,
            'Open': prices - np.random.uniform(0.5, 1.5, days),
            'High': prices + np.random.uniform(0.5, 2, days),
            'Low': prices - np.random.uniform(0.5, 2, days),
            'Close': prices,
            'Volume': np.random.randint(1000000, 5000000, days)
        })

    @patch('services.data_fetcher.yf.Ticker')
    def test_returns_dataframe_when_valid(self, mock_ticker_class):
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = self._create_sample_df(60)
        mock_ticker_class.return_value = mock_ticker

        fetcher = DataFetcher()
        result = fetcher.fetch_data("AAPL", "US")

        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert 'close' in result.columns
        assert len(result) >= 30

    @patch('services.data_fetcher.yf.Ticker')
    def test_returns_none_when_dataframe_empty(self, mock_ticker_class):
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame()
        mock_ticker_class.return_value = mock_ticker

        fetcher = DataFetcher()
        result = fetcher.fetch_data("INVALID", "US")

        assert result is None

    @patch('services.data_fetcher.yf.Ticker')
    def test_returns_none_when_missing_columns(self, mock_ticker_class):
        mock_ticker = MagicMock()
        df = self._create_sample_df(60)
        df = df.drop(columns=['Open'])
        mock_ticker.history.return_value = df
        mock_ticker_class.return_value = mock_ticker

        fetcher = DataFetcher()
        result = fetcher.fetch_data("AAPL", "US")

        assert result is None

    @patch('services.data_fetcher.yf.Ticker')
    def test_returns_none_when_insufficient_data(self, mock_ticker_class):
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = self._create_sample_df(10)
        mock_ticker_class.return_value = mock_ticker

        fetcher = DataFetcher()
        result = fetcher.fetch_data("AAPL", "US")

        assert result is None

    @patch('services.data_fetcher.yf.Ticker')
    def test_returns_none_on_exception(self, mock_ticker_class):
        mock_ticker = MagicMock()
        mock_ticker.history.side_effect = Exception("Network error")
        mock_ticker_class.return_value = mock_ticker

        fetcher = DataFetcher()
        result = fetcher.fetch_data("AAPL", "US")

        assert result is None

    @patch('services.data_fetcher.yf.Ticker')
    def test_uses_correct_ticker_symbol_for_ar_market(self, mock_ticker_class):
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = self._create_sample_df(60)
        mock_ticker_class.return_value = mock_ticker

        fetcher = DataFetcher()
        fetcher.fetch_data("YPF", "AR")

        mock_ticker_class.assert_called_once_with("YPF.BA")

    @patch('services.data_fetcher.yf.Ticker')
    def test_resets_index_and_lowercases_columns(self, mock_ticker_class):
        mock_ticker = MagicMock()
        df = self._create_sample_df(60)
        mock_ticker.history.return_value = df
        mock_ticker_class.return_value = mock_ticker

        fetcher = DataFetcher()
        result = fetcher.fetch_data("AAPL", "US")

        assert 'index' in result.columns
        assert 'close' in result.columns
        assert 'open' in result.columns
        assert 'high' in result.columns
        assert 'low' in result.columns
        assert 'volume' in result.columns


class TestHasValidData:
    """Tests for has_valid_data method"""

    def _create_sample_df(self, days=60):
        dates = [datetime(2026, 4, 25) - timedelta(days=i) for i in range(days, 0, -1)]
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(days) * 2)

        return pd.DataFrame({
            'Date': dates,
            'Open': prices - np.random.uniform(0.5, 1.5, days),
            'High': prices + np.random.uniform(0.5, 2, days),
            'Low': prices - np.random.uniform(0.5, 2, days),
            'Close': prices,
            'Volume': np.random.randint(1000000, 5000000, days)
        })

    @patch('services.data_fetcher.yf.Ticker')
    def test_returns_true_when_valid_data(self, mock_ticker_class):
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = self._create_sample_df(60)
        mock_ticker_class.return_value = mock_ticker

        fetcher = DataFetcher()
        result = fetcher.has_valid_data("AAPL", "US")

        assert result is True

    @patch('services.data_fetcher.yf.Ticker')
    def test_returns_false_when_no_data(self, mock_ticker_class):
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame()
        mock_ticker_class.return_value = mock_ticker

        fetcher = DataFetcher()
        result = fetcher.has_valid_data("INVALID", "US")

        assert result is False

    @patch('services.data_fetcher.yf.Ticker')
    def test_returns_false_when_insufficient_data(self, mock_ticker_class):
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = self._create_sample_df(10)
        mock_ticker_class.return_value = mock_ticker

        fetcher = DataFetcher()
        result = fetcher.has_valid_data("AAPL", "US")

        assert result is False