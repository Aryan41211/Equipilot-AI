from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, Optional

from backend.graphs.state import GraphState

_TICKER_RE = re.compile(r"\b([A-Z]{1,5})\b")


def _fail(state: GraphState, message: str, *, node_name: str, err: Optional[Exception] = None) -> GraphState:
    errors = list(state.get("errors", []))
    if err is not None:
        errors.append(f"{node_name} error: {err}")
    else:
        errors.append(message)

    # status must be failed on any exception (and also on extraction failure)
    executed_nodes = list(state.get("executed_nodes", []))
    if node_name not in executed_nodes:
        executed_nodes.append(node_name)

    return {
        **state,
        "status": "failed",
        "executed_nodes": executed_nodes,
        "errors": errors,
    }


def router_node(state: GraphState) -> GraphState:
    """
    Route the user query to identify a ticker.

    Placeholder behavior:
    - Extract the first uppercase token that looks like a ticker (1-5 chars).
    - If extraction fails: ticker=None, append exact error message and status=failed.
    """
    try:
        executed_nodes = list(state.get("executed_nodes", []))
        executed_nodes.append("router")

        user_query = state["user_query"]
        match = _TICKER_RE.search(user_query.upper())
        ticker: Optional[str] = match.group(1) if match else None

        if ticker is None:
            errors = list(state.get("errors", []))
            errors.append("Ticker could not be extracted from query.")
            return {
                **state,
                "ticker": None,
                "status": "failed",
                "executed_nodes": executed_nodes,
                "errors": errors,
            }

        return {
            **state,
            "ticker": ticker,
            "status": state.get("status", "pending"),
            "executed_nodes": executed_nodes,
        }
    except Exception as e:
        return _fail(state, "Router error", node_name="router", err=e)


def market_data_node(state: GraphState) -> GraphState:
    """
    Fetch market data for the ticker.

    Placeholder behavior:
    - No external calls.
    - Returns minimal market_data containing ticker + timestamp.
    """
    try:
        executed_nodes = list(state.get("executed_nodes", []))
        executed_nodes.append("market_data")

        ticker = state.get("ticker")
        if not ticker:
            return _fail(
                state,
                "Ticker could not be extracted from query.",
                node_name="market_data",
            )

        now = datetime.utcnow().isoformat()
        market_data: Dict[str, Any] = {
            "ticker": ticker,
            "source": "placeholder",
            "data_as_of": now,
        }

        return {
            **state,
            "market_data": market_data,
            "status": state.get("status", "pending"),
            "executed_nodes": executed_nodes,
        }
    except Exception as e:
        return _fail(state, "Market data error", node_name="market_data", err=e)


def research_node(state: GraphState) -> GraphState:
    """
    Generate the research report.

    Placeholder behavior:
    - No LLM.
    - Returns a deterministic placeholder report string.
    - If prior nodes failed, this node will propagate failure.
    """
    try:
        executed_nodes = list(state.get("executed_nodes", []))
        executed_nodes.append("research")

        # If earlier nodes failed, keep failed status and avoid producing a report.
        if state.get("status") == "failed":
            return {
                **state,
                "status": "failed",
                "executed_nodes": executed_nodes,
            }

        ticker = state.get("ticker")
        report = (
            f"Placeholder research report for {ticker} based on market data. "
            f"(No LLM integration yet.)"
        )

        return {
            **state,
            "report": report,
            "status": "success",
            "executed_nodes": executed_nodes,
        }
    except Exception as e:
        # On exception, mark failed.
        return _fail(state, "Research error", node_name="research", err=e)
