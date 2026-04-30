import pytest
import time
from unittest.mock import patch, MagicMock
import json

from services.company_metadata import (
    _empty_info,
    get_company_info,
    _fetch_from_yfinance,
    metadata_cache,
    yfinance_cache
)


class TestEmptyInfo:
    """Tests for _empty_info function"""

    @patch('services.company_metadata._fetch_from_yfinance')
    def test_returns_dict_with_symbol_as_name(self, mock_yfinance):
        mock_yfinance.return_value = "AAPL"

        result = _empty_info("AAPL")

        assert result["name"] == "AAPL"

    def test_returns_empty_logo_for_unknown_symbol(self):
        result = _empty_info("UNKNOWN")
        assert result["logo"] == ""

    def test_returns_sector_from_static_mapping(self):
        result = _empty_info("AAPL")
        assert result["sector"] == "Technology"

    def test_returns_empty_exchange_and_country(self):
        result = _empty_info("AAPL")
        assert result["exchange"] == ""
        assert result["country"] == ""

    def test_returns_empty_industry(self):
        result = _empty_info("AAPL")
        assert result["industry"] == ""

    def test_returns_none_for_marketcap(self):
        result = _empty_info("AAPL")
        assert result["marketCap"] is None


class TestGetCompanyInfo:
    """Tests for get_company_info function"""

    def setup_method(self):
        """Clear caches before each test"""
        metadata_cache.clear()
        yfinance_cache.clear()

    @patch('services.company_metadata._fetch_from_finnhub')
    def test_returns_cached_data(self, mock_finnhub):
        metadata_cache["AAPL"] = {
            "data": {"name": "Cached Apple", "logo": "", "sector": "Tech", "industry": "", "exchange": "", "country": "", "marketCap": 1000},
            "timestamp": time.time()
        }

        result = get_company_info("AAPL")

        assert result["name"] == "Cached Apple"
        mock_finnhub.assert_not_called()

    @patch('services.company_metadata._fetch_from_finnhub')
    def test_fetches_when_cache_expired(self, mock_finnhub):
        metadata_cache["AAPL"] = {
            "data": {"name": "Old Apple", "logo": "", "sector": "", "industry": "", "exchange": "", "country": "", "marketCap": None},
            "timestamp": time.time() - 1000000
        }

        mock_finnhub.return_value = {"name": "Fresh Apple", "logo": "url", "sector": "Tech", "industry": "Software", "exchange": "NASDAQ", "country": "US", "marketCap": 3000}

        with patch('services.company_metadata.FINNHUB_API_KEY', 'test_key'):
            result = get_company_info("AAPL")

        assert result["name"] == "Fresh Apple"
        mock_finnhub.assert_called_once_with("AAPL")

    @patch('services.company_metadata._fetch_from_finnhub')
    def test_calls_finnhub_when_not_cached(self, mock_finnhub):
        mock_finnhub.return_value = {"name": "Apple Inc.", "logo": "https://logo.url", "sector": "Technology", "industry": "Consumer Electronics", "exchange": "NASDAQ", "country": "US", "marketCap": 3000000000}

        with patch('services.company_metadata.FINNHUB_API_KEY', 'test_key'):
            result = get_company_info("AAPL")

        assert result["name"] == "Apple Inc."
        mock_finnhub.assert_called_once_with("AAPL")

    @patch('services.company_metadata._fetch_from_finnhub')
    def test_caches_result_after_fetch(self, mock_finnhub):
        mock_finnhub.return_value = {"name": "Apple", "logo": "", "sector": "", "industry": "", "exchange": "", "country": "", "marketCap": None}

        with patch('services.company_metadata.FINNHUB_API_KEY', 'test_key'):
            get_company_info("AAPL")

        assert "AAPL" in metadata_cache

    @patch.dict('services.company_metadata.metadata_cache', {}, clear=True)
    @patch('services.company_metadata._fetch_from_finnhub')
    def test_handles_finnhub_404_with_empty_info(self, mock_finnhub):
        import os
        original_key = os.environ.get('FINNHUB_API_KEY', '')

        try:
            os.environ['FINNHUB_API_KEY'] = 'test_key'
            mock_finnhub.side_effect = Exception("404")

            with patch.dict(os.environ, {'FINNHUB_API_KEY': 'test_key'}):
                result = get_company_info("INVALID")
                assert "name" in result
        finally:
            os.environ['FINNHUB_API_KEY'] = original_key


class TestFetchFromYfinance:
    """Tests for _fetch_from_yfinance function"""

    def setup_method(self):
        """Clear cache before each test"""
        yfinance_cache.clear()

    @patch('services.company_metadata.yf.Ticker')
    def test_returns_cached_name(self, mock_ticker_class):
        yfinance_cache["AAPL"] = {
            "name": "Cached Apple",
            "timestamp": time.time()
        }

        result = _fetch_from_yfinance("AAPL")

        assert result == "Cached Apple"
        mock_ticker_class.assert_not_called()

    @patch('services.company_metadata.yf.Ticker')
    def test_returns_symbol_when_cache_expired(self, mock_ticker_class):
        yfinance_cache["AAPL"] = {
            "name": "Old Name",
            "timestamp": time.time() - 200000
        }

        mock_ticker = MagicMock()
        mock_ticker.info = {"longName": "New Apple"}
        mock_ticker_class.return_value = mock_ticker

        result = _fetch_from_yfinance("AAPL")

        assert result == "New Apple"

    @patch('services.company_metadata.yf.Ticker')
    def test_returns_symbol_on_error(self, mock_ticker_class):
        mock_ticker_class.side_effect = Exception("Network error")

        result = _fetch_from_yfinance("INVALID")

        assert result == "INVALID"

    @patch('services.company_metadata.yf.Ticker')
    def test_uses_shortname_as_fallback(self, mock_ticker_class):
        mock_ticker = MagicMock()
        mock_ticker.info = {"shortName": "Short Apple"}
        mock_ticker_class.return_value = mock_ticker

        result = _fetch_from_yfinance("AAPL")

        assert result == "Short Apple"

    @patch('services.company_metadata.yf.Ticker')
    def test_handles_case_insensitive_symbol(self, mock_ticker_class):
        mock_ticker = MagicMock()
        mock_ticker.info = {"longName": "Apple"}
        mock_ticker_class.return_value = mock_ticker

        result = _fetch_from_yfinance("aapl")

        assert result == "Apple"
        mock_ticker_class.assert_called_once_with("AAPL")


class TestMetadataCache:
    """Tests for metadata cache behavior"""

    def setup_method(self):
        metadata_cache.clear()
        yfinance_cache.clear()

    def test_cache_is_dict(self):
        assert isinstance(metadata_cache, dict)

    def test_cache_can_be_populated(self):
        metadata_cache["TEST"] = {"data": {"name": "Test"}, "timestamp": time.time()}
        assert "TEST" in metadata_cache

    def test_cache_can_be_cleared(self):
        metadata_cache["TEST"] = {"data": {"name": "Test"}, "timestamp": time.time()}
        metadata_cache.clear()
        assert len(metadata_cache) == 0