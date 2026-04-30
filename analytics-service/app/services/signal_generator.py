# -*- coding: utf-8 -*-
import httpx
import os
import logging
import math

from config import (
    SCORING_TREND_WEIGHT,
    SCORING_RSI_REVERSAL_WEIGHT,
    SCORING_MACD_WEIGHT,
    SCORING_MACD_CROSS_WEIGHT,
    SCORING_VOLUME_WEIGHT,
    SCORING_ATR_PENALTY,
    SCORING_EMA_PROXIMITY_PCT,
    SCORING_VOLUME_SURGE_MULTIPLIER,
    SCORING_ATR_VOLATILITY_PCT,
    SCORING_OVERSOLD,
    SCORING_OVERSOLD_MILD,
    SCORING_OVERBOUGHT,
    SCORING_OVERBOUGHT_MILD,
    API_BATCH_TIMEOUT,
)

logger = logging.getLogger(__name__)


def _safe_float(value):
    """Sanitiza valores NaN/Inf para JSON."""
    if value is None:
        return 0.0
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return 0.0
        return round(value, 6)
    try:
        return round(float(value), 6)
    except (ValueError, TypeError):
        return 0.0


# ------------------------------------------------------------------
# Thresholds por mercado — externalizables en stock-config.json
# Agregá en stock-config.json bajo "market_config": { "AR": {...}, ... }
# Si no están en el JSON, se usan estos defaults.
# ------------------------------------------------------------------
DEFAULT_MARKET_CONFIG = {
    "US": {
        "rsi_oversold":      30.0,   # RSI bajo = sobrevendido
        "rsi_oversold_mild": 40.0,
        "rsi_overbought":    70.0,   # RSI alto = sobrecomprado
        "rsi_overbought_mild": 60.0,
        "atr_high_pct":      0.03,   # ATR > 3% = alta volatilidad
        "adx_min":           20.0,   # ADX < 20 = sin tendencia
        "vol_high_mult":     1.5,    # volumen > 1.5x = confirma señal
        "vol_low_mult":      0.5,
        "lateral_pct":       0.005,  # EMA diferencia < 0.5% = lateral
        "sr_high":           0.85,   # cerca del máximo 52w
        "sr_low":            0.15,
        "buy_threshold":     0.30,   # normalized >= 0.30 → BUY
        "sell_threshold":    0.30,
    },
    "AR": {
        # Mercado argentino: más volátil por inflación
        # ATR y RSI tienen rangos más amplios
        "rsi_oversold":      35.0,
        "rsi_oversold_mild": 45.0,
        "rsi_overbought":    65.0,
        "rsi_overbought_mild": 55.0,
        "atr_high_pct":      0.05,   # 5% es normal en AR
        "adx_min":           25.0,   # necesita más fuerza de tendencia
        "vol_high_mult":     2.0,    # mercado chico, requiere más volumen
        "vol_low_mult":      0.5,
        "lateral_pct":       0.015,  # 1.5% - más permisivo por volatilidad
        "sr_high":           0.80,
        "sr_low":            0.20,
        "buy_threshold":     0.35,   # más exigente por volatilidad
        "sell_threshold":    0.35,
    },
    "EU": {
        "rsi_oversold":      30.0,
        "rsi_oversold_mild": 40.0,
        "rsi_overbought":    70.0,
        "rsi_overbought_mild": 60.0,
        "atr_high_pct":      0.025,  # mercados EU menos volátiles que US
        "adx_min":           20.0,
        "vol_high_mult":     1.5,
        "vol_low_mult":      0.5,
        "lateral_pct":       0.005,  # EMA diferencia < 0.5% = lateral
        "sr_high":           0.85,
        "sr_low":            0.15,
        "buy_threshold":     0.30,
        "sell_threshold":    0.30,
    },
    "JP": {
        "rsi_oversold":      30.0,
        "rsi_oversold_mild": 40.0,
        "rsi_overbought":    70.0,
        "rsi_overbought_mild": 60.0,
        "atr_high_pct":      0.02,   # mercado japonés: muy estable
        "adx_min":           20.0,
        "vol_high_mult":     1.5,
        "vol_low_mult":      0.5,
        "lateral_pct":       0.005,  # EMA diferencia < 0.5% = lateral
        "sr_high":           0.85,
        "sr_low":            0.15,
        "buy_threshold":     0.30,
        "sell_threshold":    0.30,
    },
}


