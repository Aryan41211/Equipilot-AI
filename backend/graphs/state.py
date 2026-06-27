from typing import TypedDict, List, Dict, Any, Optional


# NOTE: `langgraph.StateGraph` treats TypedDict keys as *channels/state keys*.
# We must not create nodes whose name collides with these keys (e.g. "market_data").
class GraphState(TypedDict):
    """
    State schema for the dynamically routed tool-integration milestone.
    """

    # Input
    user_query: str
    ticker: Optional[str]

    # Routing
    detected_intent: str  # fundamentals | news | sentiment | full_research | market_overview
    selected_tools: List[str]
    skipped_tools: List[str]
    execution_summary: Dict[str, Any]

    # Tool outputs
    market_data: Dict[str, Any]
    news: Dict[str, Any]
    sentiment: Dict[str, Any]

    # Placeholder research output
    report: str

    # Error tracking
    errors: List[str]

    # Execution metadata (node/tool tracking, timings, success flags)
    execution_metadata: Dict[str, Any]

    # Execution
    status: str  # pending | success | failed
    executed_nodes: List[str]
