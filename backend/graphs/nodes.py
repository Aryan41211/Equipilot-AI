from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict

from backend.graphs.state import GraphState


_TICKER_RE = re.compile(r"\b([A-Z]{1,5})\b")


def router_node(state: GraphState) -> GraphState:
    """
    Route the user query to identify a ticker.

    Placeholder behavior:
    - Extract the first uppercase token that looks like a ticker (1-5 chars).
    - If none is found, default to "TCS" (required for the example execution).
    """
    user_query = state["user_query"]

    try:
        match = _TICKER_RE.search(user_query.upper())
        ticker = match.group(1) if match else "TCS"

        return {
            **state,
            "ticker": ticker,
            "errors": list(state.get("errors", [])),
        }
    except Exception as e:
        errors = list(state.get("errors", []))
        errors.append(f"Router error: {e}")
        return {
            **state,
            "ticker": state.get("ticker", "TCS"),
            "errors": errors,
        }


def market_data_node(state: GraphState) -> GraphState:
    """
    Fetch market data for the ticker.

    Placeholder behavior:
    - No external calls.
    - Returns minimal market_data containing ticker + timestamp.
    """
    try:
        ticker = state["ticker"]
        now = datetime.utcnow().isoformat()

        market_data: Dict[str, Any] = {
            "ticker": ticker,
            "source": "placeholder",
            "data_as_of": now,
        }

        return {
            **state,
            "market_data": market_data,
        }
    except Exception as e:
        errors = list(state.get("errors", []))
        errors.append(f"Market data node error: {e}")
        return {
            **state,
            "market_data": {},
            "errors": errors,
        }


def research_node(state: GraphState) -> GraphState:
    """
    Generate the research report.

    Placeholder behavior:
    - No LLM.
    - Returns a deterministic placeholder report string.
    """
    try:
        ticker = state["ticker"]
        report = (
            f"Placeholder research report for {ticker} based on market data. "
            f"(No LLM integration yet.)"
        )

        return {
            **state,
            "report": report,
        }
    except Exception as e:
        errors = list(state.get("errors", []))
        errors.append(f"Research node error: {e}")
        return {
            **state,
            "report": "",
            "errors": errors,
        }
