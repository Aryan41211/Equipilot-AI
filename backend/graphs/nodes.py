from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.graphs.state import GraphState, _get_timestamp
from backend.tools.market_data_tool import fetch_market_data
from backend.tools.news_tool import fetch_news
from backend.tools.sentiment_tool import analyze_sentiment
from backend.utils.logger import get_logger

logger = get_logger(__name__)

_TICKER_RE = re.compile(r"\b([A-Z]{1,5})\b")

_FUNDAMENTALS_KEYWORDS = {
    "fundamental", "financial", "financials", "earnings", "revenue", "profit", "valuation",
    "pe", "p/e", "margin", "balance", "cash flow", "dividend", "growth",
    "ROE", "ROI", "debt", "asset", "liability", "income", "expense",
    "fundamentals", "balance sheet", "income statement",
}

_NEWS_KEYWORDS = {
    "news", "headline", "headlines", "article", "announcement", "press", "media",
    "report",
}

_SENTIMENT_KEYWORDS = {
    "sentiment", "bullish", "bearish", "mood", "outlook", "optimistic",
    "pessimistic",
}

_MARKET_OVERVIEW_KEYWORDS = {
    "overview", "summary", "general", "market",
}


def _ensure_execution_metadata(state: GraphState) -> Dict[str, Any]:
    execution_metadata = dict(state.get("execution_metadata", {}) or {})
    execution_metadata.setdefault("nodes", {})
    execution_metadata.setdefault("tools", {})
    execution_metadata.setdefault("traces", [])
    return execution_metadata


def _record_node_start(state: GraphState, node_name: str) -> GraphState:
    execution_metadata = _ensure_execution_metadata(state)
    nodes = dict(execution_metadata.get("nodes", {}) or {})
    node_meta = nodes.get(node_name, {})
    started_at = _get_timestamp()
    node_meta["started_at"] = started_at
    nodes[node_name] = node_meta
    execution_metadata["nodes"] = nodes
    logger.info("Node started", node=node_name, request_id=state.get("request_id"))
    return {**state, "execution_metadata": execution_metadata}


def _record_tool_result(
    state: GraphState,
    *,
    tool_name: str,
    ok: bool,
    started_at: str,
    finished_at: str,
    result: Any,
) -> GraphState:
    execution_metadata = _ensure_execution_metadata(state)
    tools = dict(execution_metadata.get("tools", {}) or {})

    tools[tool_name] = {
        "ok": ok,
        "started_at": started_at,
        "finished_at": finished_at,
        "result": result,
    }
    execution_metadata["tools"] = tools
    logger.info(
        "Tool completed",
        tool=tool_name,
        ok=ok,
        request_id=state.get("request_id"),
    )
    return {**state, "execution_metadata": execution_metadata}


def _record_node_finish(
    state: GraphState, node_name: str, *, ok: bool, error: Optional[str] = None
) -> GraphState:
    execution_metadata = _ensure_execution_metadata(state)
    nodes = dict(execution_metadata.get("nodes", {}) or {})
    node_meta = nodes.get(node_name, {})
    node_meta["ok"] = ok
    if error:
        node_meta["error"] = error
    node_meta["finished_at"] = _get_timestamp()
    nodes[node_name] = node_meta
    execution_metadata["nodes"] = nodes

    traces = list(execution_metadata.get("traces", []))
    started_at = node_meta.get("started_at")
    duration_ms = None
    if started_at:
        try:
            start = datetime.fromisoformat(started_at)
            end = datetime.fromisoformat(node_meta["finished_at"])
            duration_ms = (end - start).total_seconds() * 1000
        except Exception:
            pass
    traces.append({
        "node_name": node_name,
        "start_time": started_at,
        "end_time": node_meta["finished_at"],
        "duration_ms": duration_ms,
        "success": ok,
        "error": error,
    })
    execution_metadata["traces"] = traces

    if ok:
        logger.info("Node completed", node=node_name, ok=True, request_id=state.get("request_id"))
    else:
        logger.warning(
            "Node failed",
            node=node_name,
            error=error,
            request_id=state.get("request_id"),
        )
    return {**state, "execution_metadata": execution_metadata}


def _append_error(state: GraphState, error_message: str) -> GraphState:
    errors = list(state.get("errors", []))
    errors.append(error_message)
    return {**state, "errors": errors}


