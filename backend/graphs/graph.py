from __future__ import annotations

from typing import Literal

from langgraph.graph import StateGraph, START, END

from backend.graphs.nodes import (
    router_node,
    market_data_tool_node,
    news_tool_node,
    sentiment_tool_node,
    merge_results_node,
    research_node,
)
from backend.graphs.state import GraphState


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
    Create the dynamically routed LangGraph workflow:

    START -> router -> [market_data_tool | news_tool] -> [news_tool | sentiment_tool | merge_results] -> research -> END
    """
    workflow = StateGraph(GraphState)

    workflow.add_node("router", router_node)
    workflow.add_node("market_data_tool", market_data_tool_node)
    workflow.add_node("news_tool", news_tool_node)
    workflow.add_node("sentiment_tool", sentiment_tool_node)
    workflow.add_node("merge_results", merge_results_node)
    workflow.add_node("research", research_node)

    workflow.set_entry_point("router")

    workflow.add_conditional_edges(
        "router",
        route_after_router,
        {
            "market_data_tool": "market_data_tool",
            "news_tool": "news_tool",
            "__end__": END,
        },
    )

    workflow.add_conditional_edges(
        "market_data_tool",
        route_after_market_data,
        {
            "merge_results": "merge_results",
            "news_tool": "news_tool",
            "__end__": END,
        },
    )

    workflow.add_conditional_edges(
        "news_tool",
        route_after_news,
        {
            "sentiment_tool": "sentiment_tool",
            "merge_results": "merge_results",
            "__end__": END,
        },
    )

    workflow.add_conditional_edges(
        "sentiment_tool",
        route_after_sentiment,
        {
            "merge_results": "merge_results",
            "__end__": END,
        },
    )

    workflow.add_edge("merge_results", "research")
    workflow.add_edge("research", END)

    # Avoid checkpointer configuration issues in test/runtime environments.
    return workflow.compile(checkpointer=False)


def create_initial_state(user_query: str) -> GraphState:
    """
    Create the initial GraphState for the first graph.
    """
    return GraphState(
        user_query=user_query,
        ticker=None,
        detected_intent="full_research",
        selected_tools=[],
        skipped_tools=[],
        execution_summary={},
        market_data={},
        news={},
        sentiment={},
        report="",
        errors=[],
        execution_metadata={},
        status="pending",
        executed_nodes=[],
    )
