import pandas as pd
import numpy as np
import math

from config import (
    AVG_VOLUME_PERIOD,
    INDICATOR_RSI_PERIOD,
    INDICATOR_EMA_SHORT,
    INDICATOR_EMA_LONG,
    INDICATOR_MACD_FAST,
    INDICATOR_MACD_SLOW,
    INDICATOR_MACD_SIGNAL,
    INDICATOR_ATR_PERIOD,
    DAYS_FOR_52W_HIGH,
)

import logging
logger = logging.getLogger(__name__)


class TechnicalAnalyzer:
    def __init__(self):
        # Todos los períodos vienen de config.py / stock-config.json
        self.rsi_period  = INDICATOR_RSI_PERIOD
        self.ema_short   = INDICATOR_EMA_SHORT
        self.ema_long    = INDICATOR_EMA_LONG
        self.macd_fast   = INDICATOR_MACD_FAST
        self.macd_slow   = INDICATOR_MACD_SLOW
        self.macd_signal = INDICATOR_MACD_SIGNAL
        self.atr_period  = INDICATOR_ATR_PERIOD
        self.bb_period   = 20
        self.bb_std      = 2
        self.stoch_k     = 14
        self.stoch_d     = 3
        self.adx_period  = 14
        self.days_52w    = DAYS_FOR_52W_HIGH

    # ------------------------------------------------------------------
    # RSI — escalar (último valor)
    # ------------------------------------------------------------------
    def calculate_rsi(self, prices: pd.Series, period: int = None) -> float:
        period = period or self.rsi_period
        delta    = prices.diff()
        gain     = delta.where(delta > 0, 0)
        loss     = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()
        rs  = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        val = rsi.iloc[-1]
        return float(val) if not pd.isna(val) else 50.0

    # ------------------------------------------------------------------
    # RSI — Serie completa (para gráfico histórico)
    # ------------------------------------------------------------------
    def calculate_rsi_series(self, prices: pd.Series, period: int = None) -> pd.Series:
        period = period or self.rsi_period
        delta    = prices.diff()
        gain     = delta.where(delta > 0, 0)
        loss     = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()
        rs  = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    # ------------------------------------------------------------------
    # EMA
    # ------------------------------------------------------------------
    def calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        return prices.ewm(span=period, adjust=False).mean()

    # ------------------------------------------------------------------
    # MACD completo
    # ------------------------------------------------------------------
    def calculate_macd_full(self, prices: pd.Series) -> dict:
        ema_fast    = prices.ewm(span=self.macd_fast,   adjust=False).mean()
        ema_slow    = prices.ewm(span=self.macd_slow,   adjust=False).mean()
        macd_line   = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.macd_signal, adjust=False).mean()
        histogram   = macd_line - signal_line

        if len(histogram) >= 2:
            return {
                "macd":             float(histogram.iloc[-1]),
                "macd_line":        float(macd_line.iloc[-1]),
                "macd_signal":      float(signal_line.iloc[-1]),
                "macd_prev":        float(histogram.iloc[-2]),
                "macd_line_prev":   float(macd_line.iloc[-2]),
                "macd_signal_prev": float(signal_line.iloc[-2]),
            }
        val = float(histogram.iloc[-1]) if len(histogram) > 0 else 0.0
        return {
            "macd": val, "macd_line": 0.0, "macd_signal": 0.0,
            "macd_prev": 0.0, "macd_line_prev": 0.0, "macd_signal_prev": 0.0,
        }

    # ------------------------------------------------------------------
    # ATR
    # ------------------------------------------------------------------
    def calculate_atr(self, high: pd.Series, low: pd.Series,
                      close: pd.Series, period: int = None) -> float:
        period = period or self.atr_period
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low  - close.shift())
        tr  = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        val = atr.iloc[-1]
        return float(val) if not pd.isna(val) else 0.0

    # ------------------------------------------------------------------
    # Bollinger Bands
    # ------------------------------------------------------------------
    def calculate_bollinger(self, prices: pd.Series) -> dict:
        sma   = prices.rolling(window=self.bb_period).mean()
        std   = prices.rolling(window=self.bb_period).std()
        upper = sma + self.bb_std * std
        lower = sma - self.bb_std * std

        last_price  = float(prices.iloc[-1])
        last_upper  = float(upper.iloc[-1])
        last_lower  = float(lower.iloc[-1])
        last_middle = float(sma.iloc[-1])

        band_width  = last_upper - last_lower
        bb_position = (last_price - last_lower) / band_width if band_width > 0 else 0.5
        bb_width    = band_width / last_middle if last_middle > 0 else 0.0

        return {
            "bb_upper":    round(last_upper, 4),
            "bb_middle":   round(last_middle, 4),
            "bb_lower":    round(last_lower, 4),
            "bb_position": round(min(max(bb_position, 0.0), 1.0), 4),
            "bb_width":    round(bb_width, 4),
        }

    # ------------------------------------------------------------------
    # Stochastic %K y %D
    # ------------------------------------------------------------------
    def calculate_stochastic(self, high: pd.Series, low: pd.Series,
                              close: pd.Series) -> dict:
        lowest_low   = low.rolling(window=self.stoch_k).min()
        highest_high = high.rolling(window=self.stoch_k).max()
        stoch_range  = highest_high - lowest_low

        k = ((close - lowest_low) / stoch_range * 100).where(stoch_range > 0, 50)
        d = k.rolling(window=self.stoch_d).mean()

        last_k = float(k.iloc[-1]) if not pd.isna(k.iloc[-1]) else 50.0
        last_d = float(d.iloc[-1]) if not pd.isna(d.iloc[-1]) else 50.0
        prev_k = float(k.iloc[-2]) if len(k) >= 2 and not pd.isna(k.iloc[-2]) else last_k
        prev_d = float(d.iloc[-2]) if len(d) >= 2 and not pd.isna(d.iloc[-2]) else last_d

        return {
            "stoch_k":      round(last_k, 2),
            "stoch_d":      round(last_d, 2),
            "stoch_k_prev": round(prev_k, 2),
            "stoch_d_prev": round(prev_d, 2),
        }

    # ------------------------------------------------------------------
    # ADX — fuerza de tendencia
    # ------------------------------------------------------------------
    def calculate_adx(self, high: pd.Series, low: pd.Series,
                      close: pd.Series) -> dict:
        period    = self.adx_period
        high_diff = high.diff()
        low_diff  = -low.diff()

        plus_dm  = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0.0)
        minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0.0)

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low  - close.shift())
        tr  = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        atr14    = tr.ewm(span=period, adjust=False).mean()
        plus_di  = 100 * plus_dm.ewm(span=period, adjust=False).mean() / atr14
        minus_di = 100 * minus_dm.ewm(span=period, adjust=False).mean() / atr14

        dx_num = abs(plus_di - minus_di)
        dx_den = plus_di + minus_di
        dx     = (dx_num / dx_den * 100).where(dx_den > 0, 0)
        adx    = dx.ewm(span=period, adjust=False).mean()

        return {
            "adx":      round(float(adx.iloc[-1])      if not pd.isna(adx.iloc[-1])      else 0.0, 2),
            "plus_di":  round(float(plus_di.iloc[-1])  if not pd.isna(plus_di.iloc[-1])  else 0.0, 2),
            "minus_di": round(float(minus_di.iloc[-1]) if not pd.isna(minus_di.iloc[-1]) else 0.0, 2),
        }

    # ------------------------------------------------------------------
    # Soporte / Resistencia — posición vs rango 52 semanas
    # ------------------------------------------------------------------
    def calculate_support_resistance(self, high: pd.Series, low: pd.Series,
                                     close: pd.Series) -> dict:
        days    = min(self.days_52w, len(close))
        h52     = float(high.tail(days).max())
        l52     = float(low.tail(days).min())
        last    = float(close.iloc[-1])
        rng     = h52 - l52

        sr_position   = (last - l52) / rng if rng > 0 else 0.5
        pct_from_high = (h52 - last) / h52  if h52  > 0 else 0.0
        pct_from_low  = (last - l52) / last  if last > 0 else 0.0

        return {
            "high_52w":      round(h52, 4),
            "low_52w":       round(l52, 4),
            "sr_position":   round(min(max(sr_position, 0.0), 1.0), 4),
            "pct_from_high": round(pct_from_high, 4),
            "pct_from_low":  round(pct_from_low, 4),
        }

    # ------------------------------------------------------------------
    # calculate_indicators — método principal
    # ------------------------------------------------------------------
    def calculate_indicators(self, df: pd.DataFrame) -> dict:
        close = df['close']
        high  = df['high']
        low   = df['low']

        try:
            rsi = self.calculate_rsi(close)
        except Exception as e:
            logger.warning(f"RSI failed: {e}")
            rsi = 50.0

        try:
            ema20 = float(self.calculate_ema(close, self.ema_short).iloc[-1])
        except Exception:
            ema20 = float(close.iloc[-1])

        try:
            ema50 = float(self.calculate_ema(close, self.ema_long).iloc[-1])
        except Exception:
            ema50 = float(close.iloc[-1])

        try:
            macd_data = self.calculate_macd_full(close)
        except Exception as e:
            logger.warning(f"MACD failed: {e}")
            macd_data = {
                "macd": 0.0, "macd_line": 0.0, "macd_signal": 0.0,
                "macd_prev": 0.0, "macd_line_prev": 0.0, "macd_signal_prev": 0.0,
            }

        try:
            atr = self.calculate_atr(high, low, close)
        except Exception:
            atr = 0.0

        try:
            avg_volume = float(df['volume'].tail(AVG_VOLUME_PERIOD).mean()) \
                         if 'volume' in df.columns else 0.0
        except Exception:
            avg_volume = 0.0

        try:
            bb = self.calculate_bollinger(close)
        except Exception as e:
            logger.warning(f"Bollinger failed: {e}")
            bb = {"bb_upper": 0.0, "bb_middle": 0.0, "bb_lower": 0.0,
                  "bb_position": 0.5, "bb_width": 0.0}

        try:
            stoch = self.calculate_stochastic(high, low, close)
        except Exception as e:
            logger.warning(f"Stochastic failed: {e}")
            stoch = {"stoch_k": 50.0, "stoch_d": 50.0,
                     "stoch_k_prev": 50.0, "stoch_d_prev": 50.0}

        try:
            adx_data = self.calculate_adx(high, low, close)
        except Exception as e:
            logger.warning(f"ADX failed: {e}")
            adx_data = {"adx": 25.0, "plus_di": 0.0, "minus_di": 0.0}

        try:
            sr = self.calculate_support_resistance(high, low, close)
        except Exception as e:
            logger.warning(f"S/R failed: {e}")
            sr = {"high_52w": 0.0, "low_52w": 0.0, "sr_position": 0.5,
                  "pct_from_high": 0.0, "pct_from_low": 0.0}

        return {
            "rsi":              rsi,
            "ema20":            ema20,
            "ema50":            ema50,
            "macd":             macd_data["macd"],
            "macd_line":        macd_data["macd_line"],
            "macd_signal":      macd_data["macd_signal"],
            "macd_prev":        macd_data["macd_prev"],
            "macd_line_prev":   macd_data["macd_line_prev"],
            "macd_signal_prev": macd_data["macd_signal_prev"],
            "atr":              atr,
            "avg_volume":       avg_volume,
            **bb,
            **stoch,
            **adx_data,
            **sr,
        }

    # ------------------------------------------------------------------
    # get_all_indicators — para el gráfico histórico
    # ------------------------------------------------------------------
    def get_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df['RSI']         = self.calculate_rsi_series(df['close'])
        df['EMA20']       = self.calculate_ema(df['close'], self.ema_short)
        df['EMA50']       = self.calculate_ema(df['close'], self.ema_long)

        ema_fast          = df['close'].ewm(span=self.macd_fast,   adjust=False).mean()
        ema_slow          = df['close'].ewm(span=self.macd_slow,   adjust=False).mean()
        df['MACD']        = ema_fast - ema_slow
        df['MACD_Signal'] = df['MACD'].ewm(span=self.macd_signal, adjust=False).mean()
        df['MACD_Hist']   = df['MACD'] - df['MACD_Signal']

        tr1               = df['high'] - df['low']
        tr2               = abs(df['high'] - df['close'].shift())
        tr3               = abs(df['low']  - df['close'].shift())
        tr                = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['ATR']         = tr.rolling(window=self.atr_period).mean()

        sma               = df['close'].rolling(window=self.bb_period).mean()
        std               = df['close'].rolling(window=self.bb_period).std()
        df['BB_Upper']    = sma + self.bb_std * std
        df['BB_Middle']   = sma
        df['BB_Lower']    = sma - self.bb_std * std

        lowest_low        = df['low'].rolling(window=self.stoch_k).min()
        highest_high      = df['high'].rolling(window=self.stoch_k).max()
        stoch_range       = highest_high - lowest_low
        df['Stoch_K']     = ((df['close'] - lowest_low) / stoch_range * 100).where(stoch_range > 0, 50)
        df['Stoch_D']     = df['Stoch_K'].rolling(window=self.stoch_d).mean()

        return df

    def calculate_seasonality(self, df: pd.DataFrame, years: list = None) -> dict:
        """
        Calculate historical seasonal performance by month.
        years: list of years to include (e.g: [2026, 2025, 2024])
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            if years is None:
                years = [2026, 2025, 2024]

            if 'close' not in df.columns:
                return {"error": "No price data available"}

            # Asegurar que el índice tiene fechas
            if not isinstance(df.index, pd.DatetimeIndex):
                if 'date' in df.columns:
                    df = df.set_index('date')
                else:
                    return {"error": "No date index available"}

            df = df.sort_index()
            
            # DEBUG: ver datos
            logger.info(f"Seasonality: df shape={df.shape}, index type={type(df.index)}")
            logger.info(f"Seasonality: years={years}")

            months_es = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
            current_year = 2026
            current_month = 4  # Abril

            yearly_returns = {}
            
            for year in years:
                year_data = df[df.index.year == year]
                
                logger.info(f"Seasonality: year {year} has {len(year_data)} rows")
                
                if year_data.empty:
                    continue

                monthly_returns = []
                months_in_year = list(range(1, 13))
                
                if year == current_year:
                    months_in_year = list(range(1, current_month + 1))

                for month in months_in_year:
                    month_data = year_data[year_data.index.month == month]
                    
                    if month_data.empty:
                        monthly_returns.append(0.0)
                        continue

                    prices = month_data['close'].dropna()
                    if len(prices) < 2:
                        monthly_returns.append(0.0)
                        continue

                    try:
                        first_price = float(prices.iloc[0])
                        last_price = float(prices.iloc[-1])
                        monthly_return = ((last_price - first_price) / first_price) * 100
                        if math.isnan(monthly_return) or math.isinf(monthly_return):
                            monthly_returns.append(0.0)
                        else:
                            monthly_returns.append(round(monthly_return, 2))
                    except Exception as e:
                        logger.info(f"  Month {month}: error calculating: {e}")
                        monthly_returns.append(0.0)

                logger.info(f"Seasonality: year {year} monthly_returns={monthly_returns}")
                yearly_returns[str(year)] = monthly_returns

        except Exception as e:
            logger.error(f"Error calculating seasonality: {e}")
            return {"error": str(e)}
        
        avg_returns = []
        max_years = max(len(yearly_returns.get(str(y), [])) for y in years)
        
        for i in range(max_years):
            values = []
            for year in years:
                year_str = str(year)
                if year_str in yearly_returns and i < len(yearly_returns[year_str]):
                    val = yearly_returns[year_str][i]
                    if val is not None:
                        values.append(val)
            avg_returns.append(round(sum(values) / len(values), 2) if values else 0.0)

        return {
            "years": [str(y) for y in years],
            "yearlyReturns": yearly_returns,
            "monthlyAvg": avg_returns,
            "months": months_es[:max_years],
            "bestMonth": months_es[avg_returns.index(max(avg_returns))] if avg_returns else None,
            "worstMonth": months_es[avg_returns.index(min(avg_returns))] if avg_returns else None,
            "avgReturn": round(sum(avg_returns) / len(avg_returns), 2) if avg_returns else 0
        }
