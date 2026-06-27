from __future__ import annotations

from typing import Any, Dict, List, Optional

from langchain_core.tools import tool

from backend.schemas.news import NewsArticle
from backend.services.sentiment_service import SentimentService
from backend.utils.logger import get_logger
from backend.exceptions.sentiment_exceptions import SentimentError

logger = get_logger(__name__)

# Singleton for existing patterns.
sentiment_service = SentimentService()


class SentimentTool:
    """LangGraph-compatible tool wrapper for sentiment analysis."""

    @tool
    async def analyze_sentiment(
        self,
        articles: List[Dict[str, Any]],
        tickers: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze sentiment for provided normalized news articles.

        Args:
            articles: List of normalized articles (expects keys compatible with NewsArticle)
            tickers: tickers to focus on

        Returns:
            Structured response contract:
            {
              "ok": bool,
              "result": <SentimentAnalysis dict> | null,
              "error": {"type": "...", "message": "..."} | null
            }
        """
        tickers = tickers or []

        try:
            normalized_articles: List[NewsArticle] = []
            for a in articles:
                # NewsArticle model tolerates extra fields? We pass only expected.
                normalized_articles.append(
                    NewsArticle(
                        title=a.get("title"),
                        description=a.get("description"),
                        content=a.get("content"),
                        url=a.get("url"),
                        source=a.get("source", ""),
                        author=a.get("author"),
                        published_at=a.get("published_at"),
                        category=a.get("category"),
                        relevance_score=a.get("relevance_score"),
                        tickers_mentioned=a.get("tickers_mentioned", []),
                        ticker=a.get("ticker"),
                    )
                )

            result = await sentiment_service.analyze_articles(
                normalized_articles,
                tickers=tickers,
            )
            return {"ok": True, "result": result.model_dump(), "error": None}
        except SentimentError as e:
            # Exception-to-response mapping; never propagate raw exceptions.
            logger.warning("Sentiment tool failed", error=str(e))
            return {
                "ok": False,
                "result": None,
                "error": {"type": e.__class__.__name__, "message": str(e)},
            }
        except Exception as e:
            # Ensure contract stability.
            logger.error("Unexpected sentiment tool error", error=str(e))
            return {
                "ok": False,
                "result": None,
                "error": {"type": "UnexpectedError", "message": str(e)},
            }


# Export tool functions for LangGraph
analyze_sentiment = SentimentTool().analyze_sentiment
