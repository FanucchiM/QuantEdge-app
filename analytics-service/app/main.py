# -*- coding: utf-8 -*-
import os
import sys

# Add the app directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
import time
import asyncio
import math
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import datetime, timedelta
import re

from config import (
    logger, VALID_MARKETS, SYMBOL_REGEX, MIN_DATA_DAYS,
    DAYS_FOR_52W_HIGH, CACHE_TTL, PYTHON_PORT, COMPANY_DOMAINS
)
from services.data_fetcher import DataFetcher
from services.analyzer import TechnicalAnalyzer
from services.signal_generator import SignalGenerator
from services.scheduler import Scheduler
from services.company_metadata import get_company_info


def safe_float(value):
    """Sanitize NaN/Inf values for JSON."""
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


app = FastAPI(title="Stock Analytics Service", version="1.0.0")

stock_cache = {}

def get_market_from_symbol(symbol: str) -> str:
    if symbol in ("TM", "SONY"):
        return "JP"
    if '.' in symbol:
        if symbol.endswith('.AS'):
            return 'EU'
        elif symbol.endswith(('.L', '.DE', '.PA', '.SW')):
            return 'EU'
        elif symbol.endswith('.BA'):
            return 'AR'
    return 'US'

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:4200").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

data_fetcher = DataFetcher()
analyzer = TechnicalAnalyzer()
signal_generator = SignalGenerator()
scheduler = Scheduler(data_fetcher, analyzer, signal_generator)


class SignalRequest(BaseModel):
    symbol: str
    market: str

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        if not re.match(SYMBOL_REGEX, v):
            raise ValueError(f'Invalid stock symbol. Must match {SYMBOL_REGEX}')
        return v

    @field_validator('market')
    @classmethod
    def validate_market(cls, v: str) -> str:
        if v.upper() not in VALID_MARKETS:
            raise ValueError(f'Invalid market. Must be one of: {VALID_MARKETS}')
        return v.upper()


class SignalResponse(BaseModel):
    symbol: str
    market: str
    signal_type: str
    normalized: float
    trend: str
    explanation: str
    rsi: float
    ema20: float
    ema50: float
    macd: float
    atr: float
    price: float
    analyzed_at: str


@app.get("/")
def root():
    return {"status": "ok", "service": "Stock Analytics", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/debug/indicators/{symbol}")
def debug_indicators(symbol: str, market: str = "US"):
    return {
        "symbol": symbol,
        "market": market,
        "message": "yfinance not available from Render - use /debug/test-send to test integration"
    }


@app.get("/debug/test-send")
def debug_test_send():
    """Envía signals de ejemplo al Java API para probar la integración"""
    import asyncio
    import httpx
    from datetime import datetime
    import json
    
    test_signals = [
        {
            "symbol": "AAPL",
            "market": "US",
            "companyName": "Apple Inc.",
            "signalType": "BUY",
            "trend": "BULLISH",
            "explanation": "Test signal from debug endpoint",
            "summary": "Test signal",
            "reasons": "Test reason 1; Test reason 2",
            "rsi": 35.0,
            "ema20": 175.5,
            "ema50": 170.2,
            "macd": 2.5,
            "atr": 3.2,
            "price": 178.5,
            "priceChange24h": 1.2,
            "priceChangePercent24h": 0.68,
            "volumeRelative": 1.2,
            "analyzedAt": datetime.now().isoformat(),
        },
        {
            "symbol": "GOOGL",
            "market": "US",
            "companyName": "Alphabet Inc.",
            "signalType": "BUY",
            "trend": "BULLISH",
            "explanation": "Test signal for GOOGL",
            "summary": "Test",
            "reasons": "EMA bullish; RSI oversold",
            "rsi": 38.0,
            "ema20": 142.0,
            "ema50": 138.5,
            "macd": 1.8,
            "atr": 2.8,
            "price": 145.2,
            "analyzedAt": datetime.now().isoformat(),
        },
    ]
    
    api_url = "https://quantedge-api-a1ib.onrender.com"
    
    async def send():
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{api_url}/api/signals/batch",
                    json=test_signals,
                    headers={"Content-Type": "application/json"},
                    timeout=30.0,
                )
                return {"status": response.status_code, "body": response.text[:500]}
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}
    
    result = asyncio.run(send())
    return {"sent": len(test_signals), "api_url": api_url, "result": result}


