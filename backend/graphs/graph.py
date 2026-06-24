from __future__ import annotations

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from backend.graphs.nodes import router_node, market_data_node, research_node
from backend.graphs.state import GraphState


def create_first_graph():
    """
    Create the first minimal LangGraph workflow:

    START -> router_node -> market_data_node -> research_node -> END
    """
    workflow = StateGraph(GraphState)

    workflow.add_node("router", router_node)
    workflow.add_node("market_data", market_data_node)
    workflow.add_node("research", research_node)

    workflow.add_edge(START, "router")
    workflow.add_edge("router", "market_data")
    workflow.add_edge("market_data", "research")
    workflow.add_edge("research", END)

    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


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
