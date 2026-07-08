from __future__ import annotations

import asyncio
import re
from datetime import datetime
from typing import Any

from backend.graphs.state import GraphState, _get_timestamp
from backend.tools.market_data_tool import fetch_market_data
from backend.tools.news_tool import fetch_news
from backend.tools.sentiment_tool import analyze_sentiment
from backend.utils.logger import get_logger

logger = get_logger(__name__)

_TICKER_RE = re.compile(r"\b([A-Z]{1,5})\b")

_FUNDAMENTALS_KEYWORDS = {
    "fundamental",
    "financial",
    "financials",
    "earnings",
    "revenue",
    "profit",
    "valuation",
    "pe",
    "p/e",
    "margin",
    "balance",
    "cash flow",
    "dividend",
    "growth",
    "ROE",
    "ROI",
    "debt",
    "asset",
    "liability",
    "income",
    "expense",
    "fundamentals",
    "balance sheet",
    "income statement",
}

_NEWS_KEYWORDS = {
    "news",
    "headline",
    "headlines",
    "article",
    "announcement",
    "press",
    "media",
    "report",
}

_SENTIMENT_KEYWORDS = {
    "sentiment",
    "bullish",
    "bearish",
    "mood",
    "outlook",
    "optimistic",
    "pessimistic",
}

_MARKET_OVERVIEW_KEYWORDS = {
    "overview",
    "summary",
    "general",
    "market",
}

_COMMON_NON_TICKERS = {
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


def _duration_ms(started_at: str | None, finished_at: str | None) -> float | None:
    if not started_at or not finished_at:
        return None
    try:
        start = datetime.fromisoformat(started_at)
        end = datetime.fromisoformat(finished_at)
        return max((end - start).total_seconds() * 1000, 0.0)
    except Exception:
        return None


def _ensure_execution_metadata(state: GraphState) -> dict[str, Any]:
    execution_metadata = dict(state.get("execution_metadata", {}) or {})
    execution_metadata.setdefault("nodes", {})
    execution_metadata.setdefault("tools", {})
    execution_metadata.setdefault("traces", [])
    execution_metadata.setdefault("errors", [])
    return execution_metadata


def _ensure_list_field(state: GraphState, key: str) -> list[Any]:
    return list(state.get(key, []) or [])


def _append_error(state: GraphState, error_message: str) -> GraphState:
    errors = _ensure_list_field(state, "errors")
    errors.append(error_message)

    execution_metadata = _ensure_execution_metadata(state)
    meta_errors = list(execution_metadata.get("errors", []) or [])
    meta_errors.append(error_message)
    execution_metadata["errors"] = meta_errors

    return {**state, "errors": errors, "execution_metadata": execution_metadata}


def _record_node_start(state: GraphState, node_name: str) -> GraphState:
    execution_metadata = _ensure_execution_metadata(state)
    nodes = dict(execution_metadata.get("nodes", {}) or {})
    node_meta = dict(nodes.get(node_name, {}) or {})

    started_at = _get_timestamp()
    node_meta["started_at"] = started_at
    node_meta.setdefault("finished_at", None)
    node_meta.setdefault("duration_ms", 0)
    nodes[node_name] = node_meta
    execution_metadata["nodes"] = nodes

    logger.info("Node started", node=node_name, request_id=state.get("request_id"))
    return {**state, "execution_metadata": execution_metadata}


def _record_node_finish(
    state: GraphState,
    node_name: str,
    *,
    ok: bool,
    error: str | None = None,
) -> GraphState:
    execution_metadata = _ensure_execution_metadata(state)
    nodes = dict(execution_metadata.get("nodes", {}) or {})
    node_meta = dict(nodes.get(node_name, {}) or {})

    finished_at = _get_timestamp()
    started_at = node_meta.get("started_at")
    duration = _duration_ms(started_at, finished_at)

    node_meta["ok"] = ok
    node_meta["error"] = error
    node_meta["finished_at"] = finished_at
    node_meta["duration_ms"] = int(duration) if duration is not None else 0
    nodes[node_name] = node_meta
    execution_metadata["nodes"] = nodes

    traces = list(execution_metadata.get("traces", []) or [])
    traces.append(
        {
            "node_name": node_name,
            "start_time": started_at,
            "end_time": finished_at,
            "duration_ms": duration,
            "success": ok,
            "error": error,
        }
    )
    execution_metadata["traces"] = traces

    if ok:
        logger.info("Node completed", node=node_name, request_id=state.get("request_id"))
    else:
        logger.warning(
            "Node failed",
            node=node_name,
            error=error,
            request_id=state.get("request_id"),
        )

    return {**state, "execution_metadata": execution_metadata}


def _set_tool_node_contract(
    state: GraphState,
    *,
    tool_node_name: str,
    ok: bool,
    duration_ms: float = 0,
    error: str | None = None,
    skipped: bool = False,
    reason: str | None = None,
    cached: bool = False,
) -> GraphState:
    execution_metadata = _ensure_execution_metadata(state)
    nodes = dict(execution_metadata.get("nodes", {}) or {})
    node_meta = dict(nodes.get(tool_node_name, {}) or {})

    node_meta["ok"] = ok
    node_meta["duration_ms"] = int(duration_ms) if duration_ms is not None else 0
    node_meta["cached"] = bool(cached)
    node_meta["error"] = error
    node_meta["skipped"] = bool(skipped)
    node_meta["reason"] = reason
    nodes[tool_node_name] = node_meta
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
        "duration_ms": _duration_ms(started_at, finished_at),
        "result": result,
    }
    execution_metadata["tools"] = tools

    logger.info("Tool completed", tool=tool_name, ok=ok, request_id=state.get("request_id"))
    return {**state, "execution_metadata": execution_metadata}


