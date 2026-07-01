# EquiPilot AI - Market Agent
# Market data retrieval agent

from typing import Any

from backend.schemas.market_data import MarketData
from backend.services.market_service import market_service
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class MarketAgent:
    """Agent for fetching and processing market data."""

    def __init__(self):
        self.service = market_service

    async def fetch(
        self,
        tickers: list[str],
        period: str = "1y",
        include_fundamentals: bool = True,
        include_technicals: bool = False,
    ) -> dict[str, MarketData]:
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
                for _ticker, md in data.items():
                    md.fundamentals = None

            if not include_technicals:
                for _ticker, md in data.items():
                    md.technicals = None

            return data

        except Exception as e:
            logger.error("Market data fetch failed", error=str(e))
            # Return empty data for failed tickers
            return {
                ticker: MarketData(ticker=ticker, data_as_of=None)
                for ticker in tickers
            }

    async def fetch_fundamentals(self, tickers: list[str]) -> dict[str, Any]:
        """Fetch only fundamental data."""
        return await self.service.get_fundamentals(tickers)

    async def search_tickers(self, query: str) -> list[dict[str, str]]:
        """Search for tickers matching query."""
        return await self.service.search_tickers(query)
