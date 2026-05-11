import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from unittest.mock import patch, MagicMock

from services.scheduler import _safe_float, _clean_dict, create_signal_dict


class TestSafeFloat:
    """Tests for _safe_float function"""

    def test_returns_zero_for_none(self):
        assert _safe_float(None) == 0.0

    def test_returns_zero_for_nan(self):
        assert _safe_float(float('nan')) == 0.0

    def test_returns_zero_for_inf(self):
        assert _safe_float(float('inf')) == 0.0
        assert _safe_float(float('-inf')) == 0.0

    def test_returns_float_for_valid_float(self):
        assert _safe_float(42.5) == 42.5
        assert _safe_float(-10.3) == -10.3

    def test_converts_int_to_float(self):
        assert _safe_float(42) == 42.0
        assert _safe_float(0) == 0.0

    def test_converts_string_to_float(self):
        assert _safe_float("42.5") == 42.5
        assert _safe_float("100") == 100.0

    def test_returns_zero_for_invalid_string(self):
        assert _safe_float("invalid") == 0.0


class TestCleanDict:
    """Tests for _clean_dict function"""

    def test_returns_empty_dict_for_empty_input(self):
        assert _clean_dict({}) == {}

    def test_passes_through_non_float_values(self):
        result = _clean_dict({"name": "AAPL", "count": 5})
        assert result == {"name": "AAPL", "count": 5}

    def test_replaces_nan_with_zero(self):
        result = _clean_dict({"value": float('nan')})
        assert result["value"] == 0.0

    def test_replaces_inf_with_zero(self):
        result = _clean_dict({"value": float('inf')})
        assert result["value"] == 0.0

    def test_replaces_negative_inf_with_zero(self):
        result = _clean_dict({"value": float('-inf')})
        assert result["value"] == 0.0

    def test_rounds_float_to_4_decimal_places(self):
        result = _clean_dict({"value": 3.14159265})
        assert result["value"] == 3.1416

    def test_preserves_small_floats(self):
        result = _clean_dict({"value": 0.0001})
        assert result["value"] == 0.0001

    def test_recursively_cleans_nested_dicts(self):
        nested = {"outer": {"inner": float('nan')}}
        result = _clean_dict(nested)
        assert result["outer"]["inner"] == 0.0

    def test_preserves_lists(self):
        result = _clean_dict({"items": [1, 2, 3]})
        assert result["items"] == [1, 2, 3]

    def test_cleans_dicts_inside_lists(self):
        result = _clean_dict({"items": [{"value": float('nan')}]})
        assert result["items"][0]["value"] == 0.0


