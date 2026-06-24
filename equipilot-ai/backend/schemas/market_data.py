# EquiPilot AI - Market Data Schemas
# Pydantic models for market data structures

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PriceData(BaseModel):
    """Single price data point."""

    date: datetime
    open: float
    high: float
    low: float
    close: float
    adjusted_close: Optional[float] = None
    volume: int

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class FundamentalsData(BaseModel):
    """Company fundamental data."""

    # Valuation
    market_cap: Optional[float] = None
    enterprise_value: Optional[float] = None
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    peg_ratio: Optional[float] = None
    price_to_book: Optional[float] = None
    price_to_sales: Optional[float] = None
    ev_to_revenue: Optional[float] = None
    ev_to_ebitda: Optional[float] = None

    # Profitability
    profit_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    return_on_assets: Optional[float] = None
    return_on_equity: Optional[float] = None

    # Financial Health
    total_cash: Optional[float] = None
    total_debt: Optional[float] = None
    current_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None

    # Growth
    revenue_growth: Optional[float] = None
    earnings_growth: Optional[float] = None

    # Dividends
    dividend_yield: Optional[float] = None
    payout_ratio: Optional[float] = None
    dividend_date: Optional[datetime] = None

    # Metadata
    currency: str = "USD"
    last_updated: Optional[datetime] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class TechnicalIndicators(BaseModel):
    """Technical indicator values."""

    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    rsi_14: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    bollinger_upper: Optional[float] = None
    bollinger_middle: Optional[float] = None
    bollinger_lower: Optional[float] = None
    atr_14: Optional[float] = None
    volume_sma_20: Optional[float] = None


class MarketData(BaseModel):
    """Complete market data for a ticker."""

    ticker: str
    company_name: Optional[str] = None
    currency: str = "USD"
    exchange: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None

    # Current price info
    current_price: Optional[float] = None
    previous_close: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None

    # Price history
    price_history: List[PriceData] = Field(default_factory=list)

    # Fundamentals
    fundamentals: Optional[FundamentalsData] = None

    # Technicals
    technicals: Optional[TechnicalIndicators] = None

    # Metadata
    data_as_of: datetime = Field(default_factory=datetime.utcnow)
    source: str = "yfinance"

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class MarketDataResponse(BaseModel):
    """Response model for market data requests."""

    tickers: List[str]
    data: Dict[str, MarketData]
    errors: Dict[str, str] = Field(default_factory=dict)
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}