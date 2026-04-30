import yfinance as yf
import pandas as pd
import logging
from datetime import datetime, timedelta

from config import DEFAULT_DAYS, MIN_DATA_DAYS

logger = logging.getLogger(__name__)

# Sufijos por mercado para yfinance
MARKET_SUFFIXES = {
    "AR": ".BA",   # Buenos Aires Stock Exchange
    "JP": "",      # TM, SONY cotizan en US como ADRs (sin sufijo)
    "EU": "",      # Ya viene con sufijo en el símbolo (SAP.DE, ASML.AS, etc.)
    "US": "",      # Sin sufijo
}


class DataFetcher:

    def _build_ticker_symbol(self, symbol: str, market: str) -> str:
        """
        Construye el símbolo correcto para yfinance según el mercado.
        EU ya trae el sufijo en el símbolo (ej: SAP.DE, ASML.AS, SHEL.L)
        así que no se agrega nada.
        """
        suffix = MARKET_SUFFIXES.get(market.upper(), "")
        if suffix and not symbol.endswith(suffix):
            return f"{symbol}{suffix}"
        return symbol

    def fetch_data(self, symbol: str, market: str = "US") -> pd.DataFrame | None:
        try:
            ticker_symbol = self._build_ticker_symbol(symbol, market)

            ticker   = yf.Ticker(ticker_symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=DEFAULT_DAYS)

            df = ticker.history(start=start_date, end=end_date)

            if df.empty:
                logger.warning(f"No data found for {ticker_symbol} (market={market})")
                return None

            df = df.reset_index()
            df.columns = [c.lower() if isinstance(c, str) else c for c in df.columns]

            required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required_cols):
                logger.warning(f"Missing columns for {ticker_symbol}: {df.columns.tolist()}")
                return None

            if len(df) < MIN_DATA_DAYS:
                logger.warning(
                    f"Insufficient data for {ticker_symbol}: {len(df)} days "
                    f"(minimum {MIN_DATA_DAYS})"
                )
                return None

            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
                df = df.set_index('date')

            logger.debug(f"Fetched {len(df)} rows for {ticker_symbol}")
            return df

        except Exception as e:
            logger.error(f"Error fetching data for {symbol} (market={market}): {e}")
            return None

    def has_valid_data(self, symbol: str, market: str = "US") -> bool:
        df = self.fetch_data(symbol, market)
        return df is not None and len(df) >= MIN_DATA_DAYS
