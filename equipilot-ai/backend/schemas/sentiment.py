# EquiPilot AI - Sentiment Schemas
# Pydantic models for sentiment analysis structures

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SentimentScore(BaseModel):
    """Sentiment scores for a single entity/text."""

    # Overall sentiment
    label: str = Field(..., description="positive, negative, neutral")
    score: float = Field(..., ge=-1.0, le=1.0, description="Normalized sentiment score [-1, 1]")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the prediction")

    # Detailed scores
    positive: float = Field(default=0.0, ge=0.0, le=1.0)
    negative: float = Field(default=0.0, ge=0.0, le=1.0)
    neutral: float = Field(default=0.0, ge=0.0, le=1.0)

    # Financial-specific
    bullish: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    bearish: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    # Key phrases driving sentiment
    key_phrases: List[str] = Field(default_factory=list)


class ArticleSentiment(BaseModel):
    """Sentiment analysis for a single article."""

    article_id: str
    article_title: str
    article_url: str
    published_at: datetime
    sentiment: SentimentScore
    ticker_sentiments: Dict[str, SentimentScore] = Field(default_factory=dict)
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class SentimentAnalysis(BaseModel):
    """Aggregated sentiment analysis across multiple articles."""

    # Overall sentiment
    overall_sentiment: SentimentScore

    # Per-article breakdown
    article_sentiments: List[ArticleSentiment] = Field(default_factory=list)

    # Per-ticker breakdown
    ticker_sentiments: Dict[str, SentimentScore] = Field(default_factory=dict)

    # Key themes/topics
    key_themes: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Identified themes with sentiment",
    )

    # Statistics
    total_articles: int = 0
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0
    average_confidence: float = 0.0

    # Time range
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

    # Metadata
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    model_used: str = "gpt-4o-mini"

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class SentimentRequest(BaseModel):
    """Request for sentiment analysis."""

    articles: List[Dict[str, Any]] = Field(..., description="Articles to analyze")
    tickers: List[str] = Field(default_factory=list, description="Focus tickers")
    model: str = Field(default="gpt-4o-mini", description="Model to use for analysis")