# EquiPilot AI - News Agent
# News retrieval agent

from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.services.news_service import news_service
from backend.schemas.news import NewsArticle, NewsResponse
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class NewsAgent:
    """Agent for fetching financial news."""

    def __init__(self):
        self.service = news_service

    async def fetch(
        self,
        tickers: List[str],
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 20,
    ) -> NewsResponse:
        """
        Fetch news for tickers.

        Args:
            tickers: List of ticker symbols
            date_from: Start date for news
            date_to: End date for news
            limit: Maximum articles to return

        Returns:
            NewsResponse with articles
        """
        logger.info("Fetching news", tickers=tickers, limit=limit)

        try:
            return await self.service.fetch_news(tickers, date_from, date_to, limit)
        except Exception as e:
            logger.error("News fetch failed", error=str(e))
            return NewsResponse(
                query="",
                tickers=tickers,
                articles=[],
                total_results=0,
                date_from=date_from,
                date_to=date_to,
                provider="error",
                errors=[str(e)],
            )

    async def fetch_market_news(
        self,
        category: str = "general",
        limit: int = 20,
    ) -> NewsResponse:
        """Fetch general market news."""
        return await self.service.get_market_news(category, limit)

    async def close(self):
        """Close the news service."""
        await self.service.close()