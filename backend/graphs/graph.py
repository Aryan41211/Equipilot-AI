from __future__ import annotations

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from backend.graphs.nodes import (
    router_node,
    market_data_tool_node,
    news_tool_node,
    merge_results_node,
    research_node,
)
from backend.graphs.state import GraphState


def create_first_graph():
    """
    Create the first minimal LangGraph workflow:

    START -> router -> market_data_tool -> news_tool -> merge_results -> research -> END
    """
    workflow = StateGraph(GraphState)

    workflow.add_node("router", router_node)
    workflow.add_node("market_data_tool", market_data_tool_node)
    workflow.add_node("news_tool", news_tool_node)
    workflow.add_node("merge_results", merge_results_node)
    workflow.add_node("research", research_node)

    workflow.add_edge(START, "router")
    workflow.add_edge("router", "market_data_tool")
    workflow.add_edge("market_data_tool", "news_tool")
    workflow.add_edge("news_tool", "merge_results")
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
        status="pending",
        executed_nodes=[],
        market_data={},
        report="",
        errors=[],
    )