class SignalGenerator:
    def __init__(self, market_config: dict = None):
        self.api_url   = os.getenv("API_URL", "http://localhost:8081")

        # Pesos desde config.py / stock-config.json
        self.trend_weight      = SCORING_TREND_WEIGHT
        self.rsi_reversal_weight = SCORING_RSI_REVERSAL_WEIGHT
        self.macd_weight       = SCORING_MACD_WEIGHT
        self.macd_cross_weight = SCORING_MACD_CROSS_WEIGHT
        self.volume_weight     = SCORING_VOLUME_WEIGHT
        self.atr_penalty       = SCORING_ATR_PENALTY

        # market_config puede venir del stock-config.json via el llamador
        # Si no se pasa, usa los defaults hardcodeados arriba
        self.market_config = market_config or DEFAULT_MARKET_CONFIG

    def _get_market_cfg(self, market: str) -> dict:
        """Devuelve la config del mercado, fallback a US si no existe."""
        return self.market_config.get(market.upper(), self.market_config.get("US", DEFAULT_MARKET_CONFIG["US"]))

    # ------------------------------------------------------------------
    # Método principal
    # ------------------------------------------------------------------
    def generate_signal(self, indicators: dict, price: float,
                        volume: float = 0, market: str = "US") -> dict:

        cfg = self._get_market_cfg(market)

        rsi              = indicators.get("rsi", 50)
        ema20            = indicators.get("ema20", price)
        ema50            = indicators.get("ema50", price)
        macd_line        = indicators.get("macd_line", 0)
        macd_signal_val  = indicators.get("macd_signal", 0)
        macd_line_prev   = indicators.get("macd_line_prev", 0)
        macd_signal_prev = indicators.get("macd_signal_prev", 0)
        macd_hist        = indicators.get("macd", 0)
        atr              = indicators.get("atr", 0)
        avg_volume       = indicators.get("avg_volume", 0)
        bb_position      = indicators.get("bb_position", 0.5)
        stoch_k          = indicators.get("stoch_k", 50)
        stoch_d          = indicators.get("stoch_d", 50)
        stoch_k_prev     = indicators.get("stoch_k_prev", 50)
        stoch_d_prev     = indicators.get("stoch_d_prev", 50)
        adx              = indicators.get("adx", 25)
        sr_position      = indicators.get("sr_position", 0.5)
        
        # Calcular volume_relative
        avg_volume = indicators.get("avg_volume", 0)
        volume_relative = round(volume / avg_volume, 2) if avg_volume > 0 else 1.0
        
        raw_score    = 0.0
        max_possible = 0.0
        reasons      = []

        # ── FILTRO: ADX bajo → HOLD inmediato ─────────────────────────
        if adx < cfg["adx_min"]:
            return {
                "signal_type": "HOLD",
                "trend":       "LATERAL",
                "explanation": (
                    f"HOLD: ADX {_safe_float(adx)} indicates no trend in market "
                    f"(minimum {cfg['adx_min']} for {market})."
                ),
                "summary":    self._safe_summary("HOLD", "LATERAL", rsi, adx, volume_relative),
                "reasons": [f"ADX {_safe_float(adx)} < {cfg['adx_min']} — no trend in market {market}"],
                "normalized": 0.0,
                "market":      market,
                "volume_relative": volume_relative,
            }

        # ── 1. TENDENCIA: EMA20 vs EMA50 ──────────────────────────────
        ema_diff_pct = abs(ema20 - ema50) / ema50 if ema50 > 0 else 0

        if ema_diff_pct < cfg["lateral_pct"]:
            trend = "LATERAL"
            reasons.append(f"EMA20 ≈ EMA50 — sideways market ({market})")
        else:
            max_possible += self.trend_weight
            if ema20 > ema50:
                trend = "BULLISH"
                raw_score += self.trend_weight
                reasons.append(f"EMA20 > EMA50 — bullish trend ({ema_diff_pct*100:.1f}%)")
            else:
                trend = "BEARISH"
                raw_score -= self.trend_weight
                reasons.append(f"EMA20 < EMA50 — bearish trend ({ema_diff_pct*100:.1f}%)")

        # Bonus ADX fuerte (> 40)
        if adx > 40:
            bonus = 0.5 if raw_score >= 0 else -0.5
            raw_score    += bonus
            max_possible += 0.5
            reasons.append(f"ADX {adx:.1f} — strong trend confirmed")
        else:
            reasons.append(f"ADX {adx:.1f} — moderate trend")

        # ── 2. RSI ─────────────────────────────────────────────────────
        max_possible += self.rsi_reversal_weight
        if rsi < cfg["rsi_oversold"]:
            raw_score += self.rsi_reversal_weight
            reasons.append(f"RSI {rsi:.0f} — severely oversold (< {cfg['rsi_oversold']}), possible reversal")
        elif rsi < cfg["rsi_oversold_mild"]:
            raw_score += self.rsi_reversal_weight * 0.4
            reasons.append(f"RSI {rsi:.0f} — oversold (< {cfg['rsi_oversold_mild']})")
        elif rsi > cfg["rsi_overbought"]:
            raw_score -= self.rsi_reversal_weight
            reasons.append(f"RSI {rsi:.0f} — severely overbought (> {cfg['rsi_overbought']}), possible correction")
        elif rsi > cfg["rsi_overbought_mild"]:
            raw_score -= self.rsi_reversal_weight * 0.4
            reasons.append(f"RSI {rsi:.0f} — overbought (> {cfg['rsi_overbought_mild']})")
        else:
            reasons.append(f"RSI {rsi:.0f} — neutral zone")

        # ── 3. MACD: cruce real ────────────────────────────────────────
        macd_cross_bull = (macd_line_prev <= macd_signal_prev) and (macd_line > macd_signal_val)
        macd_cross_bear = (macd_line_prev >= macd_signal_prev) and (macd_line < macd_signal_val)

        if macd_cross_bull:
            raw_score    += self.macd_cross_weight
            max_possible += self.macd_cross_weight
            reasons.append("MACD bullish crossover — line crossed above signal")
        elif macd_cross_bear:
            raw_score    -= self.macd_cross_weight
            max_possible += self.macd_cross_weight
            reasons.append("MACD bearish crossover — line crossed below signal")
        elif macd_hist > 0:
            raw_score    += self.macd_weight * 0.5
            max_possible += self.macd_weight
            reasons.append("MACD histogram positive")
        else:
            raw_score    -= self.macd_weight * 0.5
            max_possible += self.macd_weight
            reasons.append("MACD histogram negative")

        # ── 4. STOCHASTIC — peso ±1 ───────────────────────────────────
        stoch_cross_bull = (stoch_k_prev <= stoch_d_prev) and (stoch_k > stoch_d)
        stoch_cross_bear = (stoch_k_prev >= stoch_d_prev) and (stoch_k < stoch_d)

        max_possible += 1.0
        if stoch_k < 20:
            raw_score += 1.0
            reasons.append(f"Stoch %K {stoch_k:.0f} — severely oversold")
        elif stoch_k > 80:
            raw_score -= 1.0
            reasons.append(f"Stoch %K {stoch_k:.0f} — severely overbought")
        elif stoch_cross_bull and stoch_k < 50:
            raw_score += 0.75
            reasons.append(f"Stoch bullish crossover in low zone (%K {stoch_k:.0f})")
        elif stoch_cross_bear and stoch_k > 50:
            raw_score -= 0.75
            reasons.append(f"Stoch bearish crossover in high zone (%K {stoch_k:.0f})")
        else:
            reasons.append(f"Stoch %K {stoch_k:.0f} — neutral zone")

        # ── 5. BOLLINGER BANDS — confirmación ±0.5 ────────────────────
        max_possible += 0.5
        if bb_position < 0.20:
            raw_score += 0.5
            reasons.append(f"BB: price at lower band ({bb_position:.0%}) — oversold")
        elif bb_position > 0.80:
            raw_score -= 0.5
            reasons.append(f"BB: price at upper band ({bb_position:.0%}) — overbought")
        else:
            reasons.append(f"BB: price in middle zone ({bb_position:.0%})")

        # ── 6. SUPPORT / RESISTANCE — confirmación ±0.5 ──────────────
        max_possible += 0.5
        sr_pos = sr_position if sr_position is not None and not (isinstance(sr_position, float) and (math.isnan(sr_position) or math.isinf(sr_position))) else 0.5
        if sr_pos > cfg["sr_high"] and raw_score > 0:
            raw_score -= 0.5
            reasons.append(f"S/R: near 52w high ({sr_pos:.0%}) — resistance, caution on BUY")
        elif sr_pos < cfg["sr_low"] and raw_score < 0:
            raw_score += 0.5
            reasons.append(f"S/R: near 52w low ({sr_pos:.0%}) — support, caution on SELL")
        else:
            reasons.append(f"S/R: price in mid range ({sr_pos:.0%})")

        # ── 7. VOLUMEN ─────────────────────────────────────────────────
        vol_ratio = (volume / avg_volume) if avg_volume > 0 else 1.0

        if vol_ratio >= cfg["vol_high_mult"]:
            confirmation  = self.volume_weight if raw_score >= 0 else -self.volume_weight
            raw_score    += confirmation
            max_possible += self.volume_weight
            reasons.append(f"Volume {vol_ratio:.1f}x avg — confirms signal")
        elif vol_ratio <= cfg["vol_low_mult"]:
            raw_score *= 0.8
            reasons.append(f"Low volume ({vol_ratio:.1f}x) — lower confidence signal")
        else:
            reasons.append(f"Normal volume ({vol_ratio:.1f}x avg)")

        # ── 8. ATR — penalizar alta volatilidad ───────────────────────
        atr_val = atr if not (isinstance(atr, float) and (math.isnan(atr) or math.isinf(atr))) else 0.0
        price_val = price if price > 0 else 0.0
        atr_pct = (atr_val / price_val) if price_val > 0 else 0
        
        if atr_pct > cfg["atr_high_pct"]:
            raw_score *= (1.0 - self.atr_penalty / 10)
            reasons.append(
                f"ATR {atr_pct*100:.1f}% > {cfg['atr_high_pct']*100:.1f}% "
                f"— high volatility for {market}, score reduced"
            )
        else:
            if atr_val > 0:
                reasons.append(f"ATR {atr_pct*100:.1f}% — normal volatility for {market}")
            else:
                reasons.append("ATR: data unavailable")

        # ── 9. NORMALIZAR -1/+1 ───────────────────────────────────────
        normalized = max(-1.0, min(1.0, raw_score / max_possible)) if max_possible > 0 else 0.0

        # ── 10. SEÑAL FINAL ───────────────────────────────────────────
        buy_thr  = cfg["buy_threshold"]
        sell_thr = cfg["sell_threshold"]

        if trend == "LATERAL":
            signal_type = "HOLD"
        elif normalized >= buy_thr:
            signal_type = "BUY"
        elif normalized <= -sell_thr:
            signal_type = "SELL"
        else:
            signal_type = "HOLD"

        # Mantener el normalized real para HOLD (no resetear a 0)
        if signal_type == "HOLD":
            normalized = max(-buy_thr + 0.01, min(buy_thr - 0.01, normalized))
        else:
            normalized = round((normalized + 1) / 2 * 100, 1)

        # Sanitizar reasons para evitar NaN en JSON
        sanitized_reasons = []
        for r in reasons:
            if isinstance(r, str):
                sanitized_reasons.append(r)
            else:
                sanitized_reasons.append(str(r))

        return {
            "signal_type": signal_type,
            "trend":       trend,
            "explanation": self._create_explanation(signal_type, trend, rsi, normalized, market),
            "summary":    self._safe_summary(signal_type, trend, rsi, adx, volume_relative),
            "reasons":     sanitized_reasons,
            "normalized":  _safe_float(normalized),
            "market":      market,
        }

    # ------------------------------------------------------------------
    def _safe_summary(self, signal_type, trend, rsi, adx, volume_relative) -> str:
        """Crea summary seguro sin exceptions."""
        try:
            return self._create_summary(signal_type, trend, rsi, adx, volume_relative, [])
        except Exception as e:
            logger.warning(f"Error creating summary: {e}")
            return f"Analisis: tendencia {trend}, RSI {rsi:.0f}"

    # ------------------------------------------------------------------
    def _create_summary(self, signal_type, trend, rsi, adx, volume_relative, reasons) -> str:
        """Creates a natural language summary easy to understand."""
        
        # Defaults for None parameters
        rsi = rsi if rsi is not None else 50
        adx = adx if adx is not None else 20
        volume_relative = volume_relative if volume_relative is not None else 1.0
        trend = trend if trend else "LATERAL"
        
        # Determine RSI state
        if rsi < 30:
            rsi_state = "severely oversold"
        elif rsi < 40:
            rsi_state = "oversold"
        elif rsi > 70:
            rsi_state = "severely overbought"
        elif rsi > 60:
            rsi_state = "overbought"
        else:
            rsi_state = "in neutral zone"
        
        # Determine trend strength
        if adx > 40:
            trend_strength = "strong"
        elif adx > 25:
            trend_strength = "moderate"
        else:
            trend_strength = "weak"
        
        # Determine volume
        if volume_relative > 1.5:
            volume_desc = "high, confirming the move"
        elif volume_relative < 0.8:
            volume_desc = "low, suggesting less conviction"
        else:
            volume_desc = "normal"
        
        # Generate text based on signal type
        if signal_type == "BUY":
            if rsi < 40 and (trend == "BULLISH" or trend == "ALCISTA"):
                return (f"The stock shows upward momentum with good strength. "
                        f"RSI is {rsi_state} and price could rise. "
                        f"Volume is {volume_desc}. "
                        f"Trend has {trend_strength} strength (ADX {adx:.0f}).")
            else:
                return (f"Buy signal detected. The trend is {trend.lower()} "
                        f"with {trend_strength} strength. RSI is {rsi_state} "
                        f"and volume is {volume_desc}. "
                        f"Several indicators suggest buying opportunity.")
        
        elif signal_type == "SELL":
            if rsi > 60 and (trend == "BEARISH" or trend == "BAJISTA"):
                return (f"Selling pressure is strong. Price is {rsi_state} "
                        f"and the overall trend is bearish. "
                        f"Volume is {volume_desc}. "
                        f"Several indicators align on sell signal.")
            else:
                return (f"Sell signal detected. Market shows weakness "
                        f"with {trend.lower()} trend. RSI is {rsi_state} "
                        f"and volume is {volume_desc}. "
                        f"Beware of selling pressure.")
        
        else:  # HOLD
            if volume_relative < 0.8:
                return (f"The stock shows {trend.lower()} trend but momentum "
                        f"indicators are in neutral zone. Volume is {volume_desc}. "
                        f"Waiting for a clearer signal before acting is advisable.")
            elif adx < 15:
                return (f"Market is sideways without a clear trend (ADX {adx:.0f}). "
                        f"RSI is {rsi_state} and volume is {volume_desc}. "
                        f"Waiting for confirmation before taking a position is better.")
            else:  # 15 <= adx <= 25
                return (f"The stock shows {trend.lower()} trend with moderate strength. "
                        f"ADX is {adx:.0f}, RSI is {rsi_state}. "
                        f"Volume is {volume_desc}. "
                        f"Waiting for a clearer signal may be prudent.")

    # ------------------------------------------------------------------
    def _create_explanation(self, signal_type, trend, rsi, normalized, market):
        strength = (
            "strong"   if abs(normalized) > 0.6 else
            "moderate" if abs(normalized) > 0.3 else
            "weak"
        )
        rsi_desc = (
            "severely oversold"  if rsi < 30 else
            "oversold"          if rsi < 40 else
            "severely overbought" if rsi > 70 else
            "overbought"         if rsi > 60 else
            "neutral"
        )
        if signal_type == "BUY":
            return (f"BUY ({strength}) [{market}]: {trend} trend, "
                    f"RSI {rsi:.0f} ({rsi_desc}). Confidence {abs(normalized)*100:.0f}%.")
        elif signal_type == "SELL":
            return (f"SELL ({strength}) [{market}]: {trend} trend, "
                    f"RSI {rsi:.0f} ({rsi_desc}). Confidence {abs(normalized)*100:.0f}%.")
        else:
            return (f"HOLD [{market}]: {trend} market, mixed signals. "
                    f"RSI {rsi:.0f} ({rsi_desc}). Wait for confirmation.")

    # ------------------------------------------------------------------
    async def send_signals_to_api(self, signals: list):
        logger.info(f"Sending {len(signals)} signals to {self.api_url}")
        headers = {"Content-Type": "application/json"}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_url}/api/signals/batch",
                    json=signals,
                    headers=headers,
                    timeout=API_BATCH_TIMEOUT,
                )
                if response.status_code == 200:
                    logger.info(f"Successfully sent {len(signals)} signals")
                    return True
                logger.error(f"Error {response.status_code}: {response.text[:500]}")
                return False
            except Exception as e:
                logger.error(f"Connection error: {e}")
                return False
