from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SentimentScore(BaseModel):
    """Sentiment scoring for an entity/headline."""

    label: str = Field(..., description="positive|negative|neutral")
    confidence: float = Field(..., ge=0.0, le=1.0)
    score: float = Field(..., ge=-1.0, le=1.0, description="Normalized sentiment score [-1, 1]")


class HeadlineSentiment(BaseModel):
    """Sentiment for a single headline/article."""

    headline: str
    ticker: str | None = None
    label: str = Field(..., description="positive|negative|neutral")
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str


class SentimentProcessingMetadata(BaseModel):
    """Operational metadata for a sentiment run."""

    article_count: int = 0
    tickers_provided: list[str] = Field(default_factory=list)


class SentimentAnalysis(BaseModel):
    """Structured sentiment result for news headlines."""

    overall_sentiment: SentimentScore
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence across headlines")
    reasoning: str

    headline_sentiments: list[HeadlineSentiment] = Field(default_factory=list)
    processing_metadata: SentimentProcessingMetadata = Field(default_factory=SentimentProcessingMetadata)

    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    model_used: str = "gpt-4o-mini"

    model_config = ConfigDict(extra="forbid")
