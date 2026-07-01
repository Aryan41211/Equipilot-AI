from __future__ import annotations

from datetime import datetime
from typing import Any

from langchain_core.tools import tool

from backend.exceptions.sentiment_exceptions import SentimentError
from backend.schemas.news import NewsArticle
from backend.services.sentiment_service import SentimentService
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Singleton for existing patterns.
sentiment_service = SentimentService()


class SentimentTool:
    """LangGraph-compatible tool wrapper for sentiment analysis."""

    @tool
    async def analyze_sentiment(
        self: list[dict[str, Any]],
        tickers: list[str] | None = None,
    ) -> dict[str, Any]:
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
            normalized_articles: list[NewsArticle] = []
            for a in self:
                normalized_articles.append(
                    NewsArticle(
                        title=a.get("title", ""),
                        description=a.get("description"),
                        content=a.get("content"),
                        url=a.get("url") or "http://example.com/unknown",
                        source=a.get("source", ""),
                        author=a.get("author"),
                        published_at=a.get("published_at") or datetime.utcnow(),
                        category=a.get("category"),
                        relevance_score=a.get("relevance_score"),
                        tickers_mentioned=a.get("tickers_mentioned", []),
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
# NOTE: Expose the tool function itself (not a bound method) so calling conventions in tests/agents
# don't break due to BaseTool.__call__ kwarg handling.
analyze_sentiment = SentimentTool.analyze_sentiment
