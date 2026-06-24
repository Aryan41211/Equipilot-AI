# EquiPilot AI - Market Agent
# Market data retrieval agent

from typing import List, Dict, Any, Optional
from backend.services.market_service import market_service
from backend.schemas.market_data import MarketData
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class MarketAgent:
    """Agent for fetching and processing market data."""

    def __init__(self):
        self.service = market_service

    async def fetch(
        self,
        tickers: List[str],
        period: str = "1y",
        include_fundamentals: bool = True,
        include_technicals: bool = False,
    ) -> Dict[str, MarketData]:
        """
        Fetch market data for tickers.

        Args:
            tickers: List of ticker symbols
            period: Time period for price history
            include_fundamentals: Whether to include fundamental data
            include_technicals: Whether to include technical indicators

        Returns:
            Dictionary mapping ticker to MarketData
        """
        logger.info("Fetching market data", tickers=tickers, period=period)

        try:
            data = await self.service.get_market_data(tickers, period)

            # Optionally filter fields based on requirements
            if not include_fundamentals:
                for ticker, md in data.items():
                    md.fundamentals = None

            if not include_technicals:
                for ticker, md in data.items():
                    md.technicals = None

            return data

        except Exception as e:
            logger.error("Market data fetch failed", error=str(e))
            # Return empty data for failed tickers
            return {
                ticker: MarketData(ticker=ticker, data_as_of=None)
                for ticker in tickers
            }

    async def fetch_fundamentals(self, tickers: List[str]) -> Dict[str, Any]:
        """Fetch only fundamental data."""
        return await self.service.get_fundamentals(tickers)

    async def search_tickers(self, query: str) -> List[Dict[str, str]]:
        """Search for tickers matching query."""
        return await self.service.search_tickers(query)