# EquiPilot AI - Backend Schemas Package
# Pydantic models for request/response validation

from backend.schemas.research import (
    ResearchRequest,
    ResearchResponse,
    ResearchStatus,
)
from backend.schemas.market_data import MarketData, PriceData, FundamentalsData
from backend.schemas.news import NewsArticle, NewsResponse
from backend.schemas.sentiment import SentimentAnalysis, SentimentScore
from backend.schemas.report import ResearchReport, ReportSection, Citation
from backend.schemas.research_report import SynthesizedReport

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