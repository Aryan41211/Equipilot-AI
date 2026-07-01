# EquiPilot AI - Market Data Schemas
# Pydantic models for market data structures

from datetime import datetime

from pydantic import BaseModel, Field


class PriceData(BaseModel):
    """Single price data point."""

    date: datetime
    open: float
    high: float
    low: float
    close: float
    adjusted_close: float | None = None
    volume: int

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class FundamentalsData(BaseModel):
    """Company fundamental data."""

    # Valuation
    market_cap: float | None = None
    enterprise_value: float | None = None
    pe_ratio: float | None = None
    forward_pe: float | None = None
    peg_ratio: float | None = None
    price_to_book: float | None = None
    price_to_sales: float | None = None
    ev_to_revenue: float | None = None
    ev_to_ebitda: float | None = None

    # Profitability
    profit_margin: float | None = None
    operating_margin: float | None = None
    return_on_assets: float | None = None
    return_on_equity: float | None = None

    # Financial Health
    total_cash: float | None = None
    total_debt: float | None = None
    current_ratio: float | None = None
    debt_to_equity: float | None = None

    # Growth
    revenue_growth: float | None = None
    earnings_growth: float | None = None

    # Dividends
    dividend_yield: float | None = None
    payout_ratio: float | None = None
    dividend_date: datetime | None = None

    # Metadata
    currency: str = "USD"
    last_updated: datetime | None = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class TechnicalIndicators(BaseModel):
    """Technical indicator values."""

    sma_20: float | None = None
    sma_50: float | None = None
    sma_200: float | None = None
    ema_12: float | None = None
    ema_26: float | None = None
    rsi_14: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    macd_histogram: float | None = None
    bollinger_upper: float | None = None
    bollinger_middle: float | None = None
    bollinger_lower: float | None = None
    atr_14: float | None = None
    volume_sma_20: float | None = None


class MarketData(BaseModel):
    """Complete market data for a ticker."""

    ticker: str
    company_name: str | None = None
    currency: str = "USD"
    exchange: str | None = None
    sector: str | None = None
    industry: str | None = None

    # Current price info
    current_price: float | None = None
    previous_close: float | None = None
    change: float | None = None
    change_percent: float | None = None

    # Price history
    price_history: list[PriceData] = Field(default_factory=list)

    # Fundamentals
    fundamentals: FundamentalsData | None = None

    # Technicals
    technicals: TechnicalIndicators | None = None

    # Metadata
    data_as_of: datetime = Field(default_factory=datetime.utcnow)
    source: str = "yfinance"

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class MarketDataResponse(BaseModel):
    """Response model for market data requests."""

    tickers: list[str]
    data: dict[str, MarketData]
    errors: dict[str, str] = Field(default_factory=dict)
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
