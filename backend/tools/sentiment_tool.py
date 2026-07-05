from __future__ import annotations

from datetime import datetime
from typing import Any

from langchain_core.tools import tool

from backend.exceptions.sentiment_exceptions import SentimentError
from backend.schemas.news import NewsArticle
from backend.services.sentiment_service import get_sentiment_service
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Module-level singleton expected by tests (tests patch `module.sentiment_service`).
sentiment_service = get_sentiment_service()


async def _analyze_sentiment_impl(
    articles: list[dict[str, Any]],
    tickers: list[str] | None = None,
) -> dict[str, Any]:
    """
    Analyze sentiment for provided normalized news articles.

    Returns:
        {
          "ok": bool,
          "result": <SentimentAnalysis dict> | null,
          "error": {"type": "...", "message": "..."} | null
        }
    """
    tickers = tickers or []

    try:
        normalized_articles: list[NewsArticle] = []
        for a in articles:
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
        logger.warning("Sentiment tool failed", error=str(e))
        return {
            "ok": False,
            "result": None,
            "error": {"type": e.__class__.__name__, "message": str(e)},
        }
    except Exception as e:
        logger.error("Unexpected sentiment tool error", error=str(e))
        return {
            "ok": False,
            "result": None,
            "error": {"type": "UnexpectedError", "message": str(e)},
        }


@tool
async def analyze_sentiment(
    articles: list[dict[str, Any]],
    tickers: list[str] | None = None,
) -> dict[str, Any]:
    """Analyze sentiment for provided normalized news articles and return a contract-stable response."""
    return await _analyze_sentiment_impl(articles=articles, tickers=tickers)


class SentimentTool:
    """LangGraph-compatible tool wrapper for sentiment analysis."""

    def __init__(self) -> None:
        # Tests expect `SentimentTool().analyze_sentiment` to be a LangChain tool.
        self.analyze_sentiment = analyze_sentiment
