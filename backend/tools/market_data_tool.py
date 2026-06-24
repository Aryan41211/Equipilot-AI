# EquiPilot AI - Market Data Tool
# Standalone tool for fetching stock information

from typing import Dict, Any
from backend.services.market_data_service import market_data_service
from backend.schemas.market_data_schema import MarketDataResponse
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class MarketDataTool:
    """Tool for fetching stock market data."""

    @staticmethod
    async def fetch_market_data(ticker: str) -> Dict[str, Any]:
        """
        Fetch market data for a single ticker symbol.

        Args:
            ticker: Stock ticker symbol (e.g., "RELIANCE.NS", "TCS.NS", "INFY.NS")

        Returns:
            Dictionary with market data or error message

        Example:
            >>> result = await MarketDataTool.fetch_market_data("RELIANCE.NS")
            >>> print(result["company_name"])
        """
        logger.info("Fetching market data", ticker=ticker)

        try:
            result = await market_data_service.get_stock_info(ticker)
            return result.model_dump()
        except ValueError as e:
            logger.warning("Invalid ticker provided", ticker=ticker, error=str(e))
            return {"error": str(e), "ticker": ticker}
        except Exception as e:
            logger.error("Market data fetch failed", ticker=ticker, error=str(e))
            return {"error": f"Failed to fetch data: {str(e)}", "ticker": ticker}


# Convenience function for direct import
async def fetch_market_data(ticker: str) -> Dict[str, Any]:
    """Fetch market data for a ticker symbol."""
    return await MarketDataTool.fetch_market_data(ticker)