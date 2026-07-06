from __future__ import annotations

import uuid
from typing import Literal

from langgraph.graph import END, StateGraph

from backend.graphs.nodes import (
    parallel_tools_node,
    research_node,
    router_node,
    market_data_tool_node,
    news_tool_node,
    sentiment_tool_node,
    merge_results_node,
)
from backend.graphs.state import GraphState, _get_timestamp


def route_after_router(state: GraphState) -> Literal["market_data_tool", "news_tool", "__end__"]:
    """Determine the next node after the router based on detected intent and failure state."""
    if state.get("status") == "failed":
        return "__end__"

    intent = state.get("detected_intent", "full_research")
    if intent in ("fundamentals", "full_research"):
        return "market_data_tool"
    return "news_tool"


def route_after_market_data(state: GraphState) -> Literal["merge_results", "news_tool", "__end__"]:
    """Determine the next node after market data fetch."""
    if state.get("status") == "failed":
        return "__end__"

    intent = state.get("detected_intent", "full_research")
    if intent == "fundamentals":
        return "merge_results"
    return "news_tool"


def route_after_news(state: GraphState) -> Literal["sentiment_tool", "merge_results", "__end__"]:
    """Determine the next node after news fetch."""
    if state.get("status") == "failed":
        return "__end__"

    intent = state.get("detected_intent", "full_research")
    if intent in ("news", "sentiment", "full_research"):
        return "sentiment_tool"
    return "merge_results"


def route_after_sentiment(state: GraphState) -> Literal["merge_results", "__end__"]:
    """Determine the next node after sentiment analysis."""
    if state.get("status") == "failed":
        return "__end__"
    return "merge_results"


def create_first_graph():
    """
    Create the optimized dynamically routed LangGraph workflow.

    Phase 3:
      START -> router -> parallel_tools -> research -> END

    `parallel_tools_node` runs:
      - market_data + news concurrently
      - sentiment after news (depends on news articles)
    """
    workflow = StateGraph(GraphState)

    workflow.add_node("router", router_node)
    workflow.add_node("parallel_tools", parallel_tools_node)
    workflow.add_node("research", research_node)

    # Keep legacy nodes registered for compatibility/testing, though not used
    # in the optimized main path.
    workflow.add_node("market_data_tool", market_data_tool_node)
    workflow.add_node("news_tool", news_tool_node)
    workflow.add_node("sentiment_tool", sentiment_tool_node)
    workflow.add_node("merge_results", merge_results_node)

    workflow.set_entry_point("router")

    workflow.add_conditional_edges(
        "router",
        lambda state: "__end__" if state.get("status") == "failed" else "parallel_tools",
        {
            "parallel_tools": "parallel_tools",
            "__end__": END,
        },
    )

    workflow.add_edge("parallel_tools", "merge_results")
    workflow.add_edge("merge_results", "research")
    workflow.add_edge("research", END)

    return workflow.compile(checkpointer=False)


def create_initial_state(user_query: str) -> GraphState:
    """
    Create the initial GraphState for the first graph.
    """
    return GraphState(
        user_query=user_query,
        ticker=None,
        request_id=str(uuid.uuid4()),
        started_at=_get_timestamp(),
        completed_at=None,
        execution_duration_ms=None,
        detected_intent="full_research",
        selected_tools=[],
        skipped_tools=[],
        completed_tools=[],
        failed_tools=[],
        market_data={},
        news={},
        sentiment={},
        report="",
        errors=[],
        execution_metadata={},
        status="pending",
        executed_nodes=[],
    )
