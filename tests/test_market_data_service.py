# EquiPilot AI - Market Data Service Tests

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

# Mock yfinance before importing service
sys.modules['yfinance'] = MagicMock()

# Now import the service components
from backend.schemas.market_data_schema import MarketDataResponse


class TestMarketDataService:
    """Tests for MarketDataService core functionality."""

    def test_service_module_exists(self):
        """Test that the service module can be imported."""
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "test_market_data_service",
                os.path.join(os.path.dirname(__file__), "..", "backend", "services", "market_data_service.py")
            )
            assert spec is not None
        except Exception as e:
            pytest.fail(f"Service module import failed: {e}")

    def test_schema_direct_instantiation(self):
        """Test schema can be created without external dependencies."""
        data = MarketDataResponse(
            ticker="RELIANCE.NS",
            company_name="Reliance Industries Limited",
            current_price=2500.0,
            previous_close=2450.0,
            market_cap=1500000000000,
            pe_ratio=25.0,
            volume=1000000,
            fifty_two_week_high=2800.0,
            fifty_two_week_low=2000.0,
            sector="Energy",
            industry="Oil & Gas",
        )

        assert data.ticker == "RELIANCE.NS"
        assert data.company_name == "Reliance Industries Limited"
        assert data.current_price == 2500.0

    def test_schema_handles_none_values(self):
        """Test that None values are handled gracefully."""
        data = MarketDataResponse(ticker="TEST.NS")

        assert data.ticker == "TEST.NS"
        assert data.company_name is None
        assert data.current_price is None
        assert data.previous_close is None

    def test_schema_ticker_normalization(self):
        """Test ticker symbol is normalized."""
        data = MarketDataResponse(ticker="  infy.ns  ")
        assert data.ticker == "INFY.NS"

    def test_schema_ticker_validation(self):
        """Test empty ticker raises validation error."""
        with pytest.raises(ValueError):
            MarketDataResponse(ticker="")

    def test_schema_negative_price_rejected(self):
        """Test that negative price values are rejected."""
        with pytest.raises(ValueError):
            MarketDataResponse(ticker="TEST.NS", current_price=-100.0)

    def test_schema_negative_market_cap_rejected(self):
        """Test that negative market cap values are rejected."""
        with pytest.raises(ValueError):
            MarketDataResponse(ticker="TEST.NS", market_cap=-1000000)

    def test_schema_negative_pe_ratio_rejected(self):
        """Test that negative PE ratio values are rejected."""
        with pytest.raises(ValueError):
            MarketDataResponse(ticker="TEST.NS", pe_ratio=-5.0)


class TestMarketDataServiceExceptions:
    """Tests for MarketDataService exception classes."""

    def test_exception_hierarchy(self):
        """Test exception class hierarchy."""
        from backend.services.market_data_service import (
            MarketDataServiceError,
            InvalidTickerError,
            NetworkError,
            DataUnavailableError,
            RateLimitError,
        )

        # All should inherit from MarketDataServiceError
        assert issubclass(InvalidTickerError, MarketDataServiceError)
        assert issubclass(NetworkError, MarketDataServiceError)
        assert issubclass(DataUnavailableError, MarketDataServiceError)
        assert issubclass(RateLimitError, MarketDataServiceError)

        # RateLimitError should also be a NetworkError
        assert issubclass(RateLimitError, NetworkError)

    def test_invalid_ticker_error_instantiation(self):
        """Test InvalidTickerError can be instantiated."""
        from backend.services.market_data_service import InvalidTickerError
        error = InvalidTickerError("Invalid ticker: TEST")
        assert str(error) == "Invalid ticker: TEST"

    def test_network_error_instantiation(self):
        """Test NetworkError can be instantiated."""
        from backend.services.market_data_service import NetworkError
        error = NetworkError("Network failure")
        assert str(error) == "Network failure"

    def test_data_unavailable_error_instantiation(self):
        """Test DataUnavailableError can be instantiated."""
        from backend.services.market_data_service import DataUnavailableError
        error = DataUnavailableError("No data available")
        assert str(error) == "No data available"

    def test_rate_limit_error_instantiation(self):
        """Test RateLimitError can be instantiated."""
        from backend.services.market_data_service import RateLimitError
        error = RateLimitError("Rate limit exceeded")
        assert str(error) == "Rate limit exceeded"


