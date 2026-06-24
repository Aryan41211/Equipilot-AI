# EquiPilot AI - Market Data Service
# Wrapper around yfinance for market data retrieval

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import yfinance as yf
import pandas as pd

from backend.config import settings
from backend.schemas.market_data import (
    MarketData,
    PriceData,
    FundamentalsData,
    TechnicalIndicators,
)
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class MarketService:
    """Service for fetching and processing market data from yfinance."""

    def __init__(self):
        self.cache: Dict[str, Any] = {}
        self.cache_ttl = settings.yfinance_cache_ttl

    async def get_market_data(
        self,
        tickers: List[str],
        period: str = "1y",
        interval: str = "1d",
    ) -> Dict[str, MarketData]:
        """
        Fetch comprehensive market data for multiple tickers.

        Args:
            tickers: List of ticker symbols
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)

        Returns:
            Dictionary mapping ticker to MarketData
        """
        results = {}

        for ticker in tickers:
            try:
                data = await self._fetch_ticker_data(ticker, period, interval)
                results[ticker] = data
            except Exception as e:
                logger.error("Failed to fetch market data", ticker=ticker, error=str(e))
                results[ticker] = MarketData(
                    ticker=ticker,
                    data_as_of=datetime.utcnow(),
                    source="yfinance",
                )

        return results

    async def _fetch_ticker_data(
        self,
        ticker: str,
        period: str,
        interval: str,
    ) -> MarketData:
        """Fetch all data for a single ticker."""
        cache_key = f"{ticker}:{period}:{interval}"

        # Check cache
        if settings.enable_caching and cache_key in self.cache:
            cached = self.cache[cache_key]
            if (datetime.utcnow() - cached["timestamp"]).seconds < self.cache_ttl:
                logger.debug("Cache hit", ticker=ticker)
                return cached["data"]

        # Fetch from yfinance (run in executor to avoid blocking)
        loop = asyncio.get_event_loop()
        yf_ticker = await loop.run_in_executor(None, yf.Ticker, ticker)

        # Get info and history concurrently
        info_task = loop.run_in_executor(None, lambda: yf_ticker.info)
        history_task = loop.run_in_executor(
            None,
            lambda: yf_ticker.history(period=period, interval=interval),
        )

        info, history = await asyncio.gather(info_task, history_task)

        # Build MarketData object
        market_data = MarketData(
            ticker=ticker.upper(),
            company_name=info.get("longName") or info.get("shortName"),
            currency=info.get("currency", "USD"),
            exchange=info.get("exchange"),
            sector=info.get("sector"),
            industry=info.get("industry"),
            current_price=info.get("currentPrice") or info.get("regularMarketPrice"),
            previous_close=info.get("previousClose") or info.get("regularMarketPreviousClose"),
            price_history=self._parse_price_history(history),
            fundamentals=self._parse_fundamentals(info),
            technicals=self._calculate_technicals(history),
            data_as_of=datetime.utcnow(),
        )

        # Calculate change
        if market_data.current_price and market_data.previous_close:
            market_data.change = market_data.current_price - market_data.previous_close
            market_data.change_percent = (
                market_data.change / market_data.previous_close
            ) * 100

        # Cache result
        if settings.enable_caching:
            self.cache[cache_key] = {
                "data": market_data,
                "timestamp": datetime.utcnow(),
            }

        return market_data

    def _parse_price_history(self, history: pd.DataFrame) -> List[PriceData]:
        """Convert yfinance history DataFrame to PriceData list."""
        if history.empty:
            return []

        price_data = []
        for date, row in history.iterrows():
            price_data.append(
                PriceData(
                    date=date.to_pydatetime() if hasattr(date, "to_pydatetime") else date,
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    adjusted_close=float(row.get("Adj Close", row["Close"])),
                    volume=int(row["Volume"]),
                )
            )
        return price_data

    def _parse_fundamentals(self, info: Dict[str, Any]) -> Optional[FundamentalsData]:
        """Extract fundamental data from yfinance info."""
        if not info:
            return None

        return FundamentalsData(
            market_cap=info.get("marketCap"),
            enterprise_value=info.get("enterpriseValue"),
            pe_ratio=info.get("trailingPE"),
            forward_pe=info.get("forwardPE"),
            peg_ratio=info.get("pegRatio"),
            price_to_book=info.get("priceToBook"),
            price_to_sales=info.get("priceToSalesTrailing12Months"),
            ev_to_revenue=info.get("enterpriseToRevenue"),
            ev_to_ebitda=info.get("enterpriseToEbitda"),
            profit_margin=info.get("profitMargins"),
            operating_margin=info.get("operatingMargins"),
            return_on_assets=info.get("returnOnAssets"),
            return_on_equity=info.get("returnOnEquity"),
            total_cash=info.get("totalCash"),
            total_debt=info.get("totalDebt"),
            current_ratio=info.get("currentRatio"),
            debt_to_equity=info.get("debtToEquity"),
            revenue_growth=info.get("revenueGrowth"),
            earnings_growth=info.get("earningsGrowth"),
            dividend_yield=info.get("dividendYield"),
            payout_ratio=info.get("payoutRatio"),
            currency=info.get("currency", "USD"),
            last_updated=datetime.utcnow(),
        )

    def _calculate_technicals(self, history: pd.DataFrame) -> Optional[TechnicalIndicators]:
        """Calculate technical indicators from price history."""
        if history.empty or len(history) < 20:
            return None

        close = history["Close"]
        volume = history["Volume"]

        # Simple Moving Averages
        sma_20 = close.rolling(20).mean().iloc[-1] if len(close) >= 20 else None
        sma_50 = close.rolling(50).mean().iloc[-1] if len(close) >= 50 else None
        sma_200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else None

        # Exponential Moving Averages
        ema_12 = close.ewm(span=12, adjust=False).mean().iloc[-1]
        ema_26 = close.ewm(span=26, adjust=False).mean().iloc[-1]

        # MACD
        macd = ema_12 - ema_26
        macd_signal = macd.ewm(span=9, adjust=False).mean().iloc[-1]
        macd_histogram = macd - macd_signal

        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # Bollinger Bands
        sma_20_bb = close.rolling(20).mean()
        std_20 = close.rolling(20).std()

        return TechnicalIndicators(
            sma_20=float(sma_20) if sma_20 else None,
            sma_50=float(sma_50) if sma_50 else None,
            sma_200=float(sma_200) if sma_200 else None,
            ema_12=float(ema_12),
            ema_26=float(ema_26),
            rsi_14=float(rsi.iloc[-1]) if not rsi.empty else None,
            macd=float(macd.iloc[-1]),
            macd_signal=float(macd_signal),
            macd_histogram=float(macd_histogram.iloc[-1]),
            bollinger_upper=float(sma_20_bb.iloc[-1] + 2 * std_20.iloc[-1]),
            bollinger_middle=float(sma_20_bb.iloc[-1]),
            bollinger_lower=float(sma_20_bb.iloc[-1] - 2 * std_20.iloc[-1]),
            volume_sma_20=float(volume.rolling(20).mean().iloc[-1]) if len(volume) >= 20 else None,
        )

    async def get_fundamentals(self, tickers: List[str]) -> Dict[str, FundamentalsData]:
        """Fetch only fundamental data for tickers."""
        results = {}
        for ticker in tickers:
            try:
                loop = asyncio.get_event_loop()
                yf_ticker = await loop.run_in_executor(None, yf.Ticker, ticker)
                info = await loop.run_in_executor(None, lambda: yf_ticker.info)
                results[ticker] = self._parse_fundamentals(info)
            except Exception as e:
                logger.error("Failed to fetch fundamentals", ticker=ticker, error=str(e))
                results[ticker] = None
        return results

    async def search_tickers(self, query: str) -> List[Dict[str, str]]:
        """Search for tickers matching a query."""
        # TODO: Implement ticker search (yfinance doesn't have built-in search)
        # Could use Yahoo Finance search API or maintain a local ticker database
        return []


# Singleton instance
market_service = MarketService()