import os
import time
import logging

import httpx
import yfinance as yf

from config import (
    FINNHUB_API_KEY, FINNHUB_CACHE_TTL, FINNHUB_RATE_LIMIT_DELAY,
    FINNHUB_MAX_RETRIES, FINNHUB_TIMEOUT, COMPANY_DOMAINS
)

logger = logging.getLogger(__name__)

FINNHUB_BASE_URL = os.getenv("FINNHUB_BASE_URL", "https://finnhub.io/api/v1")

CUSTOM_LOGOS = {
    "KO": "https://img.logo.dev/coca-colacompany.com?token=pk_B0mxnLC-SRe4RJbuTTfLDg&size=80&retina=true",
    "BYMA": "https://img.logo.dev/ticker/BYMA.BA?token=pk_B0mxnLC-SRe4RJbuTTfLDg&size=80&retina=true",
}

SECTORS = {
    "AAPL": "Technology",
    "GOOGL": "Technology",
    "MSFT": "Technology",
    "NVDA": "Technology",
    "AMD": "Technology",
    "INTC": "Technology",
    "CSCO": "Technology",
    "ORCL": "Technology",
    "CRM": "Technology",
    "ADBE": "Technology",
    "PLTR": "Technology",
    "SNOW": "Technology",
    "DDOG": "Technology",
    "ZS": "Technology",
    "JNJ": "Healthcare",
    "UNH": "Healthcare",
    "PFE": "Healthcare",
    "ABBV": "Healthcare",
    "MRK": "Healthcare",
    "LLY": "Healthcare",
    "GLOB": "Technology",
    "META": "Communication Services",
    "JPM": "Financials",
    "BAC": "Financials",
    "WFC": "Financials",
    "GS": "Financials",
    "C": "Financials",
    "PYPL": "Financials",
    "COIN": "Financials",
    "BBAR": "Financials",
    "BMA": "Financials",
    "XOM": "Energy",
    "CVX": "Energy",
    "SLB": "Energy",
    "AMZN": "Consumer Discretionary",
    "TSLA": "Consumer Discretionary",
    "DIS": "Consumer Discretionary",
    "NFLX": "Consumer Discretionary",
    "ROKU": "Consumer Discretionary",
    "RIVN": "Consumer Discretionary",
    "LCID": "Consumer Discretionary",
    "MELI": "Consumer Discretionary",
    "TM": "Consumer Discretionary",
    "KO": "Consumer Staples",
    "PEP": "Consumer Staples",
    "WMT": "Consumer Staples",
    "COST": "Consumer Staples",
    "OR.PA": "Consumer Staples",
    "T": "Communication Services",
    "VZ": "Communication Services",
    "SNAP": "Communication Services",
    "DTE.DE": "Communication Services",
    "SONY": "Communication Services",
    "CEPU": "Utilities",
    "NIO": "Electric Vehicles",
    "XPEV": "Electric Vehicles",
    "LI": "Electric Vehicles",
    "UBER": "Ridesharing",
    "LYFT": "Ridesharing",
    "IBM": "Technology",
    "BA": "Industrials",
    "MCD": "Consumer Discretionary",
    "NKE": "Consumer Discretionary",
    "HD": "Consumer Discretionary",
    "V": "Financials",
    "MA": "Financials",
    "LVMH": "Consumer Staples",
    "NESN.SW": "Consumer Staples",
    "AIR.PA": "Industrials",
    "SAP.DE": "Technology",
    "ASML.AS": "Technology",
    "ALV.DE": "Financials",
    "SHEL.L": "Energy",
    "TM": "Consumer Discretionary",
    "SONY": "Communication Services",
    "YPF": "Energy",
    "PAM": "Utilities",
    "TEO": "Communication Services",
    "CRESY": "Real Estate",
    "IRCP": "Real Estate",
    "BYMA": "Financials",
    "BRIO": "Energy",
    "JG": "Consumer Discretionary",
    "GCLA": "Communication Services",
}

metadata_cache = {}
yfinance_cache = {}
YFINANCE_CACHE_TTL = int(os.getenv("YFINANCE_CACHE_TTL", 86400))

_last_call_time = 0



def _rate_limit():
    global _last_call_time
    elapsed = time.time() - _last_call_time
    if elapsed < FINNHUB_RATE_LIMIT_DELAY:
        wait = FINNHUB_RATE_LIMIT_DELAY - elapsed
        time.sleep(wait)
    _last_call_time = time.time()


