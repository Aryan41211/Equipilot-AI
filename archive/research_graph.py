# LangGraph workflow for equity research

from datetime import datetime
from typing import Literal, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from backend.agents.market_agent import MarketAgent
from backend.agents.news_agent import NewsAgent
from backend.agents.router_agent import RouterAgent
from backend.agents.sentiment_agent import SentimentAgent
from backend.agents.synthesis_agent import SynthesisAgent
from backend.schemas.market_data import MarketData
from backend.schemas.news import NewsArticle, NewsResponse
from backend.schemas.report import ResearchReport
from backend.schemas.research import ResearchStatus
from backend.schemas.sentiment import SentimentAnalysis
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ResearchState(TypedDict):
    """State schema for the research workflow."""

    # Input
    query: str
    explicit_tickers: list[str] | None
    date_from: datetime | None
    date_to: datetime | None
    include_news: bool
    include_sentiment: bool
    include_fundamentals: bool
    include_technicals: bool
    max_report_length: int

    # Routing
    category: str | None
    confidence: float | None
    reasoning: str | None
    tickers: list[str]
    required_sources: dict[str, bool]

    # Data
    market_data: dict[str, MarketData]
    news_response: NewsResponse | None
    news_articles: list[NewsArticle]
    sentiment_analysis: SentimentAnalysis | None

    # Output
    report: ResearchReport | None

    # Metadata
    request_id: str
    status: ResearchStatus
    current_step: str
    errors: list[str]
    started_at: datetime
    completed_at: datetime | None


router_agent: RouterAgent | None = None
market_agent: MarketAgent | None = None
news_agent: NewsAgent | None = None
sentiment_agent: SentimentAgent | None = None
synthesis_agent: SynthesisAgent | None = None


def create_research_graph() -> StateGraph:
    """Create the LangGraph research workflow."""

    global router_agent, market_agent, news_agent, sentiment_agent, synthesis_agent

    # Initialize agents (assign to module-scoped variables used by node functions)
    router_agent = RouterAgent()
    market_agent = MarketAgent()
    news_agent = NewsAgent()
    sentiment_agent = SentimentAgent()
    synthesis_agent = SynthesisAgent()

    # Define the graph
    workflow = StateGraph(ResearchState)

    # Add nodes
    workflow.add_node("router", router_node)
    workflow.add_node("market_data", market_data_node)
    workflow.add_node("news", news_node)
    workflow.add_node("sentiment", sentiment_node)
    workflow.add_node("synthesis", synthesis_node)
    workflow.add_node("finalize", finalize_node)

    # Define edges
    workflow.set_entry_point("router")

    # Router decides what data to fetch
    workflow.add_conditional_edges(
        "router",
        route_after_router,
        {
            "market_data": "market_data",
            "news": "news",
            "sentiment": "sentiment",
            "synthesis": "synthesis",
        }
    )

    # Market data -> next needed source
    workflow.add_conditional_edges(
        "market_data",
        route_after_market,
        {
            "news": "news",
            "sentiment": "sentiment",
            "synthesis": "synthesis",
        }
    )

    # News -> sentiment or synthesis
    workflow.add_conditional_edges(
        "news",
        route_after_news,
        {
            "sentiment": "sentiment",
            "synthesis": "synthesis",
        }
    )

    # Sentiment -> synthesis
    workflow.add_edge("sentiment", "synthesis")

    # Synthesis -> finalize
    workflow.add_edge("synthesis", "finalize")
    workflow.add_edge("finalize", END)

    # Compile with memory
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


# Node implementations
async def router_node(state: ResearchState) -> ResearchState:
    """Route the query and determine required data sources."""
    logger.info("Node: router", request_id=state["request_id"])

    try:
        if router_agent is None:
            raise RuntimeError("RouterAgent not initialized")
        routing = await router_agent.route(state["query"], state.get("explicit_tickers"))

        return {
            **state,
            "category": routing["category"],
            "confidence": routing["confidence"],
            "reasoning": routing["reasoning"],
            "tickers": routing["tickers"],
            "required_sources": routing["required_sources"],
            "current_step": "routing_complete",
            "status": ResearchStatus.IN_PROGRESS,
        }
    except Exception as e:
        logger.error("Router failed", error=str(e))
        return {
            **state,
            "errors": state["errors"] + [f"Router error: {e!s}"],
            "status": ResearchStatus.FAILED,
        }


async def market_data_node(state: ResearchState) -> ResearchState:
    """Fetch market data for tickers."""
    logger.info("Node: market_data", request_id=state["request_id"], tickers=state["tickers"])

    try:
        if market_agent is None:
            raise RuntimeError("MarketAgent not initialized")
        market_data = await market_agent.fetch(
            tickers=state["tickers"],
            period="1y",
            include_fundamentals=state.get("include_fundamentals", True),
            include_technicals=state.get("include_technicals", False),
        )

        return {
            **state,
            "market_data": market_data,
            "current_step": "market_data_complete",
        }
    except Exception as e:
        logger.error("Market data failed", error=str(e))
        return {
            **state,
            "errors": state["errors"] + [f"Market data error: {e!s}"],
            "market_data": {},
        }


