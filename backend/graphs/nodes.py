from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, Optional

from backend.graphs.state import GraphState

_TICKER_RE = re.compile(r"\b([A-Z]{1,5})\b")


def _success(state: GraphState, *, node_name: str) -> GraphState:
    executed_nodes = list(state.get("executed_nodes", []))
    if node_name not in executed_nodes:
        executed_nodes.append(node_name)

    return {
        **state,
        "executed_nodes": executed_nodes,
        "status": "success",
    }


def _fail(state: GraphState, *, node_name: str, error_message: str) -> GraphState:
    executed_nodes = list(state.get("executed_nodes", []))
    if node_name not in executed_nodes:
        executed_nodes.append(node_name)

    errors = list(state.get("errors", []))
    errors.append(error_message)

    return {
        **state,
        "status": "failed",
        "executed_nodes": executed_nodes,
        "errors": errors,
    }


def router_node(state: GraphState) -> GraphState:
    """
    START -> router -> market_data

    Placeholder behavior:
    - Extract ticker from the query via a simple heuristic.
    - If extraction fails:
      ticker=None
      status="failed"
      append "Ticker could not be extracted from query."
    """
    try:
        user_query = state["user_query"]
        match = _TICKER_RE.search(user_query.upper())
        ticker: Optional[str] = match.group(1) if match else None

        executed_nodes = list(state.get("executed_nodes", []))
        if "router" not in executed_nodes:
            executed_nodes.append("router")

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
        # Single try/except as required.
        return _fail(state, node_name="router", error_message=str(e))


def market_data_node(state: GraphState) -> GraphState:
    """
    router -> market_data

    Placeholder behavior:
    - No external calls.
    - Populates market_data when ticker is present.
    """
    try:
        executed_nodes = list(state.get("executed_nodes", []))
        if "market_data" not in executed_nodes:
            executed_nodes.append("market_data")

        ticker = state.get("ticker")
        if not ticker:
            errors = list(state.get("errors", []))
            errors.append("Ticker could not be extracted from query.")
            return {
                **state,
                "status": "failed",
                "executed_nodes": executed_nodes,
                "errors": errors,
            }

        market_data: Dict[str, Any] = {
            "ticker": ticker,
            "source": "placeholder",
            "data_as_of": datetime.utcnow().isoformat(),
        }

        return {
            **state,
            "market_data": market_data,
            "status": state.get("status", "pending"),
            "executed_nodes": executed_nodes,
        }
    except Exception as e:
        return _fail(state, node_name="market_data", error_message=str(e))


def research_node(state: GraphState) -> GraphState:
    """
    market_data -> research -> END

    Placeholder behavior:
    - No LLM.
    - If state is already failed, propagate failure.
    - Otherwise set a placeholder report and status="success".
    """
    try:
        executed_nodes = list(state.get("executed_nodes", []))
        if "research" not in executed_nodes:
            executed_nodes.append("research")

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
        return _fail(state, node_name="research", error_message=str(e))
