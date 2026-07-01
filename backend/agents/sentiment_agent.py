# EquiPilot AI - Sentiment Agent
# Sentiment analysis agent


from backend.schemas.news import NewsArticle
from backend.schemas.sentiment import SentimentAnalysis
from backend.services.sentiment_service import sentiment_service
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class SentimentAgent:
    """Agent for performing sentiment analysis on news articles."""

    def __init__(self):
        self.service = sentiment_service

    async def analyze(
        self,
        articles: list[NewsArticle],
        tickers: list[str],
    ) -> SentimentAnalysis:
        """
        Analyze sentiment of news articles.

        Args:
            articles: List of news articles
            tickers: Tickers of interest

        Returns:
            SentimentAnalysis with aggregated results
        """
        logger.info("Analyzing sentiment", article_count=len(articles), tickers=tickers)

        if not articles:
            from backend.schemas.sentiment import SentimentScore
            neutral = SentimentScore(label="neutral", score=0.0, confidence=0.0)
            return SentimentAnalysis(
                overall_sentiment=neutral,
                article_sentiments=[],
                ticker_sentiments={t: neutral for t in tickers},
                key_themes=[],
                total_articles=0,
            )

        return await self.service.analyze_articles(articles, tickers)
