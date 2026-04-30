import asyncio
import httpx
import json
import pandas as pd
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging
import math
from datetime import datetime

from config import (
    SCHEDULE_HOUR, SCHEDULE_MINUTE, API_URL, API_TOKEN,
    SCHEDULER_CALL_DELAY, US_SYMBOLS, AR_SYMBOLS, EU_SYMBOLS, JP_SYMBOLS
)
from services.analyzer import TechnicalAnalyzer
from services.company_metadata import get_company_info

logger = logging.getLogger(__name__)


def _safe_float(value):
    """Sanitiza valores NaN/Inf para JSON."""
    if value is None:
        return 0.0
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return 0.0
        return float(value)
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def _clean_dict(d: dict) -> dict:
    """Limpia el dict de valores NaN/Inf para JSON."""
    result = {}
    for k, v in d.items():
        if isinstance(v, float):
            if math.isnan(v) or math.isinf(v):
                result[k] = 0.0
            else:
                result[k] = round(v, 4)
        elif isinstance(v, dict):
            result[k] = _clean_dict(v)
        elif isinstance(v, list):
            # Don't convert strings to floats - keep them as is
            result[k] = [_clean_dict(x) if isinstance(x, dict) else x for x in v]
        else:
            result[k] = v
    return result


def create_signal_dict(symbol: str, market: str, indicators: dict, signal: dict, price: float, df=None) -> dict:
    meta = get_company_info(symbol)

    company_name = meta["name"] if meta["name"] != symbol else symbol
    logo_url = meta["logo"] if meta["logo"] else ""

    price_change_24h = 0
    price_change_percent_24h = 0
    
    # Get valid price
    valid_prices = df['close'].dropna() if df is not None and 'close' in df else pd.Series()
    current_price = valid_prices.iloc[-1] if len(valid_prices) > 0 else 0
    
    if len(valid_prices) >= 2:
        prev_close = valid_prices.iloc[-2]
        if prev_close > 0:
            price_change_24h = _safe_float(current_price - prev_close)
            price_change_percent_24h = _safe_float((current_price - prev_close) / prev_close * 100)

    current_volume = float(df['volume'].iloc[-1]) if df is not None and 'volume' in df.columns else 0
    avg_volume = indicators.get('avg_volume', 0)
    volume_relative = round(current_volume / avg_volume, 2) if avg_volume > 0 else 1.0

    logger.info(f"Looking up {symbol} -> {company_name}")
    signal_dict = {
        "symbol": symbol,
        "market": market,
        "companyName": company_name,
        "signalType": signal["signal_type"],
        "trend": signal["trend"],
        "explanation": signal["explanation"],
        "summary": signal.get("summary", ""),
        "reasons": json.dumps(signal.get("reasons", [])),
        "rsi": _safe_float(indicators.get("rsi")),
        "ema20": _safe_float(indicators.get("ema20")),
        "ema50": _safe_float(indicators.get("ema50")),
        "macd": _safe_float(indicators.get("macd")),
        "atr": _safe_float(indicators.get("atr")),
        "price": _safe_float(price),
        "priceChange24h": price_change_24h,
        "priceChangePercent24h": price_change_percent_24h,
        "volumeRelative": _safe_float(volume_relative),
        "analyzedAt": datetime.now().isoformat(),
        "sector": meta.get("sector"),
        "industry": meta.get("industry"),
        "exchange": meta.get("exchange"),
        "country": meta.get("country"),
        "logoUrl": logo_url,
        "marketCap": _safe_float(meta["marketCap"]) if meta.get("marketCap") else None,
    }
    return _clean_dict(signal_dict)


