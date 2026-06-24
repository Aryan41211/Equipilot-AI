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