def _mark_tool_completion(state: GraphState, *, tool_name: str, ok: bool) -> GraphState:
    completed_tools = _ensure_list_field(state, "completed_tools")
    failed_tools = _ensure_list_field(state, "failed_tools")

    if ok:
        if tool_name not in completed_tools:
            completed_tools.append(tool_name)
    else:
        if tool_name not in failed_tools:
            failed_tools.append(tool_name)

    return {**state, "completed_tools": completed_tools, "failed_tools": failed_tools}


def _classify_intent(query: str) -> str:
    q = query.lower()
    tokens = set(q.split())

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


def _select_tools(intent: str) -> tuple[list[str], list[str]]:
    if intent == "fundamentals":
        return (["market_data_tool"], ["news_tool", "sentiment_tool"])
    if intent == "news":
        return (["news_tool", "sentiment_tool"], ["market_data_tool"])
    if intent == "sentiment":
        return (["news_tool", "sentiment_tool"], ["market_data_tool"])
    if intent == "market_overview":
        return (["news_tool"], ["market_data_tool", "sentiment_tool"])
    return (["market_data_tool", "news_tool", "sentiment_tool"], [])


def _extract_ticker(query: str) -> str | None:
    matches = _TICKER_RE.findall(query.upper())
    filtered = [m for m in matches if m not in _COMMON_NON_TICKERS]
    return filtered[-1] if filtered else None


async def router_node(state: GraphState) -> GraphState:
    state = _record_node_start(state, "router")

    try:
        user_query = state.get("user_query", "")
        executed_nodes = _ensure_list_field(state, "executed_nodes")
        if "router" not in executed_nodes:
            executed_nodes.append("router")

        if not user_query or not user_query.strip():
            state = _append_error(state, "Query is empty.")
            state = {**state, "ticker": None, "status": "failed", "executed_nodes": executed_nodes}
            return _record_node_finish(state, "router", ok=False, error="Empty query")

        ticker = _extract_ticker(user_query)
        if ticker is None:
            state = _append_error(state, "Ticker could not be extracted from query.")
            state = {**state, "ticker": None, "status": "failed", "executed_nodes": executed_nodes}
            return _record_node_finish(state, "router", ok=False, error="Ticker extraction failed")

        detected_intent = _classify_intent(user_query)
        selected_tools, skipped_tools = _select_tools(detected_intent)

        execution_metadata = _ensure_execution_metadata(state)
        execution_metadata["detected_intent"] = detected_intent
        execution_metadata["selected_tools"] = list(selected_tools)
        execution_metadata["skipped_tools"] = list(skipped_tools)

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
            "execution_metadata": execution_metadata,
        }

        logger.info(
            "Routing decision",
            intent=detected_intent,
            selected_tools=selected_tools,
            skipped_tools=skipped_tools,
            request_id=state.get("request_id"),
        )

        return _record_node_finish(state, "router", ok=True)
    except Exception as exc:
        executed_nodes = _ensure_list_field(state, "executed_nodes")
        if "router" not in executed_nodes:
            executed_nodes.append("router")
        state = _append_error(state, f"Router error: {exc!s}")
        state = {**state, "status": "failed", "executed_nodes": executed_nodes}
        return _record_node_finish(state, "router", ok=False, error=str(exc))


