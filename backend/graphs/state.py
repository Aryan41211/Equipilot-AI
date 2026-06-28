from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime


def _get_timestamp() -> str:
    return datetime.utcnow().isoformat()


class ExecutionTrace(TypedDict):
    """Structured execution trace for a single node."""
    node_name: str
    start_time: str
    end_time: Optional[str]
    duration_ms: Optional[float]
    success: bool
    error: Optional[str]


# NOTE: `langgraph.StateGraph` treats TypedDict keys as *channels/state keys*.
# We must not create nodes whose name collides with these keys (e.g. "market_data").
class GraphState(TypedDict):
    """
    State schema for the dynamically routed tool-integration milestone.
    """

    # Input
    user_query: str
    ticker: Optional[str]

    # Request metadata
    request_id: str
    started_at: str
    completed_at: Optional[str]
    execution_duration_ms: Optional[float]

    # Routing
    detected_intent: str  # fundamentals | news | sentiment | full_research | market_overview
    selected_tools: List[str]
    skipped_tools: List[str]
    completed_tools: List[str]
    failed_tools: List[str]

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
