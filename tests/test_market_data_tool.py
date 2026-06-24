# EquiPilot AI - Market Data Tool Tests

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from datetime import datetime
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