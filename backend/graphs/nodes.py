from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, Optional

from backend.graphs.state import GraphState
from backend.tools.market_data_tool import fetch_market_data
from backend.tools.news_tool import fetch_news

_TICKER_RE = re.compile(r"\b([A-Z]{1,5})\b")


def _ensure_execution_metadata(state: GraphState) -> Dict[str, Any]:
    execution_metadata = dict(state.get("execution_metadata", {}) or {})
    execution_metadata.setdefault("nodes", {})
    execution_metadata.setdefault("tools", {})
    return execution_metadata


def _record_node_start(state: GraphState, node_name: str) -> GraphState:
    execution_metadata = _ensure_execution_metadata(state)
    nodes = dict(execution_metadata.get("nodes", {}) or {})
    node_meta = nodes.get(node_name, {})
    node_meta["started_at"] = datetime.utcnow().isoformat()
    nodes[node_name] = node_meta
    execution_metadata["nodes"] = nodes
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
    node_meta["finished_at"] = datetime.utcnow().isoformat()
    nodes[node_name] = node_meta
    execution_metadata["nodes"] = nodes
    return {**state, "execution_metadata": execution_metadata}


def _append_error(state: GraphState, error_message: str) -> GraphState:
    errors = list(state.get("errors", []))
    errors.append(error_message)
    return {**state, "errors": errors}


def router_node(state: GraphState) -> GraphState:
    """
    START -> router

    Extract ticker from query via a simple heuristic.
    """
    state = _record_node_start(state, "router")
    try:
        user_query = state["user_query"]
        matches = _TICKER_RE.findall(user_query.upper())
        # Pick the most likely ticker mention by using the last all-caps token
        # (e.g. "Give me updates about TCS" => "TCS", not "GIVE").
        ticker: Optional[str] = matches[-1] if matches else None

        executed_nodes = list(state.get("executed_nodes", []))
        if "router" not in executed_nodes:
            executed_nodes.append("router")

        if ticker is None:
            state = _append_error(state, "Ticker could not be extracted from query.")
            state = {**state, "ticker": None, "status": "failed", "executed_nodes": executed_nodes}
            state = _record_node_finish(state, "router", ok=False, error="Ticker extraction failed")
            return state

        state = {
            **state,
            "ticker": ticker,
            "status": state.get("status", "pending"),
            "executed_nodes": executed_nodes,
        }
        state = _record_node_finish(state, "router", ok=True)
        return state
    except Exception as e:
        state = _append_error(state, f"Router error: {str(e)}")
        state = {**state, "status": "failed"}
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
        return state

    started_at = datetime.utcnow().isoformat()
    try:
        result = await fetch_market_data(ticker)
        finished_at = datetime.utcnow().isoformat()

        ok = "error" not in result
        state = _record_tool_result(
            state,
            tool_name="market_data_tool",
            ok=ok,
            started_at=started_at,
            finished_at=finished_at,
            result=result,
        )

        if not ok:
            state = _append_error(state, f"Market Data Tool failed: {result.get('error')}")
            state = {**state, "market_data": {}, "status": state.get("status", "pending")}
        else:
            state = {**state, "market_data": result, "status": state.get("status", "pending")}

        state = _record_node_finish(state, "market_data_tool", ok=ok)
        state = {**state, "executed_nodes": executed_nodes}
        return state
    except Exception as e:
        finished_at = datetime.utcnow().isoformat()
        state = _record_tool_result(
            state,
            tool_name="market_data_tool",
            ok=False,
            started_at=started_at,
            finished_at=finished_at,
            result={"error": str(e)},
        )
        state = _append_error(state, f"Market Data Tool exception: {str(e)}")
        state = {
            **state,
            "market_data": {},
            "status": state.get("status", "pending"),
            "executed_nodes": executed_nodes,
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

    started_at = datetime.utcnow().isoformat()
    try:
        result = await fetch_news(
            tickers=[ticker],
            date_from=None,
            date_to=None,
            limit=20,
        )
        finished_at = datetime.utcnow().isoformat()

        ok = "error" not in result
        state = _record_tool_result(
            state,
            tool_name="news_tool",
            ok=ok,
            started_at=started_at,
            finished_at=finished_at,
            result=result,
        )

        if not ok:
            state = _append_error(state, f"News Tool failed: {result.get('error')}")
            state = {**state, "news": {}, "status": state.get("status", "pending")}
        else:
            state = {**state, "news": result, "status": state.get("status", "pending")}

        state = _record_node_finish(state, "news_tool", ok=ok)
        state = {**state, "executed_nodes": executed_nodes}
        return state
    except Exception as e:
        finished_at = datetime.utcnow().isoformat()
        state = _record_tool_result(
            state,
            tool_name="news_tool",
            ok=False,
            started_at=started_at,
            finished_at=finished_at,
            result={"error": str(e)},
        )
        state = _append_error(state, f"News Tool exception: {str(e)}")
        state = {**state, "news": {}, "status": state.get("status", "pending"), "executed_nodes": executed_nodes}
        state = _record_node_finish(state, "news_tool", ok=False, error=str(e))
        return state


def merge_results_node(state: GraphState) -> GraphState:
    """
    Market Data + News -> Merge Results

    For this milestone, merging is implicit: keep outputs in state.
    """
    state = _record_node_start(state, "merge_results")

    executed_nodes = list(state.get("executed_nodes", []))
    if "merge_results" not in executed_nodes:
        executed_nodes.append("merge_results")

    # Determine overall success/failure:
    # - If both tools failed => status failed
    # - Else => status success (research placeholder can still be produced)
    has_market = bool(state.get("market_data"))
    has_news = bool(state.get("news"))

    ok = has_market or has_news
    new_status = "success" if ok else "failed"
    state = {**state, "status": new_status, "executed_nodes": executed_nodes}

    state = _record_node_finish(state, "merge_results", ok=ok, error=None if ok else "Both tools failed")
    return state


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

    # If both tools failed, keep status failed; otherwise success.
    state_status = state.get("status", "pending")
    if state_status not in ("success", "failed"):
        state_status = "success" if (state.get("market_data") or state.get("news")) else "failed"
        state = {**state, "status": state_status}

    ok = state_status == "success"
    state = _record_node_finish(state, "research", ok=ok, error=None if ok else "Research produced but no tool data")
    return state