async def market_data_node(state: GraphState) -> GraphState:
    return await market_data_tool_node(state)


async def market_data_tool_node(state: GraphState) -> GraphState:
    state = _record_node_start(state, "market_data_tool")

    executed_nodes = _ensure_list_field(state, "executed_nodes")
    if "market_data_tool" not in executed_nodes:
        executed_nodes.append("market_data_tool")

    ticker = state.get("ticker")
    if not ticker:
        state = _append_error(state, "Ticker missing; cannot run Market Data Tool.")
        state = _set_tool_node_contract(
            {**state, "market_data": {}, "executed_nodes": executed_nodes},
            tool_node_name="market_data_tool",
            ok=False,
            error="No ticker",
        )
        state = _mark_tool_completion(state, tool_name="market_data_tool", ok=False)
        return _record_node_finish(state, "market_data_tool", ok=False, error="No ticker")

    started_at = _get_timestamp()
    try:
        result = await fetch_market_data(ticker)
    except Exception as exc:
        result = {"error": str(exc), "error_type": "exception"}
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
    state = _mark_tool_completion(state, tool_name="market_data_tool", ok=ok)
    state = _set_tool_node_contract(
        state,
        tool_node_name="market_data_tool",
        ok=ok,
        duration_ms=_duration_ms(started_at, finished_at) or 0,
        error=None if ok else result.get("error"),
    )

    if ok:
        state = {**state, "market_data": result, "executed_nodes": executed_nodes}
    else:
        state = _append_error(state, f"Market Data Tool failed: {result.get('error')}")
        state = {**state, "market_data": {}, "executed_nodes": executed_nodes}

    return _record_node_finish(state, "market_data_tool", ok=ok, error=None if ok else result.get("error"))


async def news_tool_node(state: GraphState) -> GraphState:
    state = _record_node_start(state, "news_tool")

    executed_nodes = _ensure_list_field(state, "executed_nodes")
    if "news_tool" not in executed_nodes:
        executed_nodes.append("news_tool")

    ticker = state.get("ticker")
    if not ticker:
        state = _append_error(state, "Ticker missing; cannot run News Tool.")
        state = _set_tool_node_contract(
            {**state, "news": {}, "executed_nodes": executed_nodes},
            tool_node_name="news_tool",
            ok=False,
            error="No ticker",
        )
        state = _mark_tool_completion(state, tool_name="news_tool", ok=False)
        return _record_node_finish(state, "news_tool", ok=False, error="No ticker")

    started_at = _get_timestamp()
    try:
        result = await fetch_news(tickers=[ticker], date_from=None, date_to=None, limit=20)
    except Exception as exc:
        result = {"error": str(exc), "error_type": "exception"}
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
    state = _mark_tool_completion(state, tool_name="news_tool", ok=ok)
    state = _set_tool_node_contract(
        state,
        tool_node_name="news_tool",
        ok=ok,
        duration_ms=_duration_ms(started_at, finished_at) or 0,
        error=None if ok else result.get("error"),
    )

    if ok:
        state = {**state, "news": result, "executed_nodes": executed_nodes}
    else:
        state = _append_error(state, f"News Tool failed: {result.get('error')}")
        state = {**state, "news": {}, "executed_nodes": executed_nodes}

    return _record_node_finish(state, "news_tool", ok=ok, error=None if ok else result.get("error"))


async def sentiment_tool_node(state: GraphState) -> GraphState:
    state = _record_node_start(state, "sentiment_tool")

    executed_nodes = _ensure_list_field(state, "executed_nodes")
    if "sentiment_tool" not in executed_nodes:
        executed_nodes.append("sentiment_tool")

    ticker = state.get("ticker")
    news_result = state.get("news") or {}
    articles = news_result.get("articles", []) if isinstance(news_result, dict) else []

    started_at = _get_timestamp()
    try:
        result = await analyze_sentiment(articles=articles, tickers=[ticker] if ticker else [])
    except Exception as exc:
        result = {"ok": False, "error": str(exc)}
    finished_at = _get_timestamp()

    ok = bool(result.get("ok")) if "ok" in result else ("error" not in result)
    err = result.get("error")
    if isinstance(err, dict):
        err = err.get("message") or str(err)

    skipped = len(articles) == 0
    reason = "No news articles" if skipped else None

    state = _record_tool_result(
        state,
        tool_name="sentiment_tool",
        ok=ok,
        started_at=started_at,
        finished_at=finished_at,
        result=result,
    )
    state = _mark_tool_completion(state, tool_name="sentiment_tool", ok=ok)
    state = _set_tool_node_contract(
        state,
        tool_node_name="sentiment_tool",
        ok=ok,
        duration_ms=_duration_ms(started_at, finished_at) or 0,
        error=None if ok else err,
        skipped=skipped,
        reason=reason,
    )

    if ok:
        state = {**state, "sentiment": result, "executed_nodes": executed_nodes}
    else:
        state = _append_error(state, f"Sentiment Tool failed: {err}")
        state = {**state, "sentiment": {}, "executed_nodes": executed_nodes}

    return _record_node_finish(state, "sentiment_tool", ok=ok, error=None if ok else err)


