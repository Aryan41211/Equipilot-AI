# EquiPilot AI - News Service
# Wrapper for financial news API integration

from datetime import datetime, timedelta

import httpx

from backend.config import settings
from backend.schemas.news import NewsArticle, NewsResponse
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class NewsService:
    """Service for fetching financial news from various providers."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=settings.news_api_timeout)
        self.provider = settings.news_api_provider
        self.api_key = settings.news_api_key

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def fetch_news(
        self,
        tickers: list[str],
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 20,
    ) -> NewsResponse:
        """
        Fetch news articles for given tickers.

        Args:
            tickers: List of ticker symbols
            date_from: Start date for news search
            date_to: End date for news search
            limit: Maximum number of articles to return

        Returns:
            NewsResponse with articles and metadata
        """
        if not settings.enable_news_fetching:
            return NewsResponse(
                query="",
                tickers=tickers,
                articles=[],
                total_results=0,
                provider=self.provider,
                errors=["News fetching is disabled"],
            )

        if not self.api_key:
            return NewsResponse(
                query="",
                tickers=tickers,
                articles=[],
                total_results=0,
                provider=self.provider,
                errors=["News API key not configured"],
            )

        # Set default date range
        if date_to is None:
            date_to = datetime.utcnow()
        if date_from is None:
            date_from = date_to - timedelta(days=settings.news_lookback_days)

        # Build search query
        query = " OR ".join([f'"{ticker}"' for ticker in tickers])

        # Fetch from provider
        try:
            if self.provider == "newsapi":
                return await self._fetch_newsapi(query, tickers, date_from, date_to, limit)
            elif self.provider == "alphavantage":
                return await self._fetch_alphavantage(query, tickers, date_from, date_to, limit)
            elif self.provider == "finnhub":
                return await self._fetch_finnhub(query, tickers, date_from, date_to, limit)
            else:
                return NewsResponse(
                    query=query,
                    tickers=tickers,
                    articles=[],
                    total_results=0,
                    provider=self.provider,
                    errors=[f"Unknown provider: {self.provider}"],
                )
        except Exception as e:
            logger.error("News fetch failed", error=str(e))
            return NewsResponse(
                query=query,
                tickers=tickers,
                articles=[],
                total_results=0,
                provider=self.provider,
                errors=[str(e)],
            )

    async def _fetch_newsapi(
        self,
        query: str,
        tickers: list[str],
        date_from: datetime,
        date_to: datetime,
        limit: int,
    ) -> NewsResponse:
        """Fetch from NewsAPI.org."""
        params = {
            "q": query,
            "from": date_from.strftime("%Y-%m-%d"),
            "to": date_to.strftime("%Y-%m-%d"),
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": min(limit, 100),
            "apiKey": self.api_key,
        }

        response = await self.client.get(
            "https://newsapi.org/v2/everything",
            params=params,
        )
        response.raise_for_status()
        data = response.json()

        articles = []
        for item in data.get("articles", []):
            articles.append(
                NewsArticle(
                    title=item.get("title", ""),
                    description=item.get("description"),
                    content=item.get("content"),
                    url=item.get("url", ""),
                    source=item.get("source", {}).get("name", "Unknown"),
                    author=item.get("author"),
                    published_at=datetime.fromisoformat(
                        item.get("publishedAt", "").replace("Z", "+00:00")
                    ),
                    category=item.get("category"),
                    provider="newsapi",
                )
            )

        return NewsResponse(
            query=query,
            tickers=tickers,
            articles=articles,
            total_results=data.get("totalResults", 0),
            date_from=date_from,
            date_to=date_to,
            provider="newsapi",
        )

    async def _fetch_alphavantage(
        self,
        query: str,
        tickers: list[str],
        date_from: datetime,
        date_to: datetime,
        limit: int,
    ) -> NewsResponse:
        """Fetch from Alpha Vantage."""
        # Alpha Vantage uses different endpoint structure
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": ",".join(tickers),
            "time_from": date_from.strftime("%Y%m%dT%H%M"),
            "time_to": date_to.strftime("%Y%m%dT%H%M"),
            "limit": limit,
            "apikey": self.api_key,
        }

        response = await self.client.get(
            "https://www.alphavantage.co/query",
            params=params,
        )
        response.raise_for_status()
        data = response.json()

        articles = []
        for item in data.get("feed", []):
            articles.append(
                NewsArticle(
                    title=item.get("title", ""),
                    description=item.get("summary"),
                    content=item.get("summary"),
                    url=item.get("url", ""),
                    source=item.get("source", "Alpha Vantage"),
                    author=item.get("authors", [None])[0] if item.get("authors") else None,
                    published_at=datetime.fromisoformat(
                        item.get("time_published", "").replace("Z", "+00:00")
                    ),
                    category=item.get("category_within_source"),
                    provider="alphavantage",
                )
            )

        return NewsResponse(
            query=query,
            tickers=tickers,
            articles=articles,
            total_results=len(articles),
            date_from=date_from,
            date_to=date_to,
            provider="alphavantage",
        )

    async def _fetch_finnhub(
        self,
        query: str,
        tickers: list[str],
        date_from: datetime,
        date_to: datetime,
        limit: int,
    ) -> NewsResponse:
        """Fetch from Finnhub."""
        # Finnhub requires individual ticker calls
        all_articles = []

        for ticker in tickers:
            params = {
                "symbol": ticker,
                "from": date_from.strftime("%Y-%m-%d"),
                "to": date_to.strftime("%Y-%m-%d"),
                "token": self.api_key,
            }

            response = await self.client.get(
                "https://finnhub.io/api/v1/company-news",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            for item in data[: limit // len(tickers) if len(tickers) > 0 else limit]:
                all_articles.append(
                    NewsArticle(
                        title=item.get("headline", ""),
                        description=item.get("summary"),
                        content=item.get("summary"),
                        url=item.get("url", ""),
                        source=item.get("source", "Finnhub"),
                        author=None,
                        published_at=datetime.fromtimestamp(item.get("datetime", 0)),
                        category=item.get("category"),
                        provider="finnhub",
                    )
                )

        # Sort by date descending
        all_articles.sort(key=lambda x: x.published_at, reverse=True)
        all_articles = all_articles[:limit]

        return NewsResponse(
            query=query,
            tickers=tickers,
            articles=all_articles,
            total_results=len(all_articles),
            date_from=date_from,
            date_to=date_to,
            provider="finnhub",
        )

    async def get_market_news(
        self,
        category: str = "general",
        limit: int = 20,
    ) -> NewsResponse:
        """Fetch general market news."""
        if self.provider != "newsapi":
            # Only NewsAPI supports general market news easily
            return NewsResponse(
                query=f"market {category}",
                tickers=[],
                articles=[],
                total_results=0,
                provider=self.provider,
                errors=["General market news only supported with NewsAPI"],
            )

        params = {
            "category": "business",
            "country": "us",
            "pageSize": limit,
            "apiKey": self.api_key,
        }

        response = await self.client.get(
            "https://newsapi.org/v2/top-headlines",
            params=params,
        )
        response.raise_for_status()
        data = response.json()

        articles = []
        for item in data.get("articles", []):
            articles.append(
                NewsArticle(
                    title=item.get("title", ""),
                    description=item.get("description"),
                    content=item.get("content"),
                    url=item.get("url", ""),
                    source=item.get("source", {}).get("name", "Unknown"),
                    author=item.get("author"),
                    published_at=datetime.fromisoformat(
                        item.get("publishedAt", "").replace("Z", "+00:00")
                    ),
                    category=item.get("category"),
                    provider="newsapi",
                )
            )

        return NewsResponse(
            query=f"market {category}",
            tickers=[],
            articles=articles,
            total_results=data.get("totalResults", 0),
            provider="newsapi",
        )


# Lazy singleton - created on first use
_news_service: NewsService | None = None


def get_news_service() -> NewsService:
    """Get or create news service singleton lazily."""
    global _news_service
    if _news_service is None:
        _news_service = NewsService()
    return _news_service
