import os
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "..", "config", "stock-config.json")

def _load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    logger.warning(f"Config file not found at {CONFIG_PATH}, using defaults")
    return {}

_config = _load_config()

API_URL = os.getenv("API_URL", "http://localhost:8081")
API_TOKEN = os.getenv("API_JWT_TOKEN", "")

US_SYMBOLS = _config.get("stocks", {}).get("US", [])
AR_SYMBOLS = _config.get("stocks", {}).get("AR", [])
EU_SYMBOLS = _config.get("stocks", {}).get("EU", [])
JP_SYMBOLS = _config.get("stocks", {}).get("JP", [])

indicators = _config.get("indicators", {})
scoring = _config.get("scoring", {})
finnhub_cfg = _config.get("finnhub", {})
scheduler_cfg = _config.get("scheduler", {})
api_cfg = _config.get("api", {})
server_cfg = _config.get("server", {})

INDICATOR_RSI_PERIOD = int(os.getenv("RSI_PERIOD", indicators.get("rsi_period", 14)))
INDICATOR_EMA_SHORT = int(os.getenv("EMA_SHORT", indicators.get("ema_short", 20)))
INDICATOR_EMA_LONG = int(os.getenv("EMA_LONG", indicators.get("ema_long", 50)))
INDICATOR_MACD_FAST = int(os.getenv("MACD_FAST", indicators.get("macd_fast", 12)))
INDICATOR_MACD_SLOW = int(os.getenv("MACD_SLOW", indicators.get("macd_slow", 26)))
INDICATOR_MACD_SIGNAL = int(os.getenv("MACD_SIGNAL", indicators.get("macd_signal", 9)))
INDICATOR_ATR_PERIOD = int(os.getenv("ATR_PERIOD", indicators.get("atr_period", 14)))
AVG_VOLUME_PERIOD = int(os.getenv("AVG_VOLUME_PERIOD", indicators.get("avg_volume_period", 20)))

SCORING_TREND_WEIGHT = float(os.getenv("TREND_WEIGHT", scoring.get("trend_weight", 2)))
SCORING_RSI_REVERSAL_WEIGHT = float(os.getenv("RSI_REVERSAL_WEIGHT", scoring.get("rsi_reversal_weight", 3)))
SCORING_MACD_WEIGHT = float(os.getenv("MACD_WEIGHT", scoring.get("macd_weight", 1)))
SCORING_MACD_CROSS_WEIGHT = float(os.getenv("MACD_CROSS_WEIGHT", scoring.get("macd_cross_weight", 2)))
SCORING_OVERSOLD = float(os.getenv("OVERSOLD_THRESHOLD", scoring.get("oversold_threshold", 30)))
SCORING_OVERSOLD_MILD = float(os.getenv("OVERSOLD_MILD", scoring.get("oversold_mild", 40)))
SCORING_OVERBOUGHT = float(os.getenv("OVERBOUGHT_THRESHOLD", scoring.get("overbought_threshold", 70)))
SCORING_OVERBOUGHT_MILD = float(os.getenv("OVERBOUGHT_MILD", scoring.get("overbought_mild", 60)))
SCORING_BUY_MIN = float(os.getenv("BUY_MIN_SCORE", scoring.get("buy_min_score", 2)))
SCORING_SELL_MAX = float(os.getenv("SELL_MAX_SCORE", scoring.get("sell_max_score", -2)))
SCORING_EMA_PROXIMITY_PCT = float(os.getenv("EMA_PROXIMITY_PCT", scoring.get("ema_proximity_pct", 0.5)))
SCORING_VOLUME_SURGE_MULTIPLIER = float(os.getenv("VOLUME_SURGE_MULTIPLIER", scoring.get("volume_surge_multiplier", 1.5)))
SCORING_ATR_VOLATILITY_PCT = float(os.getenv("ATR_VOLATILITY_PCT", scoring.get("atr_volatility_pct", 2.5)))
SCORING_VOLUME_WEIGHT = float(os.getenv("VOLUME_WEIGHT", scoring.get("volume_weight", 1)))
SCORING_ATR_PENALTY = float(os.getenv("ATR_PENALTY", scoring.get("atr_penalty", 0.5)))

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
FINNHUB_CACHE_TTL = int(os.getenv("FINNHUB_CACHE_TTL", finnhub_cfg.get("cache_ttl", 86400)))
FINNHUB_RATE_LIMIT_DELAY = float(os.getenv("FINNHUB_RATE_LIMIT_DELAY", finnhub_cfg.get("rate_limit_delay", 0.5)))
FINNHUB_MAX_RETRIES = int(os.getenv("FINNHUB_MAX_RETRIES", finnhub_cfg.get("max_retries", 3)))
FINNHUB_TIMEOUT = float(os.getenv("FINNHUB_TIMEOUT", finnhub_cfg.get("timeout", 10.0)))

SCHEDULE_HOUR = int(os.getenv("SCHEDULE_HOUR", scheduler_cfg.get("hour", 6)))
SCHEDULE_MINUTE = int(os.getenv("SCHEDULE_MINUTE", scheduler_cfg.get("minute", 0)))
SCHEDULER_CALL_DELAY = float(os.getenv("SCHEDULER_CALL_DELAY", scheduler_cfg.get("call_delay_between_symbols", 0.3)))

API_BATCH_TIMEOUT = float(os.getenv("API_BATCH_TIMEOUT", api_cfg.get("batch_timeout", 180.0)))
MIN_DATA_DAYS = int(os.getenv("MIN_DATA_DAYS", api_cfg.get("min_data_days", 30)))
DAYS_FOR_52W_HIGH = int(os.getenv("DAYS_FOR_52W_HIGH", api_cfg.get("days_for_52w_high", 252)))
CACHE_TTL = int(os.getenv("CACHE_TTL", api_cfg.get("cache_ttl_seconds", 600)))
SYMBOL_REGEX = os.getenv("SYMBOL_REGEX", api_cfg.get("symbol_regex", "^[A-Z0-9\\.]{1,10}$"))
VALID_MARKETS = os.getenv("VALID_MARKETS", ",".join(api_cfg.get("valid_markets", ["AR", "US", "EU", "JP"]))).split(",")

PYTHON_PORT = int(os.getenv("PORT", server_cfg.get("python_port", 8000)))

DEFAULT_DAYS = int(os.getenv("DEFAULT_DAYS", api_cfg.get("default_days", 365)))

COMPANY_DOMAINS = _config.get("company_domains", {})
