import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path


@pytest.fixture
def sample_prices_df():
    dates = [datetime(2026, 4, 25) - timedelta(days=i) for i in range(60, 0, -1)]
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(60) * 2)

    return pd.DataFrame({
        'date': dates,
        'open': prices - np.random.uniform(0.5, 1.5, 60),
        'high': prices + np.random.uniform(0.5, 2, 60),
        'low': prices - np.random.uniform(0.5, 2, 60),
        'close': prices,
        'volume': np.random.randint(1000000, 5000000, 60)
    })


@pytest.fixture
def sample_prices_csv():
    fixture_path = Path(__file__).parent / 'fixtures' / 'sample_prices.csv'
    return pd.read_csv(fixture_path)


@pytest.fixture
def sample_metadata():
    return {
        "AAPL": {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "logo": "https://example.com/apple.png",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "exchange": "NASDAQ",
            "country": "US",
            "marketCap": 3725926
        },
        "TM": {
            "symbol": "TM",
            "name": "Toyota Motor Corporation",
            "logo": "https://example.com/toyota.png",
            "sector": "Consumer Discretionary",
            "industry": "Automobiles",
            "exchange": "NYSE",
            "country": "JP",
            "marketCap": 42019651
        }
    }


@pytest.fixture
def mock_indicators():
    return {
        'rsi': 45.0,
        'ema20': 105.5,
        'ema50': 102.3,
        'macd': 1.2,
        'macd_signal': 0.8,
        'macd_hist': 0.4,
        'atr': 3.5,
        'adx': 28.0,
        'plus_di': 32.0,
        'minus_di': 25.0,
        'bb_upper': 115.0,
        'bb_middle': 105.0,
        'bb_lower': 95.0,
        'stoch_k': 55.0,
        'stoch_d': 50.0,
        'avg_volume': 2500000,
        'volume': 2800000
    }


@pytest.fixture
def bull_market_indicators():
    return {
        'rsi': 62.0,
        'ema20': 150.0,
        'ema50': 145.0,
        'macd': 5.0,
        'macd_signal': 3.0,
        'macd_hist': 2.0,
        'atr': 2.0,
        'adx': 35.0,
        'plus_di': 40.0,
        'minus_di': 20.0,
        'bb_upper': 160.0,
        'bb_middle': 150.0,
        'bb_lower': 140.0,
        'stoch_k': 75.0,
        'stoch_d': 70.0,
        'avg_volume': 2500000,
        'volume': 3000000
    }


@pytest.fixture
def bear_market_indicators():
    return {
        'rsi': 28.0,
        'ema20': 95.0,
        'ema50': 105.0,
        'macd': -3.0,
        'macd_signal': -1.5,
        'macd_hist': -1.5,
        'atr': 4.0,
        'adx': 32.0,
        'plus_di': 20.0,
        'minus_di': 40.0,
        'bb_upper': 105.0,
        'bb_middle': 95.0,
        'bb_lower': 85.0,
        'stoch_k': 20.0,
        'stoch_d': 25.0,
        'avg_volume': 2500000,
        'volume': 3500000
    }


@pytest.fixture
def sample_prices_bull():
    np.random.seed(123)
    dates = [datetime(2026, 4, 25) - timedelta(days=i) for i in range(60, 0, -1)]
    prices = 130 + np.cumsum(np.random.randn(60) * 1)

    return pd.DataFrame({
        'date': dates,
        'open': prices - np.random.uniform(0.3, 0.8, 60),
        'high': prices + np.random.uniform(0.3, 1, 60),
        'low': prices - np.random.uniform(0.3, 1, 60),
        'close': prices,
        'volume': np.random.randint(2000000, 4000000, 60)
    })


@pytest.fixture
def sample_prices_bear():
    np.random.seed(456)
    dates = [datetime(2026, 4, 25) - timedelta(days=i) for i in range(60, 0, -1)]
    prices = 90 - np.cumsum(np.random.randn(60) * 1.5)

    return pd.DataFrame({
        'date': dates,
        'open': prices - np.random.uniform(0.3, 0.8, 60),
        'high': prices + np.random.uniform(0.3, 1, 60),
        'low': prices - np.random.uniform(0.3, 1, 60),
        'close': prices,
        'volume': np.random.randint(3000000, 5000000, 60)
    })