def _classify_intent(query: str) -> str:
    """Classify user query into a research intent using deterministic rules."""
    q = query.lower()
    tokens = set(q.split())

    # Check multi-word phrases first
    for kw in _FUNDAMENTALS_KEYWORDS:
        if " " in kw and kw in q:
            return "fundamentals"

    if tokens & _FUNDAMENTALS_KEYWORDS:
        return "fundamentals"
    if tokens & _SENTIMENT_KEYWORDS:
        return "sentiment"
    if tokens & _NEWS_KEYWORDS:
        return "news"
    if tokens & _MARKET_OVERVIEW_KEYWORDS:
        return "market_overview"

    return "full_research"


def _select_tools(intent: str) -> tuple:
    """Return (selected_tools, skipped_tools) for a given intent."""
    if intent == "fundamentals":
        return (["market_data_tool"], ["news_tool", "sentiment_tool"])
    if intent == "news":
        return (["news_tool", "sentiment_tool"], ["market_data_tool"])
    if intent == "sentiment":
        return (["news_tool", "sentiment_tool"], ["market_data_tool"])
    if intent == "market_overview":
        return (["news_tool"], ["market_data_tool", "sentiment_tool"])
    return (["market_data_tool", "news_tool", "sentiment_tool"], [])


def router_node(state: GraphState) -> GraphState:
    """
    START -> router

    Deterministic rule-based router that validates input, extracts the ticker,
    classifies intent, and returns a structured routing decision.
    """
    state = _record_node_start(state, "router")
    try:
        user_query = state["user_query"]

        # Validate empty query
        if not user_query or not user_query.strip():
            executed_nodes = list(state.get("executed_nodes", []))
            if "router" not in executed_nodes:
                executed_nodes.append("router")
            state = _append_error(state, "Query is empty.")
            state = {
                **state,
                "ticker": None,
                "status": "failed",
                "executed_nodes": executed_nodes,
            }
            state = _record_node_finish(state, "router", ok=False, error="Empty query")
            return state

        # Extract ticker from query via simple heuristic
        matches = _TICKER_RE.findall(user_query.upper())

        # Avoid common English uppercase false positives in heuristic extraction.
        common_non_tickers = {
            "GIVE",
            "WHAT",
            "NO",
            "HERE",
            "UPDATES",
            "HAPPENING",
            "ME",
            "THE",
            "THIS",
            "THAT",
            "ABOUT",
            "IS",
            "IN",
            "ON",
            "FOR",
            "WITH",
            "SHOW",
            "OVERVIEW",
        }

        filtered = [m for m in matches if m not in common_non_tickers]
        ticker: Optional[str] = filtered[-1] if filtered else None

        executed_nodes = list(state.get("executed_nodes", []))
        if "router" not in executed_nodes:
            executed_nodes.append("router")

        if ticker is None:
            state = _append_error(state, "Ticker could not be extracted from query.")
            state = {**state, "ticker": None, "status": "failed", "executed_nodes": executed_nodes}
            state = _record_node_finish(state, "router", ok=False, error="Ticker extraction failed")
            return state

        detected_intent = _classify_intent(user_query)
        selected_tools, skipped_tools = _select_tools(detected_intent)

        state = {
            **state,
            "ticker": ticker,
            "detected_intent": detected_intent,
            "selected_tools": selected_tools,
            "skipped_tools": skipped_tools,
            "completed_tools": [],
            "failed_tools": [],
            "status": state.get("status", "pending"),
            "executed_nodes": executed_nodes,
        }
        logger.info(
            "Routing decision",
            intent=detected_intent,
            selected_tools=selected_tools,
            skipped_tools=skipped_tools,
            request_id=state.get("request_id"),
        )
        state = _record_node_finish(state, "router", ok=True)
        return state
    except Exception as e:
        executed_nodes = list(state.get("executed_nodes", []))
        if "router" not in executed_nodes:
            executed_nodes.append("router")
        state = _append_error(state, f"Router error: {str(e)}")
        state = {**state, "status": "failed", "executed_nodes": executed_nodes}
        state = _record_node_finish(state, "router", ok=False, error=str(e))
        return state


# Backwards-compatible alias:
# `backend/graphs/graph.py` currently imports `market_data_node`.
async def market_data_node(state: GraphState) -> GraphState:
    """
    Alias for `market_data_tool_node` (kept to preserve existing graph imports).
    """
    return await market_data_tool_node(state)