class TestCreateSignalDict:
    """Tests for create_signal_dict function"""

    def _create_sample_df(self):
        """Create a sample DataFrame for testing"""
        dates = [datetime(2026, 4, 25) - pd.Timedelta(days=i) for i in range(10, 0, -1)]
        np.random.seed(42)
        prices = [100 + i * 2 for i in range(10)]

        return pd.DataFrame({
            'close': prices,
            'volume': [1000000] * 10
        })

    @patch('services.scheduler.get_company_info')
    def test_creates_basic_signal_dict(self, mock_get_info):
        mock_get_info.return_value = {
            "name": "Apple Inc.",
            "logo": "https://logo.url",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "exchange": "NASDAQ",
            "country": "US",
            "marketCap": 3000000000
        }

        df = self._create_sample_df()
        indicators = {'rsi': 45.0, 'ema20': 110.0, 'ema50': 105.0, 'macd': 1.0, 'atr': 2.5, 'avg_volume': 1000000}
        signal = {'signal_type': 'BUY', 'trend': 'BULLISH', 'explanation': 'Test', 'reasons': ['RSI oversold']}
        price = 120.0

        result = create_signal_dict('AAPL', 'US', indicators, signal, price, df)

        assert result['symbol'] == 'AAPL'
        assert result['market'] == 'US'
        assert result['companyName'] == 'Apple Inc.'
        assert result['signalType'] == 'BUY'
        assert result['trend'] == 'BULLISH'
        assert result['rsi'] == 45.0

    @patch('services.scheduler.get_company_info')
    def test_calculates_price_change_24h(self, mock_get_info):
        mock_get_info.return_value = {"name": "AAPL", "logo": "", "sector": "", "industry": "", "exchange": "", "country": "", "marketCap": None}

        df = self._create_sample_df()
        indicators = {'rsi': 50, 'ema20': 110, 'ema50': 105, 'macd': 0, 'atr': 1, 'avg_volume': 1000000}
        signal = {'signal_type': 'HOLD', 'trend': 'LATERAL', 'explanation': '', 'reasons': []}
        price = 118.0

        result = create_signal_dict('AAPL', 'US', indicators, signal, price, df)

        assert result['priceChange24h'] == 2.0
        assert result['priceChangePercent24h'] == pytest.approx(1.724, rel=0.01)

    @patch('services.scheduler.get_company_info')
    def test_uses_symbol_as_company_name_when_meta_not_available(self, mock_get_info):
        mock_get_info.return_value = {"name": "UNKNOWN", "logo": "", "sector": "", "industry": "", "exchange": "", "country": "", "marketCap": None}

        df = self._create_sample_df()
        indicators = {'rsi': 50, 'ema20': 110, 'ema50': 105, 'macd': 0, 'atr': 1, 'avg_volume': 1000000}
        signal = {'signal_type': 'HOLD', 'trend': 'LATERAL', 'explanation': '', 'reasons': []}
        price = 100.0

        result = create_signal_dict('UNKNOWN', 'US', indicators, signal, price, df)

        assert result['companyName'] == 'UNKNOWN'

    @patch('services.scheduler.get_company_info')
    def test_handles_dataframe_with_single_row(self, mock_get_info):
        mock_get_info.return_value = {"name": "AAPL", "logo": "", "sector": "", "industry": "", "exchange": "", "country": "", "marketCap": None}

        df = pd.DataFrame({
            'close': [100],
            'volume': [1000000]
        })
        indicators = {'rsi': 50, 'ema20': 110, 'ema50': 105, 'macd': 0, 'atr': 1, 'avg_volume': 1000000}
        signal = {'signal_type': 'HOLD', 'trend': 'LATERAL', 'explanation': '', 'reasons': []}
        price = 100.0

        result = create_signal_dict('AAPL', 'US', indicators, signal, price, df)

        assert result['price'] == 100.0

    @patch('services.scheduler.get_company_info')
    def test_includes_summary_and_reasons(self, mock_get_info):
        mock_get_info.return_value = {"name": "AAPL", "logo": "", "sector": "", "industry": "", "exchange": "", "country": "", "marketCap": None}

        df = self._create_sample_df()
        indicators = {'rsi': 30, 'ema20': 100, 'ema50': 95, 'macd': 0.5, 'atr': 2, 'avg_volume': 1000000}
        signal = {'signal_type': 'BUY', 'trend': 'BULLISH', 'explanation': 'RSI oversold', 'summary': 'Oversold conditions', 'reasons': ['RSI below 30', 'EMA bullish']}
        price = 100.0

        result = create_signal_dict('AAPL', 'US', indicators, signal, price, df)

        assert result['summary'] == 'Oversold conditions'
        assert 'RSI below 30' in result['reasons']
        assert 'EMA bullish' in result['reasons']

    @patch('services.scheduler.get_company_info')
    def test_calculates_volume_relative(self, mock_get_info):
        mock_get_info.return_value = {"name": "AAPL", "logo": "", "sector": "", "industry": "", "exchange": "", "country": "", "marketCap": None}

        df = pd.DataFrame({
            'close': [100] * 10,
            'volume': [2000000] * 10
        })
        indicators = {'rsi': 50, 'ema20': 110, 'ema50': 105, 'macd': 0, 'atr': 1, 'avg_volume': 1000000}
        signal = {'signal_type': 'HOLD', 'trend': 'LATERAL', 'explanation': '', 'reasons': []}
        price = 100.0

        result = create_signal_dict('AAPL', 'US', indicators, signal, price, df)

        assert result['volumeRelative'] == 2.0

    @patch('services.scheduler.get_company_info')
    def test_cleans_nan_values_in_output(self, mock_get_info):
        mock_get_info.return_value = {"name": "AAPL", "logo": "", "sector": "", "industry": "", "exchange": "", "country": "", "marketCap": None}

        df = self._create_sample_df()
        indicators = {'rsi': float('nan'), 'ema20': float('inf'), 'ema50': 105, 'macd': float('nan'), 'atr': float('nan'), 'avg_volume': 1000000}
        signal = {'signal_type': 'HOLD', 'trend': 'LATERAL', 'explanation': '', 'reasons': []}
        price = 100.0

        result = create_signal_dict('AAPL', 'US', indicators, signal, price, df)

        assert result['rsi'] == 0.0
        assert result['ema20'] == 0.0
        assert result['macd'] == 0.0
        assert result['atr'] == 0.0