async def news_node(state: ResearchState) -> ResearchState:
    """Fetch news articles for tickers."""
    logger.info("Node: news", request_id=state["request_id"], tickers=state["tickers"])

    try:
        if news_agent is None:
            raise RuntimeError("NewsAgent not initialized")
        news_response = await news_agent.fetch(
            tickers=state["tickers"],
            date_from=state.get("date_from"),
            date_to=state.get("date_to"),
            limit=20,
        )

        return {
            **state,
            "news_response": news_response,
            "news_articles": news_response.articles,
            "current_step": "news_complete",
        }
    except Exception as e:
        logger.error("News fetch failed", error=str(e))
        return {
            **state,
            "errors": state["errors"] + [f"News error: {e!s}"],
            "news_articles": [],
        }


async def sentiment_node(state: ResearchState) -> ResearchState:
    """Analyze sentiment of news articles."""
    logger.info("Node: sentiment", request_id=state["request_id"])

    try:
        if not state["news_articles"]:
            return {
                **state,
                "sentiment_analysis": None,
                "current_step": "sentiment_complete",
            }

        if sentiment_agent is None:
            raise RuntimeError("SentimentAgent not initialized")
        sentiment = await sentiment_agent.analyze(
            articles=state["news_articles"],
            tickers=state["tickers"],
        )

        return {
            **state,
            "sentiment_analysis": sentiment,
            "current_step": "sentiment_complete",
        }
    except Exception as e:
        logger.error("Sentiment analysis failed", error=str(e))
        return {
            **state,
            "errors": state["errors"] + [f"Sentiment error: {e!s}"],
            "sentiment_analysis": None,
        }


async def synthesis_node(state: ResearchState) -> ResearchState:
    """Generate research report."""
    logger.info("Node: synthesis", request_id=state["request_id"])

    try:
        if synthesis_agent is None:
            raise RuntimeError("SynthesisAgent not initialized")
        report = await synthesis_agent.generate_report(
            query=state["query"],
            tickers=state["tickers"],
            market_data=state["market_data"],
            news_articles=state["news_articles"],
            sentiment_analysis=state.get("sentiment_analysis"),
            max_length=state.get("max_report_length", 5000),
        )

        report.request_id = state["request_id"]

        return {
            **state,
            "report": report,
            "current_step": "synthesis_complete",
        }
    except Exception as e:
        logger.error("Synthesis failed", error=str(e))
        return {
            **state,
            "errors": state["errors"] + [f"Synthesis error: {e!s}"],
            "report": None,
        }


async def finalize_node(state: ResearchState) -> ResearchState:
    """Finalize the research request."""
    logger.info("Node: finalize", request_id=state["request_id"])

    status = ResearchStatus.COMPLETED if state.get("report") else ResearchStatus.FAILED

    return {
        **state,
        "status": status,
        "completed_at": datetime.utcnow(),
        "current_step": "completed",
    }


# Routing functions
def route_after_router(state: ResearchState) -> Literal["market_data", "news", "sentiment", "synthesis"]:
    """Determine next node after routing."""
    sources = state.get("required_sources", {})

    if sources.get("market_data"):
        return "market_data"
    elif sources.get("news"):
        return "news"
    elif sources.get("sentiment"):
        return "sentiment"
    else:
        return "synthesis"


def route_after_market(state: ResearchState) -> Literal["news", "sentiment", "synthesis"]:
    """Determine next node after market data."""
    sources = state.get("required_sources", {})

    if sources.get("news"):
        return "news"
    elif sources.get("sentiment"):
        return "sentiment"
    else:
        return "synthesis"


def route_after_news(state: ResearchState) -> Literal["sentiment", "synthesis"]:
    """Determine next node after news."""
    sources = state.get("required_sources", {})

    if sources.get("sentiment") and state.get("news_articles"):
        return "sentiment"
    else:
        return "synthesis"


# Helper to create initial state
def create_initial_state(
    request_id: str,
    query: str,
    explicit_tickers: list[str] | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    include_news: bool = True,
    include_sentiment: bool = True,
    include_fundamentals: bool = True,
    include_technicals: bool = False,
    max_report_length: int = 5000,
) -> ResearchState:
    """Create initial state for research workflow."""
    return ResearchState(
        query=query,
        explicit_tickers=explicit_tickers,
        date_from=date_from,
        date_to=date_to,
        include_news=include_news,
        include_sentiment=include_sentiment,
        include_fundamentals=include_fundamentals,
        include_technicals=include_technicals,
        max_report_length=max_report_length,
        category=None,
        confidence=None,
        reasoning=None,
        tickers=[],
        required_sources={},
        market_data={},
        news_response=None,
        news_articles=[],
        sentiment_analysis=None,
        report=None,
        request_id=request_id,
        status=ResearchStatus.PENDING,
        current_step="initialized",
        errors=[],
        started_at=datetime.utcnow(),
        completed_at=None,
    )