@app.post("/analyze", response_model=List[SignalResponse])
def analyze_stocks(symbols: List[SignalRequest]):
    results = []
    for req in symbols:
        try:
            df = data_fetcher.fetch_data(req.symbol, req.market)
            if df is None or df.empty:
                continue

            indicators = analyzer.calculate_indicators(df)
            volume = float(df['volume'].iloc[-1]) if 'volume' in df.columns else 0
            signal = signal_generator.generate_signal(indicators, df['close'].iloc[-1], volume, market=req.market)

            results.append(SignalResponse(
                symbol=req.symbol,
                market=req.market,
                signal_type=signal["signal_type"],
                normalized=signal.get("normalized", 0),
                trend=signal["trend"],
                explanation=signal["explanation"],
                rsi=indicators["rsi"],
                ema20=indicators["ema20"],
                ema50=indicators["ema50"],
                macd=indicators["macd"],
                atr=indicators["atr"],
                price=float(df['close'].iloc[-1]),
                analyzed_at=datetime.now().isoformat()
            ))
        except Exception as e:
            logger.error(f"Error analyzing {req.symbol}: {e}")
            continue

    return results


@app.post("/analyze/single")
def analyze_single(request: SignalRequest):
    try:
        df = data_fetcher.fetch_data(request.symbol, request.market)
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail="No data found")

        indicators = analyzer.calculate_indicators(df)
        volume = float(df['volume'].iloc[-1]) if 'volume' in df.columns else 0
        signal = signal_generator.generate_signal(indicators, df['close'].iloc[-1], volume, market=request.market)

        return {
            "symbol": request.symbol,
            "market": request.market,
            "signal_type": signal["signal_type"],
            "normalized": signal.get("normalized", 0),
            "trend": signal["trend"],
            "explanation": signal["explanation"],
            "summary": signal.get("summary", ""),
            "reasons": signal.get("reasons", []),
            
            "rsi": indicators.get("rsi"),
            "ema20": indicators.get("ema20"),
            "ema50": indicators.get("ema50"),
            "macd": indicators.get("macd"),
            "macd_line": indicators.get("macd_line"),
            "macd_signal": indicators.get("macd_signal"),
            "atr": indicators.get("atr"),
            
            "adx": indicators.get("adx"),
            "plus_di": indicators.get("plus_di"),
            "minus_di": indicators.get("minus_di"),
            "stoch_k": indicators.get("stoch_k"),
            "stoch_d": indicators.get("stoch_d"),
            "bb_position": indicators.get("bb_position"),
            "sr_position": indicators.get("sr_position"),
            "high_52w": indicators.get("high_52w"),
            "low_52w": indicators.get("low_52w"),
            
            "price": float(df['close'].iloc[-1]),
            "analyzed_at": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/run")
def run_analysis():
    import asyncio
    asyncio.run(scheduler.run_analysis())
    return {"status": "Analysis completed"}


@app.post("/scheduler/start")
def start_scheduler():
    scheduler.start()
    return {"status": "Scheduler started"}


@app.post("/scheduler/stop")
def stop_scheduler():
    scheduler.stop()
    return {"status": "Scheduler stopped"}


@app.get("/stock/{symbol}/history")
def get_stock_history(
    symbol: str,
    days: int = Query(default=60, ge=30, le=365)
):
    cache_key = f"{symbol.upper()}_{days}"
    current_time = time.time()

    if cache_key in stock_cache:
        cached_data = stock_cache[cache_key]
        if current_time - cached_data["timestamp"] < CACHE_TTL:
            logger.info(f"Cache hit for {cache_key}")
            cached_data["data"]["cachedAt"] = datetime.fromtimestamp(cached_data["timestamp"]).isoformat()
            cached_data["data"]["cacheExpiresAt"] = datetime.fromtimestamp(cached_data["timestamp"] + CACHE_TTL).isoformat()
            return cached_data["data"]

    logger.info(f"Cache miss for {cache_key}, calculating...")

    try:
        market = get_market_from_symbol(symbol)
        df = data_fetcher.fetch_data(symbol.upper(), market)

        if df is None or df.empty:
            raise HTTPException(status_code=404, detail="No data found")

        if len(df) > days:
            df = df.tail(days)

        df_with_indicators = analyzer.get_all_indicators(df.copy())
        indicators = analyzer.calculate_indicators(df.copy())

        # Get last valid price
        valid_prices = df['close'].dropna()
        current_price = safe_float(valid_prices.iloc[-1]) if len(valid_prices) > 0 else 0
        current_rsi = indicators["rsi"]

        if len(valid_prices) >= 2:
            prev_close = safe_float(valid_prices.iloc[-2])
            price_change_24h = current_price - prev_close
            price_change_percent_24h = (price_change_24h / prev_close) * 100 if prev_close > 0 else 0
        else:
            price_change_24h = 0
            price_change_percent_24h = 0

        if len(df) >= DAYS_FOR_52W_HIGH:
            high_52w = safe_float(df['high'].tail(DAYS_FOR_52W_HIGH).max())
            low_52w = safe_float(df['low'].tail(DAYS_FOR_52W_HIGH).min())
        else:
            high_52w = safe_float(df['high'].max())
            low_52w = safe_float(df['low'].min())

        volume = safe_float(df['volume'].iloc[-1]) if 'volume' in df.columns else 0
        signal = signal_generator.generate_signal(
            indicators,
            current_price,
            volume,
            market=market
        )

        signal_type = "NEUTRAL"
        if current_rsi < 30 and signal["trend"] == "BEARISH":
            signal_type = "OVERSOLD_REVERSAL"
        elif current_rsi > 70 and signal["trend"] == "BULLISH":
            signal_type = "OVERBOUGHT_CORRECTION"
        elif signal["signal_type"] == "BUY":
            signal_type = "BULLISH_TREND"
        elif signal["signal_type"] == "SELL":
            signal_type = "BEARISH_TREND"

        if hasattr(df.index, 'strftime'):
            dates = df.index.strftime('%Y-%m-%d').tolist()
        else:
            dates = [str(d) for d in df.index.tolist()]
        
        # Use only valid prices for charts
        prices = df['close'].dropna().tolist()
        if len(prices) == 0:
            prices = [0.0] * len(dates)
        
        prices = [safe_float(p) for p in prices]
        ema20 = df_with_indicators['EMA20'].fillna(0).tolist()
        ema50 = df_with_indicators['EMA50'].fillna(0).tolist()
        rsi_values = df_with_indicators['RSI'].fillna(50).tolist()

        prices = [safe_float(p) for p in prices]
        ema20 = [safe_float(e) for e in ema20]
        ema50 = [safe_float(e) for e in ema50]
        rsi_values = [safe_float(r) for r in rsi_values]

        symbol_upper = symbol.upper()
        meta = get_company_info(symbol_upper)

        company_name = meta["name"] if meta["name"] != symbol_upper else symbol_upper
        if meta["logo"]:
            logo_url = meta["logo"]
        else:
            domain = COMPANY_DOMAINS.get(symbol_upper, "")
            logo_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=64" if domain else ""

        result = {
            "symbol": symbol_upper,
            "companyName": company_name,
            "logoUrl": logo_url,
            "market": market,
            "signalType": signal["signal_type"],
            "currentPrice": current_price,
            "priceChange24h": round(price_change_24h, 2),
            "priceChangePercent24h": round(price_change_percent_24h, 2),
            "high52w": round(high_52w, 2),
            "low52w": round(low_52w, 2),
            "signalGenerated": {
                "date": datetime.now().strftime('%Y-%m-%d'),
                "atPrice": round(current_price, 2),
                "rsi": round(current_rsi, 1),
                "type": signal_type
            },
            "chartData": {
                "dates": dates,
                "price": prices,
                "ema20": ema20,
                "ema50": ema50,
                "rsi": rsi_values
            },
            "sector": meta["sector"],
            "industry": meta["industry"],
            "exchange": meta["exchange"],
            "country": meta["country"],
            "marketCap": meta["marketCap"],
        }

        stock_cache[cache_key] = {
            "data": result,
            "timestamp": current_time
        }

        result["cachedAt"] = datetime.fromtimestamp(current_time).isoformat()
        result["cacheExpiresAt"] = datetime.fromtimestamp(current_time + CACHE_TTL).isoformat()

        logger.info(f"Successfully generated history for {symbol.upper()} with {len(dates)} data points")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting history for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stock/{symbol}/seasonality")
def get_stock_seasonality(
    symbol: str,
    years: str = Query(default="2026,2025")
):
    """Get historical seasonal performance by month."""
    try:
        years_list = [int(y.strip()) for y in years.split(",")]
        
        market = get_market_from_symbol(symbol)
        df = data_fetcher.fetch_data(symbol.upper(), market)
        
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail="No data found")
        
        seasonality = analyzer.calculate_seasonality(df.copy(), years_list)
        
        return seasonality
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting seasonality for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cache/clear")
def clear_cache():
    global stock_cache
    stock_cache = {}
    return {"status": "Cache cleared", "entries": 0}


@app.get("/cache/status")
def cache_status():
    current_time = time.time()
    entries = []
    for key, data in stock_cache.items():
        age = current_time - data["timestamp"]
        remaining = max(0, CACHE_TTL - age)
        entries.append({
            "key": key,
            "ageSeconds": round(age, 1),
            "expiresInSeconds": round(remaining, 1)
        })
    return {
        "totalEntries": len(stock_cache),
        "ttlSeconds": CACHE_TTL,
        "entries": entries
    }


if __name__ == "__main__":
    import threading
    import asyncio

    def run_initial_analysis():
        asyncio.run(scheduler.run_analysis())

    thread = threading.Thread(target=run_initial_analysis, daemon=True)
    thread.start()


@app.get("/debug/stocks")
def debug_stocks():
    from config import US_SYMBOLS, AR_SYMBOLS, EU_SYMBOLS, JP_SYMBOLS
    return {
        "us_count": len(US_SYMBOLS),
        "ar_count": len(AR_SYMBOLS),
        "eu_count": len(EU_SYMBOLS),
        "jp_count": len(JP_SYMBOLS),
        "us": US_SYMBOLS[:5],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PYTHON_PORT)
