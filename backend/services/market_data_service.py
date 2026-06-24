# EquiPilot AI - Market Data Service
# Pure service layer for fetching stock information

import asyncio
from datetime import datetime
from typing import Dict, Optional
import yfinance as yf

from backend.schemas.market_data_schema import MarketDataResponse
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class MarketDataService:
    """Service for fetching stock market data from yfinance."""

    def __init__(self):
        self._cache: Dict[str, MarketDataResponse] = {}
        self._cache_ttl_seconds = 300

    async def get_stock_info(self, ticker: str) -> MarketDataResponse:
        """
        Fetch stock information for a single ticker.

        Args:
            ticker: Stock ticker symbol (e.g., "RELIANCE.NS", "TCS.NS")

        Returns:
            MarketDataResponse with stock information

        Raises:
            ValueError: If ticker is invalid or empty
            RuntimeError: If network request fails or ticker not found
        """
        if not ticker or not ticker.strip():
            raise ValueError("Ticker symbol cannot be empty")

        ticker = ticker.upper().strip()

        # Check cache
        if ticker in self._cache:
            cached = self._cache[ticker]
            if (datetime.utcnow() - cached.data_as_of).total_seconds() < self._cache_ttl_seconds:
                logger.debug("Cache hit", ticker=ticker)
                return cached

        # Fetch data asynchronously
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, self._fetch_yfinance_data, ticker
            )
            self._cache[ticker] = response
            return response
        except Exception as e:
            logger.error("Failed to fetch stock data", ticker=ticker, error=str(e))
            raise RuntimeError(f"Failed to fetch data for {ticker}: {str(e)}") from e

    def _fetch_yfinance_data(self, ticker: str) -> MarketDataResponse:
        """Fetch data from yfinance in a blocking manner."""
        yf_ticker = yf.Ticker(ticker)
        info = yf_ticker.info

        if not info or not info.get("symbol"):
            raise ValueError(f"Invalid ticker symbol: {ticker}")

        return MarketDataResponse(
            ticker=ticker,
            company_name=info.get("longName") or info.get("shortName") or None,
            current_price=info.get("currentPrice"),
            previous_close=info.get("previousClose"),
            market_cap=info.get("marketCap"),
            pe_ratio=info.get("trailingPE"),
            volume=info.get("volume"),
            fifty_two_week_high=info.get("fiftyTwoWeekHigh"),
            fifty_two_week_low=info.get("fiftyTwoWeekLow"),
            sector=info.get("sector"),
            industry=info.get("industry"),
            data_as_of=datetime.utcnow(),
        )


# Singleton instance
market_data_service = MarketDataService()