async def market_data_tool_node(state: GraphState) -> GraphState:
    """
    router -> Market Data Tool
    """
    state = _record_node_start(state, "market_data_tool")

    executed_nodes = list(state.get("executed_nodes", []))
    if "market_data_tool" not in executed_nodes:
        executed_nodes.append("market_data_tool")

    ticker = state.get("ticker")
    if not ticker:
        state = _append_error(state, "Ticker missing; cannot run Market Data Tool.")
        state = {**state, "market_data": {}, "executed_nodes": executed_nodes}
        state = _record_node_finish(state, "market_data_tool", ok=False, error="No ticker")
        failed_tools = list(state.get("failed_tools", []))
        if "market_data_tool" not in failed_tools:
            failed_tools.append("market_data_tool")
        return {**state, "failed_tools": failed_tools}

    started_at = _get_timestamp()
    try:
        result = await fetch_market_data(ticker)
        finished_at = _get_timestamp()

        ok = "error" not in result
        state = _record_tool_result(
            state,
            tool_name="market_data_tool",
            ok=ok,
            started_at=started_at,
            finished_at=finished_at,
            result=result,
        )

        completed_tools = list(state.get("completed_tools", []))
        failed_tools = list(state.get("failed_tools", []))
        if ok and "market_data_tool" not in completed_tools:
            completed_tools.append("market_data_tool")
        elif not ok and "market_data_tool" not in failed_tools:
            failed_tools.append("market_data_tool")

        if not ok:
            state = _append_error(state, f"Market Data Tool failed: {result.get('error')}")
            state = {**state, "market_data": {}, "status": state.get("status", "pending")}
        else:
            state = {**state, "market_data": result, "status": state.get("status", "pending")}

        state = _record_node_finish(state, "market_data_tool", ok=ok)
        state = {**state, "executed_nodes": executed_nodes, "completed_tools": completed_tools, "failed_tools": failed_tools}
        return state
    except Exception as e:
        finished_at = _get_timestamp()
        state = _record_tool_result(
            state,
            tool_name="market_data_tool",
            ok=False,
            started_at=started_at,
            finished_at=finished_at,
            result={"error": str(e)},
        )
        state = _append_error(state, f"Market Data Tool exception: {str(e)}")
        completed_tools = list(state.get("completed_tools", []))
        failed_tools = list(state.get("failed_tools", []))
        if "market_data_tool" not in failed_tools:
            failed_tools.append("market_data_tool")
        state = {
            **state,
            "market_data": {},
            "status": state.get("status", "pending"),
            "executed_nodes": executed_nodes,
            "completed_tools": completed_tools,
            "failed_tools": failed_tools,
        }
        state = _record_node_finish(state, "market_data_tool", ok=False, error=str(e))
        return state


async def news_tool_node(state: GraphState) -> GraphState:
    """
    market_data_tool -> News Tool
    """
    state = _record_node_start(state, "news_tool")

    executed_nodes = list(state.get("executed_nodes", []))
    if "news_tool" not in executed_nodes:
        executed_nodes.append("news_tool")

    ticker = state.get("ticker")
    if not ticker:
        state = _append_error(state, "Ticker missing; cannot run News Tool.")
        state = {**state, "news": {}, "executed_nodes": executed_nodes}
        state = _record_node_finish(state, "news_tool", ok=False, error="No ticker")
        return state

    started_at = _get_timestamp()
    try:
        result = await fetch_news(
            tickers=[ticker],
            date_from=None,
            date_to=None,
            limit=20,
        )
        finished_at = _get_timestamp()

        ok = "error" not in result
        state = _record_tool_result(
            state,
            tool_name="news_tool",
            ok=ok,
            started_at=started_at,
            finished_at=finished_at,
            result=result,
        )

        completed_tools = list(state.get("completed_tools", []))
        failed_tools = list(state.get("failed_tools", []))
        if ok and "news_tool" not in completed_tools:
            completed_tools.append("news_tool")
        elif not ok and "news_tool" not in failed_tools:
            failed_tools.append("news_tool")

        if not ok:
            state = _append_error(state, f"News Tool failed: {result.get('error')}")
            state = {**state, "news": {}, "status": state.get("status", "pending")}
        else:
            state = {**state, "news": result, "status": state.get("status", "pending")}

        state = _record_node_finish(state, "news_tool", ok=ok)
        state = {**state, "executed_nodes": executed_nodes, "completed_tools": completed_tools, "failed_tools": failed_tools}
        return state
    except Exception as e:
        finished_at = _get_timestamp()
        state = _record_tool_result(
            state,
            tool_name="news_tool",
            ok=False,
            started_at=started_at,
            finished_at=finished_at,
            result={"error": str(e)},
        )
        state = _append_error(state, f"News Tool exception: {str(e)}")
        completed_tools = list(state.get("completed_tools", []))
        failed_tools = list(state.get("failed_tools", []))
        if "news_tool" not in failed_tools:
            failed_tools.append("news_tool")
        state = {**state, "news": {}, "status": state.get("status", "pending"), "executed_nodes": executed_nodes, "completed_tools": completed_tools, "failed_tools": failed_tools}
        state = _record_node_finish(state, "news_tool", ok=False, error=str(e))
        return state