def _fetch_from_yfinance(symbol: str) -> str:
    symbol_upper = symbol.upper()

    if symbol_upper in yfinance_cache:
        entry = yfinance_cache[symbol_upper]
        if time.time() - entry["timestamp"] < YFINANCE_CACHE_TTL:
            return entry["name"]

    try:
        ticker = yf.Ticker(symbol_upper)
        info = ticker.info
        name = info.get('longName') or info.get('shortName') or symbol_upper

        yfinance_cache[symbol_upper] = {
            "name": name,
            "timestamp": time.time()
        }
        logger.info(f"YFinance fetched name for {symbol}: {name}")
        return name
    except Exception as e:
        logger.warning(f"YFinance failed for {symbol}: {e}")
        return symbol_upper


def get_company_info(symbol: str) -> dict:
    symbol_upper = symbol.upper()

    if symbol_upper in metadata_cache:
        entry = metadata_cache[symbol_upper]
        if time.time() - entry["timestamp"] < FINNHUB_CACHE_TTL:
            return entry["data"]
        else:
            del metadata_cache[symbol_upper]

    if not FINNHUB_API_KEY:
        logger.warning("FINNHUB_API_KEY not set, returning defaults")
        return _empty_info(symbol_upper)

    info = _fetch_from_finnhub(symbol_upper)

    metadata_cache[symbol_upper] = {
        "data": info,
        "timestamp": time.time(),
    }

    return info


def _fetch_from_finnhub(symbol: str) -> dict:
    for attempt in range(FINNHUB_MAX_RETRIES):
        _rate_limit()

        try:
            url = f"{FINNHUB_BASE_URL}/stock/profile2"
            params = {"symbol": symbol, "token": FINNHUB_API_KEY}

            with httpx.Client(timeout=FINNHUB_TIMEOUT) as client:
                resp = client.get(url, params=params)

            if resp.status_code == 429:
                retry_after = float(resp.headers.get("Retry-After", 5))
                logger.warning(f"Finnhub rate limited for {symbol}, waiting {retry_after}s (attempt {attempt + 1})")
                time.sleep(retry_after)
                continue

            if resp.status_code == 403:
                logger.warning(f"Finnhub returned 403 for {symbol} (not available on this plan)")
                return _empty_info(symbol)

            resp.raise_for_status()
            data = resp.json()

            if not data or "name" not in data or not data.get("name"):
                logger.warning(f"Finnhub returned empty profile for {symbol}")
                return _empty_info(symbol)

            market_cap = data.get("marketCapitalization")
            finnhub_sector = data.get("finnhubIndustry", "") or ""
            fallback_sector = SECTORS.get(symbol, "") or ""
            sector = fallback_sector if fallback_sector else finnhub_sector
            info = {
                "name": data.get("name", symbol),
                "logo": data.get("logo", ""),
                "exchange": data.get("exchange", ""),
                "country": data.get("country", ""),
                "sector": sector,
                "industry": finnhub_sector,
                "marketCap": float(market_cap) if market_cap else None,
                "webUrl": data.get("weburl", ""),
            }

            logger.info(f"Fetched metadata for {symbol}: {info['name']} ({info['exchange']})")
            return info

        except httpx.ReadTimeout:
            logger.warning(f"Timeout fetching metadata for {symbol} (attempt {attempt + 1})")
            time.sleep(2)
            continue
        except Exception as e:
            logger.error(f"Error fetching metadata for {symbol} from Finnhub: {e}")
            if attempt < FINNHUB_MAX_RETRIES - 1:
                time.sleep(2)
                continue
            return _empty_info(symbol)

    return _empty_info(symbol)


def _empty_info(symbol: str) -> dict:
    symbol_upper = symbol.upper()
    domain = COMPANY_DOMAINS.get(symbol_upper, "")
    
    logo_url = CUSTOM_LOGOS.get(symbol_upper, "")
    if not logo_url and domain:
        logo_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=64"

    name = _fetch_from_yfinance(symbol)

    return {
        "name": name,
        "logo": logo_url,
        "exchange": "",
        "country": "",
        "sector": SECTORS.get(symbol_upper, ""),
        "industry": "",
        "marketCap": None,
        "webUrl": "",
    }
