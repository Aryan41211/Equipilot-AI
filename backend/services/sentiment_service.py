# EquiPilot AI - Sentiment Service
# Sentiment analysis orchestration

from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.services.llm_service import get_llm_service
from backend.schemas.sentiment import (
    SentimentAnalysis,
    SentimentScore,
    ArticleSentiment,
)
from backend.schemas.news import NewsArticle
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class SentimentService:
    """Service for orchestrating sentiment analysis on news articles."""

    def __init__(self):
        self.llm = get_llm_service()

    async def analyze_articles(
        self,
        articles: List[NewsArticle],
        tickers: List[str],
    ) -> SentimentAnalysis:
        """
        Analyze sentiment across multiple news articles.

        Args:
            articles: List of news articles to analyze
            tickers: Tickers of interest for focused analysis

        Returns:
            Aggregated SentimentAnalysis
        """
        if not articles:
            return self._empty_analysis(tickers)

        logger.info("Starting sentiment analysis", article_count=len(articles))

        # Analyze each article
        article_sentiments = []
        for article in articles:
            try:
                sentiment = await self._analyze_single_article(article, tickers)
                article_sentiments.append(sentiment)
            except Exception as e:
                logger.warning(
                    "Failed to analyze article",
                    article_title=article.title,
                    error=str(e),
                )

        # Aggregate results
        return self._aggregate_sentiments(article_sentiments, tickers, articles)

    async def _analyze_single_article(
        self,
        article: NewsArticle,
        tickers: List[str],
    ) -> ArticleSentiment:
        """Analyze sentiment for a single article."""
        # Combine title and description for analysis
        text = f"{article.title}\n\n{article.description or ''}\n\n{article.content or ''}"

        # Call LLM for sentiment
        result = await self.llm.analyze_sentiment(text, tickers)

        # Parse overall sentiment
        overall = result.get("overall", {})
        overall_sentiment = SentimentScore(
            label=overall.get("label", "neutral"),
            score=overall.get("score", 0.0),
            confidence=overall.get("confidence", 0.5),
        )

        # Parse ticker sentiments
        ticker_sentiments = {}
        for ticker, data in result.get("ticker_sentiments", {}).items():
            ticker_sentiments[ticker] = SentimentScore(
                label=data.get("label", "neutral"),
                score=data.get("score", 0.0),
                confidence=data.get("confidence", 0.5),
            )

        return ArticleSentiment(
            article_id=str(hash(article.url)),
            article_title=article.title,
            article_url=str(article.url),
            published_at=article.published_at,
            sentiment=overall_sentiment,
            ticker_sentiments=ticker_sentiments,
        )

    def _aggregate_sentiments(
        self,
        article_sentiments: List[ArticleSentiment],
        tickers: List[str],
        articles: List[NewsArticle],
    ) -> SentimentAnalysis:
        """Aggregate individual article sentiments into overall analysis."""
        if not article_sentiments:
            return self._empty_analysis(tickers)

        # Overall sentiment (weighted by confidence)
        total_weight = sum(s.sentiment.confidence for s in article_sentiments)
        if total_weight > 0:
            weighted_score = sum(
                s.sentiment.score * s.sentiment.confidence for s in article_sentiments
            ) / total_weight
            avg_confidence = total_weight / len(article_sentiments)
        else:
            weighted_score = 0.0
            avg_confidence = 0.0

        # Determine label
        if weighted_score > 0.1:
            overall_label = "positive"
        elif weighted_score < -0.1:
            overall_label = "negative"
        else:
            overall_label = "neutral"

        overall_sentiment = SentimentScore(
            label=overall_label,
            score=weighted_score,
            confidence=avg_confidence,
        )

        # Per-ticker aggregation
        ticker_sentiments = {}
        for ticker in tickers:
            ticker_scores = []
            ticker_confidences = []
            for s in article_sentiments:
                if ticker in s.ticker_sentiments:
                    ts = s.ticker_sentiments[ticker]
                    ticker_scores.append(ts.score * ts.confidence)
                    ticker_confidences.append(ts.confidence)

            if ticker_confidences:
                total_ticker_weight = sum(ticker_confidences)
                weighted_ticker_score = sum(ticker_scores) / total_ticker_weight
                avg_ticker_confidence = total_ticker_weight / len(ticker_confidences)

                if weighted_ticker_score > 0.1:
                    label = "positive"
                elif weighted_ticker_score < -0.1:
                    label = "negative"
                else:
                    label = "neutral"

                ticker_sentiments[ticker] = SentimentScore(
                    label=label,
                    score=weighted_ticker_score,
                    confidence=avg_ticker_confidence,
                )

        # Count sentiments
        positive_count = sum(1 for s in article_sentiments if s.sentiment.label == "positive")
        negative_count = sum(1 for s in article_sentiments if s.sentiment.label == "negative")
        neutral_count = sum(1 for s in article_sentiments if s.sentiment.label == "neutral")

        # Extract key themes (simplified - could use LLM for better extraction)
        key_themes = self._extract_themes(article_sentiments, articles)

        # Date range
        dates = [a.published_at for a in articles if a.published_at]
        date_from = min(dates) if dates else None
        date_to = max(dates) if dates else None

        return SentimentAnalysis(
            overall_sentiment=overall_sentiment,
            article_sentiments=article_sentiments,
            ticker_sentiments=ticker_sentiments,
            key_themes=key_themes,
            total_articles=len(article_sentiments),
            positive_count=positive_count,
            negative_count=negative_count,
            neutral_count=neutral_count,
            average_confidence=avg_confidence,
            date_from=date_from,
            date_to=date_to,
            analyzed_at=datetime.utcnow(),
        )

    def _extract_themes(
        self,
        article_sentiments: List[ArticleSentiment],
        articles: List[NewsArticle],
    ) -> List[Dict[str, Any]]:
        """Extract key themes from articles (placeholder implementation)."""
        # TODO: Implement proper theme extraction using LLM
        # For now, return empty list
        return []

    def _empty_analysis(self, tickers: List[str]) -> SentimentAnalysis:
        """Return empty sentiment analysis."""
        neutral = SentimentScore(label="neutral", score=0.0, confidence=0.0)
        ticker_sentiments = {t: neutral for t in tickers}

        return SentimentAnalysis(
            overall_sentiment=neutral,
            article_sentiments=[],
            ticker_sentiments=ticker_sentiments,
            key_themes=[],
            total_articles=0,
            positive_count=0,
            negative_count=0,
            neutral_count=0,
            average_confidence=0.0,
        )


# Singleton instance
sentiment_service = SentimentService()