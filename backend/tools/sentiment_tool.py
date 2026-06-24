# EquiPilot AI - Sentiment Tool
# LangGraph tool wrapper for sentiment analysis

from typing import List, Dict, Any
from langchain_core.tools import tool
from backend.services.sentiment_service import sentiment_service
from backend.schemas.news import NewsArticle
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class SentimentTool:
    """LangGraph-compatible tool for sentiment analysis."""

    @tool
    async def analyze_sentiment(
        articles: List[Dict[str, Any]],
        tickers: List[str],
    ) -> Dict[str, Any]:
        """
        Analyze sentiment of news articles.

        Args:
            articles: List of article dictionaries with title, description, content, url
            tickers: Tickers of interest

        Returns:
            Dictionary with sentiment analysis results
        """
        logger.info("Tool: analyze_sentiment", article_count=len(articles))

        try:
            # Convert dict articles to NewsArticle objects
            news_articles = []
            for a in articles:
                news_articles.append(NewsArticle(
                    title=a.get("title", ""),
                    description=a.get("description"),
                    content=a.get("content"),
                    url=a.get("url", ""),
                    source=a.get("source", "Unknown"),
                    author=a.get("author"),
                    published_at=a.get("published_at"),
                    category=a.get("category"),
                ))

            analysis = await sentiment_service.analyze_articles(news_articles, tickers)

            return {
                "overall_sentiment": {
                    "label": analysis.overall_sentiment.label,
                    "score": analysis.overall_sentiment.score,
                    "confidence": analysis.overall_sentiment.confidence,
                },
                "ticker_sentiments": {
                    ticker: {
                        "label": sent.label,
                        "score": sent.score,
                        "confidence": sent.confidence,
                    }
                    for ticker, sent in analysis.ticker_sentiments.items()
                },
                "key_themes": analysis.key_themes,
                "statistics": {
                    "total_articles": analysis.total_articles,
                    "positive_count": analysis.positive_count,
                    "negative_count": analysis.negative_count,
                    "neutral_count": analysis.neutral_count,
                    "average_confidence": analysis.average_confidence,
                },
                "date_range": {
                    "from": analysis.date_from.isoformat() if analysis.date_from else None,
                    "to": analysis.date_to.isoformat() if analysis.date_to else None,
                },
            }

        except Exception as e:
            logger.error("Tool error: analyze_sentiment", error=str(e))
            return {"error": str(e)}


# Export tool function for LangGraph
analyze_sentiment = SentimentTool.analyze_sentiment