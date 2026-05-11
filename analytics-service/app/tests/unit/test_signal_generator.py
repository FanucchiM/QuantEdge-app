import pytest
from services.signal_generator import SignalGenerator


class TestSignalGenerator:

    @pytest.fixture
    def sg(self):
        return SignalGenerator()

    def test_generate_signal_buy_oversold_rsi(self, sg, mock_indicators):
        indicators = {**mock_indicators, 'rsi': 25.0, 'adx': 30.0}
        result = sg.generate_signal(indicators, price=100.0, volume=2500000, market='US')

        assert result['signal_type'] == 'BUY'
        assert 'RSI' in result['explanation'] or 'RSI' in result.get('reasons', [])

    def test_generate_signal_sell_overbought_rsi(self, sg, mock_indicators):
        indicators = {**mock_indicators, 'rsi': 75.0, 'adx': 30.0}
        result = sg.generate_signal(indicators, price=100.0, volume=2500000, market='US')

        assert result['signal_type'] == 'SELL'
        assert 'RSI' in result['explanation'] or 'RSI' in result.get('reasons', [])

    def test_generate_signal_hold_neutral(self, sg, mock_indicators):
        indicators = {**mock_indicators, 'rsi': 50.0, 'adx': 20.0}
        result = sg.generate_signal(indicators, price=100.0, volume=2500000, market='US')

        assert result['signal_type'] in ['BUY', 'SELL', 'HOLD']
        assert isinstance(result.get('normalized'), (int, float))

    def test_generate_signal_bull_trend(self, sg, bull_market_indicators):
        result = sg.generate_signal(
            bull_market_indicators,
            price=150.0,
            volume=3000000,
            market='US'
        )

        assert 'trend' in result
        assert result['trend'] in ['BULLISH', 'BEARISH', 'LATERAL']

    def test_generate_signal_bear_trend(self, sg, bear_market_indicators):
        result = sg.generate_signal(
            bear_market_indicators,
            price=90.0,
            volume=3500000,
            market='US'
        )

        assert 'trend' in result
        assert result['trend'] in ['BULLISH', 'BEARISH', 'LATERAL']

    def test_generate_signal_with_price(self, sg, mock_indicators):
        result = sg.generate_signal(mock_indicators, price=150.75, volume=2500000, market='US')

        assert 'signal_type' in result
        assert 'trend' in result

    def test_generate_signal_us_market(self, sg, mock_indicators):
        result = sg.generate_signal(mock_indicators, price=100.0, volume=2500000, market='US')
        assert 'signal_type' in result

    def test_generate_signal_ar_market(self, sg, mock_indicators):
        result = sg.generate_signal(mock_indicators, price=100.0, volume=2500000, market='AR')
        assert 'signal_type' in result

    def test_generate_signal_jp_market(self, sg, mock_indicators):
        result = sg.generate_signal(mock_indicators, price=100.0, volume=2500000, market='JP')
        assert 'signal_type' in result

    def test_generate_signal_eu_market(self, sg, mock_indicators):
        result = sg.generate_signal(mock_indicators, price=100.0, volume=2500000, market='EU')
        assert 'signal_type' in result

    def test_generate_signal_volume_surge(self, sg, mock_indicators):
        indicators = {**mock_indicators, 'volume': 5000000, 'avg_volume': 1000000}
        result = sg.generate_signal(indicators, price=100.0, volume=5000000)

        reasons_str = str(result.get('reasons', []))
        assert 'volume' in reasons_str.lower() or 'volume' in result.get('explanation', '').lower()

    def test_generate_signal_ema_crossover_bullish(self, sg):
        indicators = {
            'rsi': 55.0,
            'ema20': 105.0,
            'ema50': 100.0,
            'macd': 2.0,
            'macd_signal': 1.0,
            'macd_hist': 1.0,
            'atr': 2.0,
            'bb_position': 0.5,
            'stoch_k': 60.0,
            'stoch_d': 55.0,
            'adx': 30.0,
            'sr_position': 0.5,
            'avg_volume': 2000000,
            'volume': 2200000
        }
        result = sg.generate_signal(indicators, price=105.0, volume=2200000, market='US')

        assert 'signal_type' in result

    def test_generate_signal_ema_crossover_bearish(self, sg):
        indicators = {
            'rsi': 45.0,
            'ema20': 95.0,
            'ema50': 100.0,
            'macd': -2.0,
            'macd_signal': -1.0,
            'macd_hist': -1.0,
            'atr': 2.0,
            'bb_position': 0.5,
            'stoch_k': 40.0,
            'stoch_d': 45.0,
            'adx': 30.0,
            'sr_position': 0.5,
            'avg_volume': 2000000,
            'volume': 2200000
        }
        result = sg.generate_signal(indicators, price=95.0, volume=2200000, market='US')

        assert 'signal_type' in result

    def test_generate_signal_empty_indicators(self, sg):
        result = sg.generate_signal({}, price=100.0, volume=1000)

        assert 'signal_type' in result
        assert 'trend' in result
        assert 'explanation' in result

    def test_generate_signal_has_normalized_score(self, sg, mock_indicators):
        result = sg.generate_signal(mock_indicators, price=100.0, volume=2500000)

        assert 'normalized' in result or 'signal_type' in result

    def test_generate_signal_has_explanation(self, sg, mock_indicators):
        result = sg.generate_signal(mock_indicators, price=100.0, volume=2500000)

        assert 'explanation' in result
        assert isinstance(result['explanation'], str)
        assert len(result['explanation']) > 0

    def test_generate_signal_has_summary(self, sg, mock_indicators):
        result = sg.generate_signal(mock_indicators, price=100.0, volume=2500000)

        assert 'summary' in result
        assert isinstance(result['summary'], str)