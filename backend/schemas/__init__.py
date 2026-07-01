# EquiPilot AI - Backend Schemas Package
# Pydantic models for request/response validation

from backend.schemas.market_data import FundamentalsData, MarketData, PriceData
from backend.schemas.news import NewsArticle, NewsResponse
from backend.schemas.report import Citation, ReportSection, ResearchReport
from backend.schemas.research import (
    ResearchRequest,
    ResearchResponse,
    ResearchStatus,
)
from backend.schemas.research_report import SynthesizedReport
from backend.schemas.sentiment import SentimentAnalysis, SentimentScore

__all__ = [
    # Research
    "ResearchRequest",
    "ResearchResponse",
    "ResearchStatus",
    # Market Data
    "MarketData",
    "PriceData",
    "FundamentalsData",
    # News
    "NewsArticle",
    "NewsResponse",
    # Sentiment
    "SentimentAnalysis",
    "SentimentScore",
    # Report
    "ResearchReport",
    "ReportSection",
    "Citation",
    # Synthesis
    "SynthesizedReport",
]
