from __future__ import annotations

import sys
import os
from unittest.mock import patch, AsyncMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.graphs.graph import create_first_graph, create_initial_state
from backend.graphs.nodes import _classify_intent, _select_tools


def _make_successful_mocks():
    """Return standard successful mock returns for all three tools."""
    return {
        "fetch_market_data": AsyncMock(return_value={"ticker": "TCS", "price": 123}),
        "fetch_news": AsyncMock(
            return_value={
                "query": "",
                "tickers": ["TCS"],
                "articles": [],
                "total_results": 0,
            }
        ),
        "analyze_sentiment": AsyncMock(
            return_value={
                "ok": True,
                "result": {"overall_sentiment": {"label": "neutral"}},
                "error": None,
            }
        ),
    }


@pytest.mark.asyncio
async def test_fundamentals_query_routes_to_market_data_only():
    graph = create_first_graph()
    state = create_initial_state("Fundamental analysis of TCS")

    mocks = _make_successful_mocks()
    with patch(
        "backend.graphs.nodes.fetch_market_data", mocks["fetch_market_data"]
    ), patch("backend.graphs.nodes.fetch_news", mocks["fetch_news"]), patch(
        "backend.graphs.nodes.analyze_sentiment", mocks["analyze_sentiment"]
    ):
        result = await graph.ainvoke(state)

    assert result["status"] == "success"
    assert result["ticker"] == "TCS"
    assert result["market_data"]
    assert result["news"] == {}
    assert result["errors"] == []

    em = result["execution_metadata"]
    assert "market_data_tool" in result["executed_nodes"]
    assert "news_tool" not in result["executed_nodes"]
    assert "sentiment_tool" not in result["executed_nodes"]
    assert "research" in result["executed_nodes"]

    assert em["tools"]["market_data_tool"]["ok"] is True
    assert "news_tool" not in em["tools"]
    assert "sentiment_tool" not in em["tools"]


@pytest.mark.asyncio
async def test_news_query_routes_to_news_and_sentiment():
    graph = create_first_graph()
    state = create_initial_state("Latest news about AAPL")

    mocks = _make_successful_mocks()
    with patch(
        "backend.graphs.nodes.fetch_market_data", mocks["fetch_market_data"]
    ), patch("backend.graphs.nodes.fetch_news", mocks["fetch_news"]), patch(
        "backend.graphs.nodes.analyze_sentiment", mocks["analyze_sentiment"]
    ):
        result = await graph.ainvoke(state)

    assert result["status"] == "success"
    assert result["ticker"] == "AAPL"
    assert result["market_data"] == {}
    assert result["news"]

    em = result["execution_metadata"]
    assert "market_data_tool" not in result["executed_nodes"]
    assert "news_tool" in result["executed_nodes"]
    assert "sentiment_tool" in result["executed_nodes"]
    assert "research" in result["executed_nodes"]

    assert em["tools"]["news_tool"]["ok"] is True
    assert em["tools"]["sentiment_tool"]["ok"] is True


@pytest.mark.asyncio
async def test_full_research_query_routes_to_all_tools():
    graph = create_first_graph()
    state = create_initial_state("Full analysis of MSFT")

    mocks = _make_successful_mocks()
    with patch(
        "backend.graphs.nodes.fetch_market_data", mocks["fetch_market_data"]
    ), patch("backend.graphs.nodes.fetch_news", mocks["fetch_news"]), patch(
        "backend.graphs.nodes.analyze_sentiment", mocks["analyze_sentiment"]
    ):
        result = await graph.ainvoke(state)

    assert result["status"] == "success"
    assert result["ticker"] == "MSFT"
    assert result["market_data"]
    assert result["news"]

    em = result["execution_metadata"]
    assert "market_data_tool" in result["executed_nodes"]
    assert "news_tool" in result["executed_nodes"]
    assert "sentiment_tool" in result["executed_nodes"]
    assert "research" in result["executed_nodes"]

    assert em["tools"]["market_data_tool"]["ok"] is True
    assert em["tools"]["news_tool"]["ok"] is True
    assert em["tools"]["sentiment_tool"]["ok"] is True


@pytest.mark.asyncio
async def test_empty_query_fails():
    graph = create_first_graph()
    state = create_initial_state("")

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
    assert any("empty" in e.lower() or "Empty" in e for e in result["errors"])
    assert result["execution_metadata"]["nodes"]["router"]["ok"] is False


@pytest.mark.asyncio
async def test_invalid_query_no_ticker_fails():
    graph = create_first_graph()
    state = create_initial_state("What is happening? No explicit ticker here")

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
    assert any("Ticker could not be extracted" in e for e in result["errors"])
    assert result["execution_metadata"]["nodes"]["router"]["ok"] is False


def test_routing_correctness_fundamentals():
    state = {
        "detected_intent": "fundamentals",
        "selected_tools": _select_tools("fundamentals")[0],
        "skipped_tools": _select_tools("fundamentals")[1],
    }
    assert state["selected_tools"] == ["market_data_tool"]
    assert state["skipped_tools"] == ["news_tool", "sentiment_tool"]


def test_routing_correctness_news():
    state = {
        "detected_intent": "news",
        "selected_tools": _select_tools("news")[0],
        "skipped_tools": _select_tools("news")[1],
    }
    assert state["selected_tools"] == ["news_tool", "sentiment_tool"]
    assert state["skipped_tools"] == ["market_data_tool"]


def test_routing_correctness_full_research():
    state = {
        "detected_intent": "full_research",
        "selected_tools": _select_tools("full_research")[0],
        "skipped_tools": _select_tools("full_research")[1],
    }
    assert state["selected_tools"] == ["market_data_tool", "news_tool", "sentiment_tool"]
    assert state["skipped_tools"] == []


@pytest.mark.asyncio
async def test_sentiment_tool_skipped_when_news_has_no_articles():
    graph = create_first_graph()
    state = create_initial_state("News about AAPL")

    mocks = _make_successful_mocks()
    mocks["fetch_news"].return_value = {
        "query": "",
        "tickers": ["AAPL"],
        "articles": [],
        "total_results": 0,
    }

    with patch(
        "backend.graphs.nodes.fetch_market_data", mocks["fetch_market_data"]
    ), patch("backend.graphs.nodes.fetch_news", mocks["fetch_news"]), patch(
        "backend.graphs.nodes.analyze_sentiment", mocks["analyze_sentiment"]
    ) as sentiment_mock:
        result = await graph.ainvoke(state)

    assert result["status"] == "success"
    assert result["execution_metadata"]["nodes"]["sentiment_tool"]["ok"] is True
    sentiment_mock.assert_called_once()
