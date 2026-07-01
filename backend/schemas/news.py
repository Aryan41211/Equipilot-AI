# EquiPilot AI - News Schemas
# Pydantic models for news article structures

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class NewsArticle(BaseModel):
    """Individual news article."""

    title: str
    description: str | None = None
    content: str | None = None
    url: HttpUrl
    source: str
    author: str | None = None
    published_at: datetime
    category: str | None = None
    language: str = "en"
    country: str | None = None

    # Relevance scoring
    relevance_score: float | None = Field(default=None, ge=0.0, le=1.0)
    tickers_mentioned: list[str] = Field(default_factory=list)

    # Metadata
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    provider: str = "unknown"

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class NewsResponse(BaseModel):
    """Response model for news requests."""

    query: str
    tickers: list[str]
    articles: list[NewsArticle]
    total_results: int
    date_from: datetime | None = None
    date_to: datetime | None = None
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    provider: str
    errors: list[str] = Field(default_factory=list)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class NewsSearchParams(BaseModel):
    """Parameters for news search."""

    tickers: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    date_from: datetime | None = None
    date_to: datetime | None = None
    sources: list[str] | None = None
    categories: list[str] | None = None
    languages: list[str] = Field(default=["en"])
    sort_by: str = Field(default="publishedAt", description="publishedAt, relevance, popularity")
    page_size: int = Field(default=20, ge=1, le=100)
    page: int = Field(default=1, ge=1)