class TestMarketDataServiceLogic:
    """Tests for MarketDataService business logic (mocked)."""

    @pytest.mark.asyncio
    async def test_empty_ticker_raises_invalid_ticker_error(self):
        """Test that empty ticker raises InvalidTickerError."""
        from backend.services.market_data_service import MarketDataService, InvalidTickerError

        service = MarketDataService()

        with pytest.raises(InvalidTickerError, match="cannot be empty"):
            await service.get_stock_info("")

    @pytest.mark.asyncio
    async def test_whitespace_ticker_raises_invalid_ticker_error(self):
        """Test that whitespace-only ticker raises InvalidTickerError."""
        from backend.services.market_data_service import MarketDataService, InvalidTickerError

        service = MarketDataService()

        with pytest.raises(InvalidTickerError, match="cannot be empty"):
            await service.get_stock_info("   ")

    @pytest.mark.asyncio
    async def test_ticker_normalization(self):
        """Test that ticker is normalized to uppercase."""
        from backend.services.market_data_service import MarketDataService

        service = MarketDataService()

        # Mock the internal fetch to return a valid response
        with patch.object(service, '_fetch_yfinance_data') as mock_fetch:
            mock_fetch.return_value = MarketDataResponse(
                ticker="INFY.NS",
                company_name="Infosys Limited",
                current_price=1500.0,
            )

            result = await service.get_stock_info("  infy.ns  ")
            assert result.ticker == "INFY.NS"
            mock_fetch.assert_called_once_with("INFY.NS")

    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_data(self):
        """Test that cached data is returned without fetching."""
        from backend.services.market_data_service import MarketDataService

        service = MarketDataService()

        # Pre-populate cache
        cached_response = MarketDataResponse(
            ticker="TCS.NS",
            company_name="Tata Consultancy Services",
            current_price=3500.0,
        )
        service._cache["TCS.NS"] = cached_response

        result = await service.get_stock_info("TCS.NS")
        assert result.ticker == "TCS.NS"
        assert result.current_price == 3500.0

    @pytest.mark.asyncio
    async def test_cache_expiry_triggers_refetch(self):
        """Test that expired cache triggers a new fetch."""
        from backend.services.market_data_service import MarketDataService

        service = MarketDataService()
        service._cache_ttl_seconds = 1  # Very short TTL

        # Pre-populate cache with old data
        cached_response = MarketDataResponse(
            ticker="TCS.NS",
            company_name="Old Name",
            current_price=1000.0,
        )
        service._cache["TCS.NS"] = cached_response

        # Mock the internal fetch
        with patch.object(service, '_fetch_yfinance_data') as mock_fetch:
            mock_fetch.return_value = MarketDataResponse(
                ticker="TCS.NS",
                company_name="New Name",
                current_price=3500.0,
            )

            # Wait for cache to expire
            import asyncio
            await asyncio.sleep(1.1)

            result = await service.get_stock_info("TCS.NS")
            assert result.company_name == "New Name"
            assert result.current_price == 3500.0
            mock_fetch.assert_called_once_with("TCS.NS")


