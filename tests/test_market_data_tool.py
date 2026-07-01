# EquiPilot AI - Market Data Tool Tests

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import AsyncMock, patch

import pytest

from backend.schemas.market_data_schema import MarketDataResponse


class TestMarketDataSchema:
    """Tests for MarketDataResponse schema validation."""

    def test_valid_schema_creation(self):
        """Test that valid data creates a schema instance."""
        data = MarketDataResponse(
            ticker="INFY.NS",
            company_name="Infosys Limited",
            current_price=1500.0,
            sector="Technology",
            industry="IT Services",
        )

        assert data.ticker == "INFY.NS"
        assert data.company_name == "Infosys Limited"
        assert data.current_price == 1500.0
        assert data.sector == "Technology"

    def test_ticker_validation_uppercase(self):
        """Test that ticker is validated and uppercased."""
        data = MarketDataResponse(ticker="infy.ns")
        assert data.ticker == "INFY.NS"

    def test_ticker_validation_stripped(self):
        """Test that ticker whitespace is stripped."""
        data = MarketDataResponse(ticker="  TCS.NS  ")
        assert data.ticker == "TCS.NS"

    def test_ticker_validation_empty_raises(self):
        """Test that empty ticker raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            MarketDataResponse(ticker="")

    def test_all_fields_optional_except_ticker(self):
        """Test that all fields except ticker are optional."""
        data = MarketDataResponse(ticker="RELIANCE.NS")
        assert data.ticker == "RELIANCE.NS"
        assert data.company_name is None
        assert data.current_price is None

    def test_fifty_two_week_high_low_set(self):
        """Test that 52-week high/low fields work correctly."""
        data = MarketDataResponse(
            ticker="TEST.NS",
            fifty_two_week_high=2800.0,
            fifty_two_week_low=2000.0,
        )

        assert data.fifty_two_week_high == 2800.0
        assert data.fifty_two_week_low == 2000.0

    def test_model_dump_returns_dict(self):
        """Test that model_dump returns a proper dictionary."""
        data = MarketDataResponse(
            ticker="RELIANCE.NS",
            company_name="Reliance Industries",
            current_price=2500.0,
            previous_close=2450.0,
            market_cap=1500000000000,
            pe_ratio=25.0,
            volume=1000000,
            sector="Energy",
        )

        result = data.model_dump()
        assert isinstance(result, dict)
        assert result["ticker"] == "RELIANCE.NS"
        assert result["company_name"] == "Reliance Industries"


class TestMarketDataTool:
    """Tests for MarketDataTool fetch_market_data method."""

    @pytest.mark.asyncio
    async def test_fetch_market_data_success(self):
        """Test successful market data fetch via tool."""
        from backend.tools.market_data_tool import MarketDataTool

        mock_response = MarketDataResponse(
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

        with patch('backend.tools.market_data_tool.market_data_service.get_stock_info',
                   new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await MarketDataTool.fetch_market_data("RELIANCE.NS")

            assert result["ticker"] == "RELIANCE.NS"
            assert result["company_name"] == "Reliance Industries Limited"
            assert result["current_price"] == 2500.0
            assert result["market_cap"] == 1500000000000
            assert "error" not in result

    @pytest.mark.asyncio
    async def test_fetch_market_data_invalid_ticker(self):
        """Test tool handles invalid ticker error."""
        from backend.services.market_data_service import InvalidTickerError
        from backend.tools.market_data_tool import MarketDataTool

        with patch('backend.tools.market_data_tool.market_data_service.get_stock_info',
                   new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = InvalidTickerError("Invalid ticker symbol: INVALID.NS")

            result = await MarketDataTool.fetch_market_data("INVALID.NS")

            assert result["error"] == "Invalid ticker symbol: INVALID.NS"
            assert result["ticker"] == "INVALID.NS"
            assert result["error_type"] == "invalid_ticker"

    @pytest.mark.asyncio
    async def test_fetch_market_data_data_unavailable(self):
        """Test tool handles data unavailable error."""
        from backend.services.market_data_service import DataUnavailableError
        from backend.tools.market_data_tool import MarketDataTool

        with patch('backend.tools.market_data_tool.market_data_service.get_stock_info',
                   new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = DataUnavailableError("No market data available for ticker: TEST.NS")

            result = await MarketDataTool.fetch_market_data("TEST.NS")

            assert result["error"] == "No market data available for ticker: TEST.NS"
            assert result["ticker"] == "TEST.NS"
            assert result["error_type"] == "data_unavailable"

    @pytest.mark.asyncio
    async def test_fetch_market_data_rate_limit(self):
        """Test tool handles rate limit error."""
        from backend.services.market_data_service import RateLimitError
        from backend.tools.market_data_tool import MarketDataTool

        with patch('backend.tools.market_data_tool.market_data_service.get_stock_info',
                   new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = RateLimitError("Yahoo Finance rate limit exceeded for TEST.NS")

            result = await MarketDataTool.fetch_market_data("TEST.NS")

            assert result["error"] == "Yahoo Finance rate limit exceeded for TEST.NS"
            assert result["ticker"] == "TEST.NS"
            assert result["error_type"] == "rate_limit"

    @pytest.mark.asyncio
    async def test_fetch_market_data_network_error(self):
        """Test tool handles network error."""
        from backend.services.market_data_service import NetworkError
        from backend.tools.market_data_tool import MarketDataTool

        with patch('backend.tools.market_data_tool.market_data_service.get_stock_info',
                   new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = NetworkError("Network error fetching TEST.NS: Connection failed")

            result = await MarketDataTool.fetch_market_data("TEST.NS")

            assert "Network error" in result["error"]
            assert result["ticker"] == "TEST.NS"
            assert result["error_type"] == "network_error"

    @pytest.mark.asyncio
    async def test_fetch_market_data_service_error(self):
        """Test tool handles generic service error."""
        from backend.services.market_data_service import MarketDataServiceError
        from backend.tools.market_data_tool import MarketDataTool

        with patch('backend.tools.market_data_tool.market_data_service.get_stock_info',
                   new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = MarketDataServiceError("Generic service error")

            result = await MarketDataTool.fetch_market_data("TEST.NS")

            assert "Generic service error" in result["error"]
            assert result["ticker"] == "TEST.NS"
            assert result["error_type"] == "service_error"

    @pytest.mark.asyncio
    async def test_fetch_market_data_unexpected_error(self):
        """Test tool handles unexpected errors."""
        from backend.tools.market_data_tool import MarketDataTool

        with patch('backend.tools.market_data_tool.market_data_service.get_stock_info',
                   new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = RuntimeError("Unexpected runtime error")

            result = await MarketDataTool.fetch_market_data("TEST.NS")

            assert "Unexpected error" in result["error"]
            assert result["ticker"] == "TEST.NS"
            assert result["error_type"] == "unexpected_error"

    @pytest.mark.asyncio
    async def test_fetch_market_data_empty_ticker(self):
        """Test tool handles empty ticker."""
        from backend.services.market_data_service import InvalidTickerError
        from backend.tools.market_data_tool import MarketDataTool

        with patch('backend.tools.market_data_tool.market_data_service.get_stock_info',
                   new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = InvalidTickerError("Ticker symbol cannot be empty")

            result = await MarketDataTool.fetch_market_data("")

            assert result["error"] == "Ticker symbol cannot be empty"
            assert result["ticker"] == ""
            assert result["error_type"] == "invalid_ticker"

    @pytest.mark.asyncio
    async def test_fetch_market_data_convenience_function(self):
        """Test the convenience function works."""
        from backend.tools.market_data_tool import fetch_market_data

        mock_response = MarketDataResponse(
            ticker="INFY.NS",
            company_name="Infosys Limited",
            current_price=1500.0,
        )

        with patch('backend.tools.market_data_tool.market_data_service.get_stock_info',
                   new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await fetch_market_data("INFY.NS")

            assert result["ticker"] == "INFY.NS"
            assert result["company_name"] == "Infosys Limited"

    @pytest.mark.asyncio
    async def test_fetch_market_data_with_minimal_fields(self):
        """Test tool works with minimal data (only ticker and name)."""
        from backend.tools.market_data_tool import MarketDataTool

        mock_response = MarketDataResponse(
            ticker="TEST.NS",
            company_name="Test Company",
        )

        with patch('backend.tools.market_data_tool.market_data_service.get_stock_info',
                   new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await MarketDataTool.fetch_market_data("TEST.NS")

            assert result["ticker"] == "TEST.NS"
            assert result["company_name"] == "Test Company"
            assert result["current_price"] is None
            assert "error" not in result


class TestMarketDataToolIntegration:
    """Integration tests for market data tool (with real service mock)."""

    @pytest.mark.asyncio
    async def test_tool_uses_service_singleton(self):
        """Test that tool uses the singleton service instance."""
        from backend.services.market_data_service import MarketDataService
        from backend.tools.market_data_tool import market_data_service

        # The tool should use the imported singleton
        assert market_data_service is not None
        assert isinstance(market_data_service, MarketDataService)
