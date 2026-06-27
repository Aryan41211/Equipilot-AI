from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from backend.exceptions.sentiment_exceptions import (
    SentimentMalformedResponseError,
    SentimentProviderError,
    SentimentTimeoutError,
)
from backend.schemas.sentiment import SentimentAnalysis, SentimentScore, HeadlineSentiment, SentimentProcessingMetadata
from backend.tools.sentiment_tool import SentimentTool


def _sample_sentiment() -> SentimentAnalysis:
    return SentimentAnalysis(
        overall_sentiment=SentimentScore(label="positive", score=0.6, confidence=0.7),
        confidence=0.7,
        reasoning="earnings beat expectations",
        headline_sentiments=[
            HeadlineSentiment(
                headline="Ticker sentiment for AAPL",
                ticker="AAPL",
                label="positive",
                confidence=0.8,
                reasoning="Derived from ticker-level sentiment.",
            )
        ],
        processing_metadata=SentimentProcessingMetadata(article_count=1, tickers_provided=["AAPL"]),
    )


@pytest.mark.asyncio
async def test_sentiment_tool_successful_response_contract():
    tool = SentimentTool()

    with patch.object(tool, "sentiment_service", None, create=True):
        pass

    # Patch the singleton sentiment_service inside module
    from backend.tools import sentiment_tool as module

    with patch.object(module.sentiment_service, "analyze_articles", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = _sample_sentiment()

        resp = await module.SentimentTool().analyze_sentiment.ainvoke(
            {"articles": [{"title": "AAPL beats", "ticker": "AAPL"}], "tickers": ["AAPL"]}
        )

    assert resp["ok"] is True
    assert resp["error"] is None
    assert resp["result"]["overall_sentiment"]["label"] == "positive"
    assert resp["result"]["headline_sentiments"][0]["ticker"] == "AAPL"


@pytest.mark.asyncio
async def test_sentiment_tool_exception_mapping_on_malformed_response():
    from backend.tools import sentiment_tool as module

    with patch.object(
        module.sentiment_service,
        "analyze_articles",
        new_callable=AsyncMock,
    ) as mock_analyze:
        mock_analyze.side_effect = SentimentMalformedResponseError("bad json")

        resp = await module.SentimentTool().analyze_sentiment.ainvoke(
            {"articles": [{"title": "AAPL beats", "ticker": "AAPL"}], "tickers": ["AAPL"]}
        )

    assert resp["ok"] is False
    assert resp["result"] is None
    assert resp["error"]["type"] == "SentimentMalformedResponseError"
    assert "bad json" in resp["error"]["message"]


@pytest.mark.asyncio
async def test_sentiment_tool_exception_mapping_on_timeout():
    from backend.tools import sentiment_tool as module

    with patch.object(module.sentiment_service, "analyze_articles", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.side_effect = SentimentTimeoutError("timeout")

        resp = await module.SentimentTool().analyze_sentiment.ainvoke(
            {"articles": [{"title": "AAPL beats", "ticker": "AAPL"}], "tickers": ["AAPL"]}
        )

    assert resp["ok"] is False
    assert resp["error"]["type"] == "SentimentTimeoutError"


@pytest.mark.asyncio
async def test_sentiment_tool_exception_mapping_on_provider_error():
    from backend.tools import sentiment_tool as module

    with patch.object(module.sentiment_service, "analyze_articles", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.side_effect = SentimentProviderError("provider down")

        resp = await module.SentimentTool().analyze_sentiment.ainvoke(
            {"articles": [{"title": "AAPL beats", "ticker": "AAPL"}], "tickers": ["AAPL"]}
        )

    assert resp["ok"] is False
    assert resp["error"]["type"] == "SentimentProviderError"


@pytest.mark.asyncio
async def test_sentiment_tool_keeps_contract_on_unexpected_exception():
    from backend.tools import sentiment_tool as module

    with patch.object(module.sentiment_service, "analyze_articles", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.side_effect = RuntimeError("unexpected")

        resp = await module.SentimentTool().analyze_sentiment.ainvoke(
            {"articles": [{"title": "AAPL beats", "ticker": "AAPL"}], "tickers": ["AAPL"]}
        )

    assert resp["ok"] is False
    assert resp["result"] is None
    assert resp["error"]["type"] == "UnexpectedError"
    assert "unexpected" in resp["error"]["message"]
