# EquiPilot AI - News Tool
# LangGraph tool wrapper for news API

from datetime import datetime
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from backend.services.news_service import news_service
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class NewsTool:
    """LangGraph-compatible tool for financial news."""

    @tool
    async def fetch_news(
        tickers: List[str],
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Fetch news articles for given tickers.

        Args:
            tickers: List of ticker symbols
            date_from: Start date (ISO format, e.g., "2024-01-01")
            date_to: End date (ISO format)
            limit: Maximum articles to return

        Returns:
            Dictionary with articles and metadata
        """
        logger.info("Tool: fetch_news", tickers=tickers, limit=limit)

        try:
            # Parse dates
            dt_from = datetime.fromisoformat(date_from) if date_from else None
            dt_to = datetime.fromisoformat(date_to) if date_to else None

            response = await news_service.fetch_news(tickers, dt_from, dt_to, limit)

            return {
                "query": response.query,
                "tickers": response.tickers,
                "articles": [
                    {
                        "title": a.title,
                        "description": a.description,
                        "content": a.content,
                        "url": str(a.url),
                        "source": a.source,
                        "author": a.author,
                        "published_at": a.published_at.isoformat(),
                        "category": a.category,
                        "relevance_score": a.relevance_score,
                        "tickers_mentioned": a.tickers_mentioned,
                    }
                    for a in response.articles
                ],
                "total_results": response.total_results,
                "provider": response.provider,
                "errors": response.errors,
            }

        except Exception as e:
            logger.error("Tool error: fetch_news", error=str(e))
            return {"error": str(e)}

    @tool
    async def fetch_market_news(
        category: str = "general",
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Fetch general market news.

        Args:
            category: News category
            limit: Maximum articles

        Returns:
            Dictionary with market news articles
        """
        logger.info("Tool: fetch_market_news", category=category)

        try:
            response = await news_service.get_market_news(category, limit)

            return {
                "query": response.query,
                "articles": [
                    {
                        "title": a.title,
                        "description": a.description,
                        "content": a.content,
                        "url": str(a.url),
                        "source": a.source,
                        "author": a.author,
                        "published_at": a.published_at.isoformat(),
                        "category": a.category,
                    }
                    for a in response.articles
                ],
                "total_results": response.total_results,
                "provider": response.provider,
            }

        except Exception as e:
            logger.error("Tool error: fetch_market_news", error=str(e))
            return {"error": str(e)}


# Export tool functions for LangGraph
fetch_news = NewsTool.fetch_news
fetch_market_news = NewsTool.fetch_market_news