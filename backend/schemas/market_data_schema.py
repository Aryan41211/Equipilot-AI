# EquiPilot AI - Market Data Tool Schema
# Pydantic schema for market data tool responses

from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator


class MarketDataResponse(BaseModel):
    """Response schema for market data tool."""

    ticker: str = Field(..., description="Stock ticker symbol")
    company_name: str | None = Field(default=None, description="Company full name")
    current_price: float | None = Field(default=None, description="Current stock price")
    previous_close: float | None = Field(default=None, description="Previous close price")
    market_cap: float | None = Field(default=None, description="Market capitalization")
    pe_ratio: float | None = Field(default=None, description="P/E ratio")
    volume: int | None = Field(default=None, description="Trading volume")
    fifty_two_week_high: float | None = Field(
        default=None, alias="fifty_two_week_high", description="52-week high"
    )
    fifty_two_week_low: float | None = Field(
        default=None, alias="fifty_two_week_low", description="52-week low"
    )
    sector: str | None = Field(default=None, description="Company sector")
    industry: str | None = Field(default=None, description="Company industry")
    data_as_of: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
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
    def validate_positive(cls, v: float | None) -> float | None:
        """Validate numeric fields are positive when present."""
        if v is not None and v < 0:
            raise ValueError("Value must be positive")
        return v

    model_config = {"populate_by_name": True}
