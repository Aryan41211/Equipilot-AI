from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from backend.exceptions.sentiment_exceptions import (
    SentimentMalformedResponseError,
    SentimentProviderError,
    SentimentTimeoutError,
    SentimentValidationError,
)
from backend.schemas.news import NewsArticle
from backend.services.sentiment_service import SentimentService


def _news_article(*, title: str, url: str = "https://example.com/1") -> NewsArticle:
    return NewsArticle(
        title=title,
        description=None,
        content=None,
        url=str(url),
        source="example",
        author=None,
        published_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )


@pytest.mark.asyncio
async def test_sentiment_service_successful_analysis():
    service = SentimentService(max_retries=0)

    llm_payload = {
        "overall": {"label": "positive", "score": 0.6, "confidence": 0.7},
        "ticker_sentiments": {
            "AAPL": {"label": "positive", "score": 0.5, "confidence": 0.8},
        },
        "key_themes": [
            {"theme": "earnings", "sentiment": "positive", "relevance": 0.9},
        ],
    }

    with patch.object(service, "llm", autospec=True) as llm_mock:
        llm_mock.analyze_sentiment = AsyncMock(return_value=llm_payload)

        articles = [_news_article(title="AAPL beats earnings estimates")]
        result = await service.analyze_articles(articles=articles, tickers=["AAPL"])

    assert result.overall_sentiment.label == "positive"
    assert result.overall_sentiment.score == 0.6
    assert result.overall_sentiment.confidence == 0.7
    assert result.confidence == 0.7
    assert len(result.headline_sentiments) == 1
    assert result.headline_sentiments[0].ticker == "AAPL"
    assert result.processing_metadata.article_count == 1
    assert result.processing_metadata.tickers_provided == ["AAPL"]
    assert "earnings" in result.reasoning.lower()


@pytest.mark.asyncio
async def test_sentiment_service_empty_news_list_returns_neutral():
    service = SentimentService(max_retries=0)

    result = await service.analyze_articles(articles=[], tickers=["AAPL", "MSFT"])

    assert result.overall_sentiment.label == "neutral"
    assert result.overall_sentiment.score == 0.0
    assert result.confidence == 0.0
    assert result.headline_sentiments == []
    assert result.processing_metadata.article_count == 0
    assert result.processing_metadata.tickers_provided == ["AAPL", "MSFT"]


@pytest.mark.asyncio
async def test_sentiment_service_malformed_llm_response_raises_typed_error():
    service = SentimentService(max_retries=0)

    # Missing required "overall" key
    llm_payload = {
        "ticker_sentiments": {
            "AAPL": {"label": "positive", "score": 0.5, "confidence": 0.8}
        },
        "key_themes": [],
    }

    with patch.object(service, "llm", autospec=True) as llm_mock:
        llm_mock.analyze_sentiment = AsyncMock(return_value=llm_payload)

        articles = [_news_article(title="AAPL news")]
        with pytest.raises(SentimentMalformedResponseError):
            await service.analyze_articles(articles=articles, tickers=["AAPL"])


@pytest.mark.asyncio
async def test_sentiment_service_timeout_raises_typed_timeout():
    service = SentimentService(max_retries=0, llm_timeout_seconds=0.01)

    with patch.object(service, "llm", autospec=True) as llm_mock:
        llm_mock.analyze_sentiment = AsyncMock(
            side_effect=TimeoutError("provider timeout")
        )

        articles = [_news_article(title="AAPL news")]
        with pytest.raises(SentimentTimeoutError):
            await service.analyze_articles(articles=articles, tickers=["AAPL"])


@pytest.mark.asyncio
async def test_sentiment_service_provider_error_raises_typed_provider_error():
    service = SentimentService(max_retries=0)

    with patch.object(service, "llm", autospec=True) as llm_mock:
        llm_mock.analyze_sentiment = AsyncMock(
            side_effect=RuntimeError("network failure")
        )

        articles = [_news_article(title="AAPL news")]
        with pytest.raises(SentimentProviderError):
            await service.analyze_articles(articles=articles, tickers=["AAPL"])


@pytest.mark.asyncio
async def test_sentiment_service_retry_behavior_on_provider_error():
    service = SentimentService(max_retries=2, retry_backoff_seconds=0)

    llm_payload_success = {
        "overall": {"label": "neutral", "score": 0.0, "confidence": 0.4},
        "ticker_sentiments": {
            "AAPL": {"label": "neutral", "score": 0.0, "confidence": 0.5},
        },
        "key_themes": [],
    }

    with patch.object(service, "llm", autospec=True) as llm_mock:
        llm_mock.analyze_sentiment = AsyncMock(
            side_effect=[
                RuntimeError("provider down"),
                RuntimeError("provider down"),
                llm_payload_success,
            ]
        )

        articles = [_news_article(title="AAPL news")]
        result = await service.analyze_articles(articles=articles, tickers=["AAPL"])

    assert result.overall_sentiment.label == "neutral"
    assert llm_mock.analyze_sentiment.await_count == 3  # initial + 2 retries


@pytest.mark.asyncio
async def test_sentiment_service_schema_validation_error_raises_typed_validation_error():
    service = SentimentService(max_retries=0)

    # confidence out of range to trigger validation error (mapped as malformed/typed by service)
    llm_payload = {
        "overall": {"label": "positive", "score": 0.6, "confidence": 2.0},
        "ticker_sentiments": {
            "AAPL": {"label": "positive", "score": 0.5, "confidence": 0.8}
        },
        "key_themes": [],
    }

    with patch.object(service, "llm", autospec=True) as llm_mock:
        llm_mock.analyze_sentiment = AsyncMock(return_value=llm_payload)

        articles = [_news_article(title="AAPL news")]
        with pytest.raises((SentimentValidationError, SentimentMalformedResponseError)):
            await service.analyze_articles(articles=articles, tickers=["AAPL"])
