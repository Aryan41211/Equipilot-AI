# EquiPilot AI - Market Data Tool Schema
# Pydantic schema for market data tool responses

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class MarketDataResponse(BaseModel):
    """Response schema for market data tool."""

    ticker: str = Field(..., description="Stock ticker symbol")
    company_name: Optional[str] = Field(default=None, description="Company full name")
    current_price: Optional[float] = Field(default=None, description="Current stock price")
    previous_close: Optional[float] = Field(default=None, description="Previous close price")
    market_cap: Optional[float] = Field(default=None, description="Market capitalization")
    pe_ratio: Optional[float] = Field(default=None, description="P/E ratio")
    volume: Optional[int] = Field(default=None, description="Trading volume")
    fifty_two_week_high: Optional[float] = Field(
        default=None, alias="fifty_two_week_high", description="52-week high"
    )
    fifty_two_week_low: Optional[float] = Field(
        default=None, alias="fifty_two_week_low", description="52-week low"
    )
    sector: Optional[str] = Field(default=None, description="Company sector")
    industry: Optional[str] = Field(default=None, description="Company industry")
    data_as_of: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Data timestamp"
    )

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        """Validate ticker symbol is not empty."""
        if not v or not v.strip():
            raise ValueError("Ticker symbol cannot be empty")
        return v.upper().strip()

    @field_validator("current_price", "previous_close", "market_cap", "pe_ratio")
    @classmethod
    def validate_positive(cls, v: Optional[float]) -> Optional[float]:
        """Validate numeric fields are positive when present."""
        if v is not None and v < 0:
            raise ValueError("Value must be positive")
        return v

    model_config = {"populate_by_name": True}