async def parallel_tools_node(state: GraphState) -> GraphState:
    state = _record_node_start(state, "parallel_tools")

    executed_nodes = _ensure_list_field(state, "executed_nodes")
    if "parallel_tools" not in executed_nodes:
        executed_nodes.append("parallel_tools")

    ticker = state.get("ticker")
    if not ticker:
        state = _append_error(state, "Ticker missing; cannot run parallel tools.")
        state = {
            **state,
            "market_data": {},
            "news": {},
            "sentiment": {},
            "status": "failed",
            "executed_nodes": executed_nodes,
        }
        return _record_node_finish(state, "parallel_tools", ok=False, error="No ticker")

    selected_tools = set(state.get("selected_tools") or [])

    for tool_name in ("market_data_tool", "news_tool", "sentiment_tool"):
        if tool_name in selected_tools and tool_name not in executed_nodes:
            executed_nodes.append(tool_name)

    state = {**state, "market_data": state.get("market_data") or {}, "news": state.get("news") or {}, "sentiment": state.get("sentiment") or {}}

    async def _run_market() -> tuple[bool, dict[str, Any], str, str]:
        started_at = _get_timestamp()
        try:
            result = await fetch_market_data(ticker)
        except Exception as exc:
            result = {"error": str(exc), "error_type": "exception"}
        finished_at = _get_timestamp()
        return ("error" not in result), result, started_at, finished_at

    async def _run_news() -> tuple[bool, dict[str, Any], str, str]:
        started_at = _get_timestamp()
        try:
            result = await fetch_news(tickers=[ticker], date_from=None, date_to=None, limit=20)
        except Exception as exc:
            result = {"error": str(exc), "error_type": "exception"}
        finished_at = _get_timestamp()
        return ("error" not in result), result, started_at, finished_at

    market_ok = False
    news_ok = False
    market_result: dict[str, Any] = {}
    news_result: dict[str, Any] = {}

    tasks: dict[str, asyncio.Task[tuple[bool, dict[str, Any], str, str]]] = {}
    if "market_data_tool" in selected_tools:
        tasks["market_data_tool"] = asyncio.create_task(_run_market())
    if "news_tool" in selected_tools:
        tasks["news_tool"] = asyncio.create_task(_run_news())

    if tasks:
        names = list(tasks.keys())
        results = await asyncio.gather(*(tasks[n] for n in names), return_exceptions=True)
        for name, outcome in zip(names, results):
            if isinstance(outcome, Exception):
                ok = False
                result = {"error": str(outcome), "error_type": "exception"}
                started_at = _get_timestamp()
                finished_at = _get_timestamp()
            else:
                ok, result, started_at, finished_at = outcome

            state = _record_tool_result(
                state,
                tool_name=name,
                ok=ok,
                started_at=started_at,
                finished_at=finished_at,
                result=result,
            )
            state = _mark_tool_completion(state, tool_name=name, ok=ok)
            state = _set_tool_node_contract(
                state,
                tool_node_name=name,
                ok=ok,
                duration_ms=_duration_ms(started_at, finished_at) or 0,
                error=None if ok else result.get("error"),
            )

            if name == "market_data_tool":
                market_ok = ok
                market_result = result
                if ok:
                    state = {**state, "market_data": result}
                else:
                    state = _append_error(state, f"Market Data Tool failed: {result.get('error')}")
                    state = {**state, "market_data": {}}

            if name == "news_tool":
                news_ok = ok
                news_result = result
                if ok:
                    state = {**state, "news": result}
                else:
                    state = _append_error(state, f"News Tool failed: {result.get('error')}")
                    state = {**state, "news": {}}

    if "market_data_tool" not in selected_tools:
        state = {**state, "market_data": {}}
    if "news_tool" not in selected_tools:
        state = {**state, "news": {}}

    if "sentiment_tool" in selected_tools:
        sentiment_enabled = True
        try:
            from backend.config import settings

            sentiment_enabled = bool(getattr(settings, "enable_sentiment_analysis", True))
        except Exception:
            sentiment_enabled = True

        if not sentiment_enabled:
            state = _set_tool_node_contract(
                state,
                tool_node_name="sentiment_tool",
                ok=True,
                skipped=True,
                reason="Sentiment analysis disabled",
            )
            state = {**state, "sentiment": {}}
        else:
            articles: list[Any] = []
            if news_ok and isinstance(news_result, dict):
                articles = news_result.get("articles", []) or []
            else:
                from_state_news = state.get("news") or {}
                if isinstance(from_state_news, dict):
                    articles = from_state_news.get("articles", []) or []

            sentiment_started_at = _get_timestamp()
            try:
                sentiment_result = await analyze_sentiment(articles=articles, tickers=[ticker])
            except Exception as exc:
                sentiment_result = {"ok": False, "error": str(exc)}
            sentiment_finished_at = _get_timestamp()

            sentiment_ok = (
                bool(sentiment_result.get("ok")) if "ok" in sentiment_result else ("error" not in sentiment_result)
            )
            sentiment_error = sentiment_result.get("error")
            if isinstance(sentiment_error, dict):
                sentiment_error = sentiment_error.get("message") or str(sentiment_error)

            state = _record_tool_result(
                state,
                tool_name="sentiment_tool",
                ok=sentiment_ok,
                started_at=sentiment_started_at,
                finished_at=sentiment_finished_at,
                result=sentiment_result,
            )
            state = _mark_tool_completion(state, tool_name="sentiment_tool", ok=sentiment_ok)
            state = _set_tool_node_contract(
                state,
                tool_node_name="sentiment_tool",
                ok=sentiment_ok,
                duration_ms=_duration_ms(sentiment_started_at, sentiment_finished_at) or 0,
                error=None if sentiment_ok else sentiment_error,
                skipped=len(articles) == 0,
                reason="No news articles" if len(articles) == 0 else None,
            )

            if sentiment_ok:
                state = {**state, "sentiment": sentiment_result}
            else:
                state = _append_error(state, f"Sentiment Tool failed: {sentiment_error}")
                state = {**state, "sentiment": {}}
    else:
        state = {**state, "sentiment": {}}

    ok_any = bool(market_ok or news_ok)
    state = {**state, "executed_nodes": executed_nodes}
    return _record_node_finish(
        state,
        "parallel_tools",
        ok=ok_any,
        error=None if ok_any else "All parallel selected tools failed",
    )