async def sentiment_tool_node(state: GraphState) -> GraphState:
    """
    news_tool -> Sentiment Tool
    """
    state = _record_node_start(state, "sentiment_tool")

    executed_nodes = list(state.get("executed_nodes", []))
    if "sentiment_tool" not in executed_nodes:
        executed_nodes.append("sentiment_tool")

    ticker = state.get("ticker")
    news_result = state.get("news", {})
    articles = news_result.get("articles", []) if isinstance(news_result, dict) else []

    started_at = _get_timestamp()
    try:
        result = await analyze_sentiment(
            articles=articles,
            tickers=[ticker] if ticker else [],
        )
        finished_at = _get_timestamp()

        ok = result.get("ok", False)
        state = _record_tool_result(
            state,
            tool_name="sentiment_tool",
            ok=ok,
            started_at=started_at,
            finished_at=finished_at,
            result=result,
        )

        completed_tools = list(state.get("completed_tools", []))
        failed_tools = list(state.get("failed_tools", []))
        if ok and "sentiment_tool" not in completed_tools:
            completed_tools.append("sentiment_tool")
        elif not ok and "sentiment_tool" not in failed_tools:
            failed_tools.append("sentiment_tool")

        if not ok:
            state = _append_error(state, f"Sentiment Tool failed: {result.get('error')}")
            state = {**state, "sentiment": {}, "status": state.get("status", "pending")}
        else:
            state = {**state, "sentiment": result, "status": state.get("status", "pending")}

        state = _record_node_finish(state, "sentiment_tool", ok=ok)
        state = {**state, "executed_nodes": executed_nodes, "completed_tools": completed_tools, "failed_tools": failed_tools}
        return state
    except Exception as e:
        finished_at = _get_timestamp()
        state = _record_tool_result(
            state,
            tool_name="sentiment_tool",
            ok=False,
            started_at=started_at,
            finished_at=finished_at,
            result={"error": str(e)},
        )
        state = _append_error(state, f"Sentiment Tool exception: {str(e)}")
        completed_tools = list(state.get("completed_tools", []))
        failed_tools = list(state.get("failed_tools", []))
        if "sentiment_tool" not in failed_tools:
            failed_tools.append("sentiment_tool")
        state = {**state, "sentiment": {}, "status": state.get("status", "pending"), "executed_nodes": executed_nodes, "completed_tools": completed_tools, "failed_tools": failed_tools}
        state = _record_node_finish(state, "sentiment_tool", ok=False, error=str(e))
        return state


def merge_results_node(state: GraphState) -> GraphState:
    """
    Merge results from executed tools.

    Stubbed for backwards compatibility; new dynamic routing no longer requires
    a dedicated merge node.
    """
    state = _record_node_start(state, "merge_results")
    executed_nodes = list(state.get("executed_nodes", []))
    if "merge_results" not in executed_nodes:
        executed_nodes.append("merge_results")
    state = _record_node_finish(state, "merge_results", ok=True)
    return {**state, "executed_nodes": executed_nodes}


def research_node(state: GraphState) -> GraphState:
    """
    Merge Results -> Placeholder Research (no LLM).
    """
    state = _record_node_start(state, "research")

    executed_nodes = list(state.get("executed_nodes", []))
    if "research" not in executed_nodes:
        executed_nodes.append("research")

    ticker = state.get("ticker")

    report = (
        f"Placeholder research report for {ticker}. "
        f"Includes market_data and/or news results where available. "
        f"(No LLM integration.)"
    )

    state = {**state, "report": report, "executed_nodes": executed_nodes}

    # Preserve existing success/failure semantics:
    # success if we have market_data or news, failed otherwise.
    state_status = state.get("status", "pending")
    if state_status not in ("success", "failed"):
        has_market = bool(state.get("market_data"))
        has_news = bool(state.get("news"))
        state_status = "success" if (has_market or has_news) else "failed"
        state = {**state, "status": state_status}

    ok = state_status == "success"
    if not ok:
        state = _append_error(state, "Research produced but no tool data available")
    state = _record_node_finish(state, "research", ok=ok, error=None if ok else "Research produced but no tool data")
    return state
