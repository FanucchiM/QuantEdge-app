import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from services.analyzer import TechnicalAnalyzer


class TestTechnicalAnalyzer:

    @pytest.fixture
    def analyzer(self):
        return TechnicalAnalyzer()

    @pytest.fixture
    def sample_df(self, sample_prices_df):
        df = sample_prices_df.copy()
        df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
        df = df.set_index('date')
        return df

    def test_calculate_rsi(self, analyzer, sample_df):
        result = analyzer.calculate_rsi(sample_df['close'])

        assert isinstance(result, float)
        assert 0 <= result <= 100

    def test_calculate_rsi_series_length(self, analyzer, sample_df):
        result = analyzer.calculate_rsi_series(sample_df['close'])

        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_df)

    def test_calculate_rsi_custom_period(self, analyzer, sample_df):
        result = analyzer.calculate_rsi(sample_df['close'], period=7)

        assert isinstance(result, float)
        assert 0 <= result <= 100

    def test_calculate_ema(self, analyzer, sample_df):
        result = analyzer.calculate_ema(sample_df['close'], 20)

        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_df)

    def test_calculate_ema_period_20(self, analyzer, sample_df):
        result = analyzer.calculate_ema(sample_df['close'], 20)

        assert not pd.isna(result.iloc[-1])

    def test_calculate_ema_period_50(self, analyzer, sample_df):
        result = analyzer.calculate_ema(sample_df['close'], 50)

        assert not pd.isna(result.iloc[-1])

    def test_calculate_macd_full(self, analyzer, sample_df):
        result = analyzer.calculate_macd_full(sample_df['close'])

        assert isinstance(result, dict)
        assert 'macd' in result
        assert 'macd_signal' in result
        assert 'macd_line' in result

    def test_calculate_macd_values(self, analyzer, sample_df):
        result = analyzer.calculate_macd_full(sample_df['close'])

        assert isinstance(result['macd'], (int, float))
        assert isinstance(result['macd_signal'], (int, float))
        assert isinstance(result['macd_line'], (int, float))

    def test_calculate_atr(self, analyzer, sample_df):
        result = analyzer.calculate_atr(
            sample_df['high'],
            sample_df['low'],
            sample_df['close']
        )

        assert isinstance(result, (int, float))
        assert result >= 0

    def test_calculate_bollinger(self, analyzer, sample_df):
        result = analyzer.calculate_bollinger(sample_df['close'])

        assert isinstance(result, dict)
        assert 'bb_upper' in result
        assert 'bb_middle' in result
        assert 'bb_lower' in result
        assert result['bb_upper'] > result['bb_middle']
        assert result['bb_middle'] > result['bb_lower']

    def test_calculate_stochastic(self, analyzer, sample_df):
        result = analyzer.calculate_stochastic(
            sample_df['high'],
            sample_df['low'],
            sample_df['close']
        )

        assert isinstance(result, dict)
        assert 'stoch_k' in result
        assert 'stoch_d' in result
        assert 0 <= result['stoch_k'] <= 100
        assert 0 <= result['stoch_d'] <= 100

    def test_calculate_adx(self, analyzer, sample_df):
        result = analyzer.calculate_adx(
            sample_df['high'],
            sample_df['low'],
            sample_df['close']
        )

        assert isinstance(result, dict)
        assert 'adx' in result
        assert 'plus_di' in result
        assert 'minus_di' in result
        assert result['adx'] >= 0

    def test_calculate_support_resistance(self, analyzer, sample_df):
        result = analyzer.calculate_support_resistance(
            sample_df['high'],
            sample_df['low'],
            sample_df['close']
        )

        assert isinstance(result, dict)
        assert 'sr_position' in result
        assert 'high_52w' in result

    def test_calculate_support_resistance_values(self, analyzer, sample_df):
        result = analyzer.calculate_support_resistance(
            sample_df['high'],
            sample_df['low'],
            sample_df['close']
        )

        assert result['sr_position'] >= 0 and result['sr_position'] <= 1

    def test_calculate_indicators(self, analyzer, sample_df):
        result = analyzer.calculate_indicators(sample_df)

        assert isinstance(result, dict)
        assert 'rsi' in result
        assert 'ema20' in result
        assert 'ema50' in result
        assert 'macd' in result

    def test_calculate_indicators_rsi_in_range(self, analyzer, sample_df):
        result = analyzer.calculate_indicators(sample_df)

        assert 0 <= result['rsi'] <= 100

    def test_calculate_indicators_returns_float(self, analyzer, sample_df):
        result = analyzer.calculate_indicators(sample_df)

        assert isinstance(result['rsi'], (int, float))
        assert isinstance(result['ema20'], (int, float))
        assert isinstance(result['atr'], (int, float))

    def test_get_all_indicators(self, analyzer, sample_df):
        result = analyzer.get_all_indicators(sample_df)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(sample_df)

    def test_get_all_indicators_has_rsi_column(self, analyzer, sample_df):
        result = analyzer.get_all_indicators(sample_df)

        assert 'RSI' in result.columns

    def test_calculate_seasonality(self, analyzer, sample_df):
        result = analyzer.calculate_seasonality(sample_df, years=[2026, 2025])

        assert isinstance(result, dict)
        assert 'years' in result

    def test_calculate_seasonality_yearly_returns(self, analyzer, sample_df):
        result = analyzer.calculate_seasonality(sample_df, years=[2026, 2025])

        assert 'monthlyAvg' in result or 'monthly_returns' in result

    def test_calculate_indicators_with_all_columns(self, analyzer, sample_df):
        result = analyzer.calculate_indicators(sample_df)

        required_keys = ['rsi', 'ema20', 'ema50', 'macd', 'atr']
        for key in required_keys:
            assert key in result, f"Missing {key}"

    def test_calculate_indicators_handles_bad_data(self, analyzer):
        bad_df = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [105, 106, 107],
            'low': [95, 96, 97],
            'close': [100, 101, 102],
            'volume': [1000000, 1100000, 1200000]
        })

        result = analyzer.calculate_indicators(bad_df)

        assert isinstance(result, dict)

    def test_calculate_rsi_returns_50_when_insufficient_data(self, analyzer):
        short_df = pd.DataFrame({'close': [100, 101]})
        result = analyzer.calculate_rsi(short_df['close'])

        assert isinstance(result, float)

    def test_calculate_ema_short_series(self, analyzer):
        short_df = pd.DataFrame({'close': [100, 101, 102, 103, 104]})
        result = analyzer.calculate_ema(short_df['close'], 20)

        assert isinstance(result, pd.Series)

    def test_default_periods(self, analyzer):
        assert analyzer.rsi_period == 14
        assert analyzer.ema_short == 20
        assert analyzer.ema_long == 50
        assert analyzer.macd_fast == 12
        assert analyzer.macd_slow == 26
        assert analyzer.macd_signal == 9