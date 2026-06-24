# EquiPilot AI - yfinance Tool
# LangGraph tool wrapper for yfinance market data

from typing import Dict, List, Any, Optional
from langchain_core.tools import tool
from backend.services.market_service import market_service
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class YFinanceTool:
    """LangGraph-compatible tool for yfinance market data."""

    @tool
    async def get_market_data(
        tickers: List[str],
        period: str = "1y",
        include_fundamentals: bool = True,
        include_technicals: bool = False,
    ) -> Dict[str, Any]:
        """
        Fetch market data for given tickers.

        Args:
            tickers: List of ticker symbols (e.g., ["AAPL", "MSFT"])
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            include_fundamentals: Include fundamental data
            include_technicals: Include technical indicators

        Returns:
            Dictionary with market data for each ticker
        """
        logger.info("Tool: get_market_data", tickers=tickers)

        try:
            data = await market_service.get_market_data(tickers, period)

            # Convert to serializable format
            result = {}
            for ticker, md in data.items():
                result[ticker] = {
                    "ticker": md.ticker,
                    "company_name": md.company_name,
                    "currency": md.currency,
                    "exchange": md.exchange,
                    "sector": md.sector,
                    "industry": md.industry,
                    "current_price": md.current_price,
                    "previous_close": md.previous_close,
                    "change": md.change,
                    "change_percent": md.change_percent,
                    "fundamentals": md.fundamentals.model_dump() if md.fundamentals else None,
                    "technicals": md.technicals.model_dump() if md.technicals else None,
                    "data_as_of": md.data_as_of.isoformat() if md.data_as_of else None,
                }

            return result

        except Exception as e:
            logger.error("Tool error: get_market_data", error=str(e))
            return {"error": str(e)}

    @tool
    async def get_fundamentals(tickers: List[str]) -> Dict[str, Any]:
        """
        Fetch fundamental data for tickers.

        Args:
            tickers: List of ticker symbols

        Returns:
            Dictionary with fundamental data for each ticker
        """
        logger.info("Tool: get_fundamentals", tickers=tickers)

        try:
            data = await market_service.get_fundamentals(tickers)
            result = {}
            for ticker, fund in data.items():
                result[ticker] = fund.model_dump() if fund else None
            return result
        except Exception as e:
            logger.error("Tool error: get_fundamentals", error=str(e))
            return {"error": str(e)}


# Export tool functions for LangGraph
get_market_data = YFinanceTool.get_market_data
get_fundamentals = YFinanceTool.get_fundamentals