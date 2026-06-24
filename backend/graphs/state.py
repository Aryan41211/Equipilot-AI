from typing import TypedDict, List, Dict, Any, Optional


class GraphState(TypedDict):
    """
    Minimal state for the first LangGraph workflow.
    """

    # Input
    user_query: str

    # Routing/Data
    ticker: Optional[str]

    # Execution tracking
    status: str  # pending | success | failed
    executed_nodes: List[str]

    # Data
    market_data: Dict[str, Any]
    report: str

    # Errors
    errors: List[str]
