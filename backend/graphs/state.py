from typing import TypedDict, List, Dict, Any, Optional


class GraphState(TypedDict):
    """
    Minimal state for the first LangGraph workflow.
    """

    # Required by task
    user_query: str
    ticker: Optional[str]
    market_data: Dict[str, Any]
    report: str
    errors: List[str]

    # Execution
    status: str  # pending | success | failed
    executed_nodes: List[str]