class Scheduler:
    def __init__(self, data_fetcher, analyzer, signal_generator):
        self.data_fetcher = data_fetcher
        self.analyzer = analyzer
        self.signal_generator = signal_generator
        self.scheduler = AsyncIOScheduler()

    async def fetch_stocks_from_api(self) -> tuple[list, list, list, list]:
        logger.info(f"Using defaults: US={len(US_SYMBOLS)}, AR={len(AR_SYMBOLS)}, EU={len(EU_SYMBOLS)}, JP={len(JP_SYMBOLS)}")
        return US_SYMBOLS, AR_SYMBOLS, EU_SYMBOLS, JP_SYMBOLS

    async def analyze_symbol(self, symbol: str, market: str) -> dict | None:
        try:
            df = self.data_fetcher.fetch_data(symbol, market)
            if df is None or df.empty:
                return None

            indicators = self.analyzer.calculate_indicators(df)
            valid_prices = df['close'].dropna()
            current_price = valid_prices.iloc[-1] if len(valid_prices) > 0 else 0
            volume = float(df['volume'].iloc[-1]) if 'volume' in df.columns else 0
            signal = self.signal_generator.generate_signal(
                indicators,
                current_price,
                volume,
                market=market
            )

            return create_signal_dict(symbol, market, indicators, signal, current_price, df)

        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None

    async def run_analysis(self):
        logger.info("Starting daily analysis...")

        # Despertar el Java API antes de empezar
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                await client.get(f"{API_URL}/api/health", timeout=60.0)
                logger.info("Java API is awake")
        except Exception as e:
            logger.warning(f"Could not ping Java API: {e}, continuing anyway")

        us_symbols, ar_symbols, eu_symbols, jp_symbols = await self.fetch_stocks_from_api()
        logger.info(f"US symbols: {len(us_symbols)}, AR symbols: {len(ar_symbols)}, EU symbols: {len(eu_symbols)}, JP symbols: {len(jp_symbols)}")

        signals = []
        for symbol in us_symbols:
            logger.info(f"Analyzing {symbol}...")
            signal_dict = await self.analyze_symbol(symbol, "US")
            if signal_dict:
                signals.append(signal_dict)
                logger.info(f"  {symbol}: {signal_dict['signalType']}")
            else:
                logger.warning(f"  {symbol}: No signal generated")
            await asyncio.sleep(SCHEDULER_CALL_DELAY)

        for symbol in ar_symbols:
            logger.info(f"Analyzing {symbol}...")
            signal_dict = await self.analyze_symbol(symbol, "AR")
            if signal_dict:
                signals.append(signal_dict)
                logger.info(f"  {symbol}: {signal_dict['signalType']}")
            else:
                logger.warning(f"  {symbol}: No signal generated")
            await asyncio.sleep(SCHEDULER_CALL_DELAY)

        for symbol in eu_symbols:
            logger.info(f"Analyzing {symbol}...")
            signal_dict = await self.analyze_symbol(symbol, "EU")
            if signal_dict:
                signals.append(signal_dict)
                logger.info(f"  {symbol}: {signal_dict['signalType']}")
            else:
                logger.warning(f"  {symbol}: No signal generated")
            await asyncio.sleep(SCHEDULER_CALL_DELAY)

        for symbol in jp_symbols:
            logger.info(f"Analyzing {symbol}...")
            signal_dict = await self.analyze_symbol(symbol, "JP")
            if signal_dict:
                signals.append(signal_dict)
                logger.info(f"  {symbol}: {signal_dict['signalType']}")
            else:
                logger.warning(f"  {symbol}: No signal generated")
            await asyncio.sleep(SCHEDULER_CALL_DELAY)

        logger.info(f"Total signals generated: {len(signals)}")

        by_type = {}
        for s in signals:
            t = s['signalType']
            by_type[t] = by_type.get(t, 0) + 1
        logger.info(f"Signals by type: {by_type}")

        if signals:
            logger.info(f"Calling send_signals_to_api with {len(signals)} signals...")
            logger.info(f"First 5 symbols: {[s['symbol'] for s in signals[:5]]}")
            result = await self.signal_generator.send_signals_to_api(signals)
            logger.info(f"send_signals_to_api result: {result}")
        else:
            logger.warning("No signals to send!")

        logger.info(f"Analysis completed. {len(signals)} signals generated.")

    def start(self):
        self.scheduler.add_job(
            self.run_analysis,
            CronTrigger(hour=SCHEDULE_HOUR, minute=SCHEDULE_MINUTE),
            id="daily_analysis",
            name="Daily stock analysis",
            replace_existing=True
        )
        self.scheduler.start()
        logger.info(f"Scheduler started. Next analysis at {SCHEDULE_HOUR}:{SCHEDULE_MINUTE:02d}")

    def stop(self):
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")

    def run_now(self):
        asyncio.run(self.run_analysis())
