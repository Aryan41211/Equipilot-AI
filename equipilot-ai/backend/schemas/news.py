# EquiPilot AI - News Schemas
# Pydantic models for news article structures

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl


class NewsArticle(BaseModel):
    """Individual news article."""

    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    url: HttpUrl
    source: str
    author: Optional[str] = None
    published_at: datetime
    category: Optional[str] = None
    language: str = "en"
    country: Optional[str] = None

    # Relevance scoring
    relevance_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    tickers_mentioned: List[str] = Field(default_factory=list)

    # Metadata
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    provider: str = "unknown"

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class NewsResponse(BaseModel):
    """Response model for news requests."""

    query: str
    tickers: List[str]
    articles: List[NewsArticle]
    total_results: int
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    provider: str
    errors: List[str] = Field(default_factory=list)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class NewsSearchParams(BaseModel):
    """Parameters for news search."""

    tickers: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sources: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    languages: List[str] = Field(default=["en"])
    sort_by: str = Field(default="publishedAt", description="publishedAt, relevance, popularity")
    page_size: int = Field(default=20, ge=1, le=100)
    page: int = Field(default=1, ge=1)