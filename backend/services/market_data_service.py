# EquiPilot AI - Market Data Service
# Pure service layer for fetching stock information

import asyncio
import json
from datetime import UTC, datetime

import yfinance as yf

from backend.schemas.market_data_schema import MarketDataResponse
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class MarketDataServiceError(Exception):
    """Base exception for market data service errors."""
    pass


class InvalidTickerError(MarketDataServiceError):
    """Raised when ticker symbol is invalid or not found."""
    pass


class NetworkError(MarketDataServiceError):
    """Raised when network request fails."""
    pass


class DataUnavailableError(MarketDataServiceError):
    """Raised when Yahoo Finance is unavailable or returns no data."""
    pass


class RateLimitError(NetworkError):
    """Raised when Yahoo Finance rate limit is exceeded."""
    pass


class MarketDataService:
    """Service for fetching stock market data from yfinance."""

    def __init__(self):
        self._cache: dict[str, MarketDataResponse] = {}
        self._cache_ttl_seconds = 300
        self._max_retries = 3
        self._retry_delay_seconds = 1.0

    async def get_stock_info(self, ticker: str) -> MarketDataResponse:
        """
        Fetch stock information for a single ticker.

        Args:
            ticker: Stock ticker symbol (e.g., "RELIANCE.NS", "TCS.NS")

        Returns:
            MarketDataResponse with stock information

        Raises:
            InvalidTickerError: If ticker is invalid, empty, or not found
            NetworkError: If network request fails
            DataUnavailableError: If Yahoo Finance is unavailable or returns no data
        """
        if not ticker or not ticker.strip():
            raise InvalidTickerError("Ticker symbol cannot be empty")

        ticker = ticker.upper().strip()

        # Check cache
        if ticker in self._cache:
            cached = self._cache[ticker]
            if (datetime.now(UTC) - cached.data_as_of).total_seconds() < self._cache_ttl_seconds:
                logger.debug("Cache hit", ticker=ticker)
                return cached

        # Fetch data with retries
        last_exception = None
        for attempt in range(self._max_retries):
            try:
                response = await asyncio.to_thread(self._fetch_yfinance_data, ticker)
                self._cache[ticker] = response
                logger.info("Successfully fetched stock data", ticker=ticker, attempt=attempt + 1)
                return response
            except InvalidTickerError:
                # Don't retry invalid tickers
                raise
            except (NetworkError, DataUnavailableError) as e:
                last_exception = e
                logger.warning(
                    " fetch attempt failed",
                    ticker=ticker,
                    attempt=attempt + 1,
                    max_retries=self._max_retries,
                    error=str(e),
                )
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay_seconds * (attempt + 1))
            except Exception as e:
                last_exception = e
                logger.error(
                    "Unexpected error fetching stock data",
                    ticker=ticker,
                    attempt=attempt + 1,
                    error=str(e),
                )
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay_seconds * (attempt + 1))

        # All retries exhausted
        logger.error(
            "All fetch attempts failed",
            ticker=ticker,
            max_retries=self._max_retries,
            error=str(last_exception),
        )
        raise NetworkError(
            f"Failed to fetch data for {ticker} after {self._max_retries} attempts: {last_exception}"
        ) from last_exception

    def _fetch_yfinance_data(self, ticker: str) -> MarketDataResponse:
        """Fetch data from yfinance in a blocking manner with error handling."""
        try:
            yf_ticker = yf.Ticker(ticker)
            info = yf_ticker.info
        except json.JSONDecodeError as e:
            # Check if the underlying cause is rate limiting (empty response at position 0)
            error_msg = str(e).lower()
            if "too many requests" in error_msg or "429" in error_msg or "rate limit" in error_msg:
                raise RateLimitError(f"Yahoo Finance rate limit exceeded for {ticker}") from e
            # Empty response (position 0) often indicates rate limiting
            if "char 0" in str(e) or "column 1" in str(e):
                raise RateLimitError(f"Yahoo Finance rate limit exceeded for {ticker} (empty response)") from e
            raise DataUnavailableError(
                f"Yahoo Finance returned invalid response for {ticker}: {e!s}"
            ) from e
        except Exception as e:
            # Check if it's a rate limit or network error
            error_msg = str(e).lower()
            if "too many requests" in error_msg or "429" in error_msg or "rate limit" in error_msg:
                raise RateLimitError(f"Yahoo Finance rate limit exceeded for {ticker}") from e
            if "timeout" in error_msg or "connection" in error_msg:
                raise NetworkError(f"Network error fetching {ticker}: {e!s}") from e
            raise NetworkError(f"Failed to connect to Yahoo Finance for {ticker}: {e!s}") from e

        if not info or not info.get("symbol"):
            raise InvalidTickerError(f"Invalid ticker symbol or no data found: {ticker}")

        # Check if we have at least some meaningful data
        has_price = info.get("currentPrice") is not None or info.get("regularMarketPrice") is not None
        has_name = info.get("longName") is not None or info.get("shortName") is not None

        if not has_price and not has_name:
            raise DataUnavailableError(
                f"No market data available for ticker: {ticker}"
            )

        # Use currentPrice or regularMarketPrice as fallback
        current_price = info.get("currentPrice") or info.get("regularMarketPrice")

        return MarketDataResponse(
            ticker=ticker,
            company_name=info.get("longName") or info.get("shortName") or None,
            current_price=current_price,
            previous_close=info.get("previousClose"),
            market_cap=info.get("marketCap"),
            pe_ratio=info.get("trailingPE"),
            volume=info.get("volume"),
            fifty_two_week_high=info.get("fiftyTwoWeekHigh"),
            fifty_two_week_low=info.get("fiftyTwoWeekLow"),
            sector=info.get("sector"),
            industry=info.get("industry"),
            data_as_of=datetime.now(UTC),
        )


# Singleton instance
market_data_service = MarketDataService()
