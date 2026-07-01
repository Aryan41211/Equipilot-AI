from datetime import datetime
from typing import Any, TypedDict


def _get_timestamp() -> str:
    return datetime.utcnow().isoformat()


class ExecutionTrace(TypedDict):
    """Structured execution trace for a single node."""
    node_name: str
    start_time: str
    end_time: str | None
    duration_ms: float | None
    success: bool
    error: str | None


# NOTE: `langgraph.StateGraph` treats TypedDict keys as *channels/state keys*.
# We must not create nodes whose name collides with these keys (e.g. "market_data").
class GraphState(TypedDict):
    """
    State schema for the dynamically routed tool-integration milestone.
    """

    # Input
    user_query: str
    ticker: str | None

    # Request metadata
    request_id: str
    started_at: str
    completed_at: str | None
    execution_duration_ms: float | None

    # Routing
    detected_intent: str  # fundamentals | news | sentiment | full_research | market_overview
    selected_tools: list[str]
    skipped_tools: list[str]
    completed_tools: list[str]
    failed_tools: list[str]

    # Tool outputs
    market_data: dict[str, Any]
    news: dict[str, Any]
    sentiment: dict[str, Any]

    # Placeholder research output
    report: str

    # Error tracking
    errors: list[str]

    # Execution metadata (node/tool tracking, timings, success flags)
    execution_metadata: dict[str, Any]

    # Execution
    status: str  # pending | success | failed
    executed_nodes: list[str]
