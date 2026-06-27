# EquiPilot AI - Market Data Tool
# Standalone tool for fetching stock information

from typing import Dict, Any
from backend.services.market_data_service import (
    market_data_service,
    InvalidTickerError,
    NetworkError,
    DataUnavailableError,
    RateLimitError,
    MarketDataServiceError,
)
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
        except InvalidTickerError as e:
            logger.warning("Invalid ticker provided", ticker=ticker, error=str(e))
            return {"error": str(e), "ticker": ticker, "error_type": "invalid_ticker"}
        except DataUnavailableError as e:
            logger.warning("Market data unavailable", ticker=ticker, error=str(e))
            return {"error": str(e), "ticker": ticker, "error_type": "data_unavailable"}
        except RateLimitError as e:
            logger.warning("Rate limit exceeded fetching market data", ticker=ticker, error=str(e))
            return {"error": str(e), "ticker": ticker, "error_type": "rate_limit"}
        except NetworkError as e:
            logger.error("Network error fetching market data", ticker=ticker, error=str(e))
            return {"error": str(e), "ticker": ticker, "error_type": "network_error"}
        except MarketDataServiceError as e:
            logger.error("Market data service error", ticker=ticker, error=str(e))
            return {"error": str(e), "ticker": ticker, "error_type": "service_error"}
        except Exception as e:
            logger.error("Unexpected market data fetch error", ticker=ticker, error=str(e))
            return {"error": f"Unexpected error: {str(e)}", "ticker": ticker, "error_type": "unexpected_error"}


# Convenience function for direct import
async def fetch_market_data(ticker: str) -> Dict[str, Any]:
    """Fetch market data for a ticker symbol."""
    return await MarketDataTool.fetch_market_data(ticker)