from typing import TypedDict, List, Dict, Any, Optional


# NOTE: `langgraph.StateGraph` treats TypedDict keys as *channels/state keys*.
# We must not create nodes whose name collides with these keys (e.g. "market_data").
class GraphState(TypedDict):
    """
    State schema for the tool-integration milestone (Market Data + News).
    """

    # Required by task
    user_query: str
    ticker: Optional[str]

    # Tool outputs (extend graph state only where necessary)
    market_data: Dict[str, Any]
    news: Dict[str, Any]

    # Placeholder research output
    report: str

    # Error tracking
    errors: List[str]

    # Execution metadata (node/tool tracking, timings, success flags)
    execution_metadata: Dict[str, Any]

    # Execution
    status: str  # pending | success | failed
    executed_nodes: List[str]