class TestMarketDataServiceYFinanceIntegration:
    """Tests for _fetch_yfinance_data method with mocked yfinance."""

    @pytest.mark.asyncio
    async def test_fetch_yfinance_data_success(self):
        """Test successful yfinance data fetch."""
        from backend.services.market_data_service import MarketDataService

        service = MarketDataService()

        # Create a mock yfinance Ticker
        mock_ticker = MagicMock()
        mock_ticker.info = {
            "symbol": "RELIANCE.NS",
            "longName": "Reliance Industries Limited",
            "currentPrice": 2500.0,
            "previousClose": 2450.0,
            "marketCap": 1500000000000,
            "trailingPE": 25.0,
            "volume": 1000000,
            "fiftyTwoWeekHigh": 2800.0,
            "fiftyTwoWeekLow": 2000.0,
            "sector": "Energy",
            "industry": "Oil & Gas",
        }

        with patch('yfinance.Ticker', return_value=mock_ticker):
            result = service._fetch_yfinance_data("RELIANCE.NS")

            assert result.ticker == "RELIANCE.NS"
            assert result.company_name == "Reliance Industries Limited"
            assert result.current_price == 2500.0
            assert result.market_cap == 1500000000000
            assert result.pe_ratio == 25.0

    @pytest.mark.asyncio
    async def test_fetch_yfinance_data_invalid_ticker(self):
        """Test yfinance fetch with invalid ticker (no symbol)."""
        from backend.services.market_data_service import MarketDataService, InvalidTickerError

        service = MarketDataService()

        # Create a mock yfinance Ticker with no symbol
        mock_ticker = MagicMock()
        mock_ticker.info = {}

        with patch('yfinance.Ticker', return_value=mock_ticker):
            with pytest.raises(InvalidTickerError, match="Invalid ticker symbol"):
                service._fetch_yfinance_data("INVALID.NS")

    @pytest.mark.asyncio
    async def test_fetch_yfinance_data_no_price_no_name(self):
        """Test yfinance fetch with no price and no name raises DataUnavailableError."""
        from backend.services.market_data_service import MarketDataService, DataUnavailableError

        service = MarketDataService()

        # Create a mock yfinance Ticker with symbol but no price or name
        mock_ticker = MagicMock()
        mock_ticker.info = {"symbol": "TEST.NS"}

        with patch('yfinance.Ticker', return_value=mock_ticker):
            with pytest.raises(DataUnavailableError, match="No market data available"):
                service._fetch_yfinance_data("TEST.NS")

    @pytest.mark.asyncio
    async def test_fetch_yfinance_data_uses_regularMarketPrice_fallback(self):
        """Test that regularMarketPrice is used as fallback for currentPrice."""
        from backend.services.market_data_service import MarketDataService

        service = MarketDataService()

        # Create a mock yfinance Ticker with regularMarketPrice but no currentPrice
        mock_ticker = MagicMock()
        mock_ticker.info = {
            "symbol": "TEST.NS",
            "regularMarketPrice": 1500.0,
        }

        with patch('yfinance.Ticker', return_value=mock_ticker):
            result = service._fetch_yfinance_data("TEST.NS")

            assert result.current_price == 1500.0

    @pytest.mark.asyncio
    async def test_fetch_yfinance_data_json_decode_error_rate_limit(self):
        """Test JSONDecodeError with empty response is treated as rate limit."""
        from backend.services.market_data_service import MarketDataService, RateLimitError
        import json

        service = MarketDataService()

        # Create a mock yfinance Ticker that raises JSONDecodeError when info is accessed
        mock_ticker = MagicMock()
        type(mock_ticker).info = property(lambda self: (_ for _ in ()).throw(
            json.JSONDecodeError("Expecting value", "", 0)
        ))

        with patch('yfinance.Ticker', return_value=mock_ticker):
            with pytest.raises(RateLimitError, match="rate limit exceeded"):
                service._fetch_yfinance_data("TEST.NS")

    @pytest.mark.asyncio
    async def test_fetch_yfinance_data_network_error_on_timeout(self):
        """Test timeout error is wrapped as NetworkError."""
        from backend.services.market_data_service import MarketDataService, NetworkError

        service = MarketDataService()

        # Create a mock yfinance Ticker that raises timeout error
        mock_ticker = MagicMock()
        type(mock_ticker).info = property(lambda self: (_ for _ in ()).throw(
            TimeoutError("Connection timed out")
        ))

        with patch('yfinance.Ticker', return_value=mock_ticker):
            with pytest.raises(NetworkError, match="Network error fetching"):
                service._fetch_yfinance_data("TEST.NS")

    @pytest.mark.asyncio
    async def test_fetch_yfinance_data_missing_optional_fields(self):
        """Test that missing optional fields are handled gracefully."""
        from backend.services.market_data_service import MarketDataService

        service = MarketDataService()

        # Create a mock yfinance Ticker with only required fields
        mock_ticker = MagicMock()
        mock_ticker.info = {
            "symbol": "TEST.NS",
            "longName": "Test Company",
            "currentPrice": 100.0,
        }

        with patch('yfinance.Ticker', return_value=mock_ticker):
            result = service._fetch_yfinance_data("TEST.NS")

            assert result.ticker == "TEST.NS"
            assert result.company_name == "Test Company"
            assert result.current_price == 100.0
            assert result.market_cap is None
            assert result.pe_ratio is None
            assert result.volume is None
            assert result.fifty_two_week_high is None
            assert result.fifty_two_week_low is None
            assert result.sector is None
            assert result.industry is None