async def merge_results_node(state: GraphState) -> GraphState:
    state = _record_node_start(state, "merge_results")

    executed_nodes = _ensure_list_field(state, "executed_nodes")
    if "merge_results" not in executed_nodes:
        executed_nodes.append("merge_results")

    state = {**state, "executed_nodes": executed_nodes}
    return _record_node_finish(state, "merge_results", ok=True)


async def research_node(state: GraphState) -> GraphState:
    state = _record_node_start(state, "research")

    executed_nodes = _ensure_list_field(state, "executed_nodes")
    if "research" not in executed_nodes:
        executed_nodes.append("research")

    ticker = state.get("ticker")
    report = (
        f"Placeholder research report for {ticker}. "
        f"Includes market_data and/or news results where available. "
        f"(No LLM integration.)"
    )

    state = {**state, "report": report, "executed_nodes": executed_nodes}

    state_status = state.get("status", "pending")
    if state_status not in ("success", "failed"):
        has_market = bool(state.get("market_data"))
        has_news = bool(state.get("news"))
        state_status = "success" if (has_market or has_news) else "failed"

    completed_at = _get_timestamp()
    started_at = state.get("started_at")
    total_ms = _duration_ms(started_at, completed_at)

    execution_metadata = _ensure_execution_metadata(state)
    if total_ms is not None:
        execution_metadata["execution_time_ms"] = total_ms

    state = {
        **state,
        "status": state_status,
        "completed_at": completed_at,
        "execution_duration_ms": total_ms,
        "execution_metadata": execution_metadata,
    }

    ok = state_status == "success"
    if not ok:
        state = _append_error(state, "Research produced but no tool data available")

    return _record_node_finish(
        state,
        "research",
        ok=ok,
        error=None if ok else "Research produced but no tool data",
    )
