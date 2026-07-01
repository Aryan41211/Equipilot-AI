# EquiPilot AI - Router Agent
# Query classification and routing logic

from typing import Any

from backend.services.llm_service import get_llm_service
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class RouterAgent:
    """Agent for classifying queries and determining research workflow."""

    def __init__(self):
        self.llm = get_llm_service()

    async def route(
        self,
        query: str,
        explicit_tickers: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Route a research query to appropriate workflow.

        Args:
            query: User's natural language query
            explicit_tickers: Explicitly provided tickers (optional)

        Returns:
            Routing decision with category, tickers, and required data sources
        """
        logger.info("Routing query", query=query[:100])

        # Extract tickers if not provided
        if explicit_tickers:
            tickers = explicit_tickers
        else:
            tickers = await self.llm.extract_tickers(query)

        # Classify query type
        categories = [
            "company_analysis",
            "sector_analysis",
            "market_overview",
            "earnings_analysis",
            "news_sentiment",
            "comparison",
            "technical_analysis",
            "general_question",
        ]

        classification = await self.llm.classify_query(query, categories)

        # Determine required data sources based on category
        required_sources = self._determine_sources(classification.get("category", "general_question"))

        return {
            "query": query,
            "category": classification.get("category", "general_question"),
            "confidence": classification.get("confidence", 0.5),
            "reasoning": classification.get("reasoning", ""),
            "tickers": tickers,
            "required_sources": required_sources,
            "explicit_tickers": explicit_tickers or [],
        }

    def _determine_sources(self, category: str) -> dict[str, bool]:
        """Determine which data sources are needed for a category."""
        source_map = {
            "company_analysis": {
                "market_data": True,
                "fundamentals": True,
                "news": True,
                "sentiment": True,
                "technicals": False,
            },
            "sector_analysis": {
                "market_data": True,
                "fundamentals": True,
                "news": True,
                "sentiment": True,
                "technicals": False,
            },
            "market_overview": {
                "market_data": True,
                "fundamentals": False,
                "news": True,
                "sentiment": True,
                "technicals": False,
            },
            "earnings_analysis": {
                "market_data": True,
                "fundamentals": True,
                "news": True,
                "sentiment": True,
                "technicals": False,
            },
            "news_sentiment": {
                "market_data": False,
                "fundamentals": False,
                "news": True,
                "sentiment": True,
                "technicals": False,
            },
            "comparison": {
                "market_data": True,
                "fundamentals": True,
                "news": True,
                "sentiment": True,
                "technicals": False,
            },
            "technical_analysis": {
                "market_data": True,
                "fundamentals": False,
                "news": False,
                "sentiment": False,
                "technicals": True,
            },
            "general_question": {
                "market_data": False,
                "fundamentals": False,
                "news": False,
                "sentiment": False,
                "technicals": False,
            },
        }

        return source_map.get(category, source_map["general_question"])
