from typing import TypedDict, List, Dict, Any


class GraphState(TypedDict):
    """
    Minimal state for the first LangGraph workflow.

    Required fields (as per task):
    - user_query
    - ticker
    - market_data
    - report
    - errors
    """

    user_query: str
    ticker: str
    market_data: Dict[str, Any]
    report: str
    errors: List[str]
