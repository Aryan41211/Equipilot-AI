import sys
import os
import pytest
from unittest.mock import patch, AsyncMock

# Ensure backend imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.graphs.graph import create_first_graph, create_initial_state


def _base_query_with_ticker(ticker: str = "TCS") -> str:
    return f"Analyze {ticker}"


@pytest.mark.asyncio
async def test_market_and_news_success():
    graph = create_first_graph()
    state = create_initial_state(_base_query_with_ticker("TCS"))

    with patch(
        "backend.graphs.nodes.fetch_market_data", new_callable=AsyncMock
    ) as mm, patch("backend.graphs.nodes.fetch_news", new_callable=AsyncMock) as nn, patch(
        "backend.graphs.nodes.analyze_sentiment", new_callable=AsyncMock
    ) as ss:
        mm.return_value = {"ticker": "TCS", "price": 123}
        nn.return_value = {
            "query": "",
            "tickers": ["TCS"],
            "articles": [],
            "total_results": 0,
        }
        ss.return_value = {"ok": True, "result": {"overall_sentiment": {"label": "neutral"}}, "error": None}

        result = await graph.ainvoke(state)

    assert result["status"] == "success"
    assert result["ticker"] == "TCS"
    assert isinstance(result["market_data"], dict) and result["market_data"]
    assert isinstance(result["news"], dict) and result["news"]
    assert result["errors"] == []

    assert "router" in result["executed_nodes"]
    assert "market_data_tool" in result["executed_nodes"]
    assert "news_tool" in result["executed_nodes"]
    assert "sentiment_tool" in result["executed_nodes"]
    assert "research" in result["executed_nodes"]

    em = result["execution_metadata"]
    assert em["nodes"]["router"]["ok"] is True
    assert em["nodes"]["market_data_tool"]["ok"] is True
    assert em["nodes"]["news_tool"]["ok"] is True
    assert em["nodes"]["sentiment_tool"]["ok"] is True
    assert em["nodes"]["research"]["ok"] is True

    assert em["tools"]["market_data_tool"]["ok"] is True
    assert em["tools"]["news_tool"]["ok"] is True
    assert em["tools"]["sentiment_tool"]["ok"] is True


@pytest.mark.asyncio
async def test_market_success_news_fails():
    graph = create_first_graph()
    state = create_initial_state(_base_query_with_ticker("TCS"))

    with patch(
        "backend.graphs.nodes.fetch_market_data", new_callable=AsyncMock
    ) as mm, patch("backend.graphs.nodes.fetch_news", new_callable=AsyncMock) as nn, patch(
        "backend.graphs.nodes.analyze_sentiment", new_callable=AsyncMock
    ) as ss:
        mm.return_value = {"ticker": "TCS", "price": 123}
        nn.return_value = {"error": "news failed", "error_type": "service_error"}
        ss.return_value = {"ok": True, "result": {"overall_sentiment": {"label": "neutral"}}, "error": None}

        result = await graph.ainvoke(state)

    assert result["status"] == "success"
    assert result["ticker"] == "TCS"
    assert result["market_data"]
    assert result["news"] == {}
    assert any(
        "News Tool failed" in e or "News Tool exception" in e for e in result["errors"]
    )

    em = result["execution_metadata"]
    assert em["nodes"]["market_data_tool"]["ok"] is True
    assert em["nodes"]["news_tool"]["ok"] is False
    assert em["nodes"]["sentiment_tool"]["ok"] is True
    assert em["nodes"]["research"]["ok"] is True

    assert em["tools"]["market_data_tool"]["ok"] is True
    assert em["tools"]["news_tool"]["ok"] is False
    assert em["tools"]["sentiment_tool"]["ok"] is True


@pytest.mark.asyncio
async def test_market_fails_news_success():
    graph = create_first_graph()
    state = create_initial_state(_base_query_with_ticker("TCS"))

    with patch(
        "backend.graphs.nodes.fetch_market_data", new_callable=AsyncMock
    ) as mm, patch("backend.graphs.nodes.fetch_news", new_callable=AsyncMock) as nn, patch(
        "backend.graphs.nodes.analyze_sentiment", new_callable=AsyncMock
    ) as ss:
        mm.return_value = {"error": "market failed", "error_type": "service_error"}
        nn.return_value = {
            "query": "",
            "tickers": ["TCS"],
            "articles": [],
            "total_results": 0,
        }
        ss.return_value = {"ok": True, "result": {"overall_sentiment": {"label": "neutral"}}, "error": None}

        result = await graph.ainvoke(state)

    assert result["status"] == "success"
    assert result["ticker"] == "TCS"
    assert result["market_data"] == {}
    assert result["news"]
    assert any(
        "Market Data Tool failed" in e or "Market Data Tool exception" in e
        for e in result["errors"]
    )

    em = result["execution_metadata"]
    assert em["nodes"]["market_data_tool"]["ok"] is False
    assert em["nodes"]["news_tool"]["ok"] is True
    assert em["nodes"]["sentiment_tool"]["ok"] is True
    assert em["nodes"]["research"]["ok"] is True

    assert em["tools"]["market_data_tool"]["ok"] is False
    assert em["tools"]["news_tool"]["ok"] is True
    assert em["tools"]["sentiment_tool"]["ok"] is True


@pytest.mark.asyncio
async def test_both_fail():
    graph = create_first_graph()
    state = create_initial_state(_base_query_with_ticker("TCS"))

    with patch(
        "backend.graphs.nodes.fetch_market_data", new_callable=AsyncMock
    ) as mm, patch("backend.graphs.nodes.fetch_news", new_callable=AsyncMock) as nn, patch(
        "backend.graphs.nodes.analyze_sentiment", new_callable=AsyncMock
    ) as ss:
        mm.return_value = {"error": "market failed", "error_type": "service_error"}
        nn.return_value = {"error": "news failed", "error_type": "service_error"}
        ss.return_value = {"ok": True, "result": {"overall_sentiment": {"label": "neutral"}}, "error": None}

        result = await graph.ainvoke(state)

    assert result["status"] == "failed"
    assert result["ticker"] == "TCS"
    assert result["market_data"] == {}
    assert result["news"] == {}
    assert len(result["errors"]) >= 2

    em = result["execution_metadata"]
    assert em["nodes"]["market_data_tool"]["ok"] is False
    assert em["nodes"]["news_tool"]["ok"] is False
    assert em["nodes"]["sentiment_tool"]["ok"] is True
    assert em["nodes"]["research"]["ok"] is False

    assert em["tools"]["market_data_tool"]["ok"] is False
    assert em["tools"]["news_tool"]["ok"] is False
    assert em["tools"]["sentiment_tool"]["ok"] is True


@pytest.mark.asyncio
async def test_router_fails_to_extract_ticker():
    graph = create_first_graph()
    state = create_initial_state("What is happening? No explicit ticker here")

    # Tools should not be called; patch anyway to detect unexpected calls
    with patch(
        "backend.graphs.nodes.fetch_market_data", new_callable=AsyncMock
    ) as mm, patch("backend.graphs.nodes.fetch_news", new_callable=AsyncMock) as nn, patch(
        "backend.graphs.nodes.analyze_sentiment", new_callable=AsyncMock
    ) as ss:
        result = await graph.ainvoke(state)

        mm.assert_not_called()
        nn.assert_not_called()
        ss.assert_not_called()

    assert result["status"] == "failed"
    assert result["ticker"] is None
    assert result["market_data"] == {}
    assert result["news"] == {}
    assert any("Ticker could not be extracted" in e for e in result["errors"])

    em = result["execution_metadata"]
    assert em["nodes"]["router"]["ok"] is False
