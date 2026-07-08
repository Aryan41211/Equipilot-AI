# EquiPilot AI - Research Schemas
# Request/response models for research API endpoints

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ResearchStatus(str, Enum):
    """Status of a research request."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NOT_FOUND = "not_found"


class ResearchRequest(BaseModel):
    """Request model for submitting a research query."""

    query: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Natural language research query",
        examples=["Analyze AAPL's competitive position in the smartphone market"],
    )
    tickers: list[str] | None = Field(
        default=None,
        description="Explicit ticker symbols to analyze (optional, extracted from query if not provided)",
        examples=[["AAPL", "MSFT"]],
    )
    date_from: datetime | None = Field(
        default=None,
        description="Start date for historical data and news",
    )
    date_to: datetime | None = Field(
        default=None,
        description="End date for historical data and news",
    )
    include_news: bool = Field(
        default=True,
        description="Whether to include news analysis",
    )
    include_sentiment: bool = Field(
        default=True,
        description="Whether to include sentiment analysis",
    )
    include_fundamentals: bool = Field(
        default=True,
        description="Whether to include fundamental data",
    )
    include_technicals: bool = Field(
        default=False,
        description="Whether to include technical indicators",
    )
    max_report_length: int = Field(
        default=5000,
        ge=500,
        le=20000,
        description="Maximum report length in characters",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the request",
    )

    @field_validator("tickers", mode="before")
    @classmethod
    def normalize_tickers(cls, v: list[str] | None) -> list[str] | None:
        """Normalize ticker symbols to uppercase."""
        if v is None:
            return None
        return [ticker.strip().upper() for ticker in v if ticker.strip()]


class ResearchResponse(BaseModel):
    """Response model for research requests."""

    request_id: str = Field(
        ...,
        description="Unique identifier for the research request",
    )
    status: ResearchStatus = Field(
        ...,
        description="Current status of the research request",
    )
    query: str = Field(
        ...,
        description="Original research query",
    )
    tickers: list[str] = Field(
        default_factory=list,
        description="Tickers analyzed in the research",
    )

    # Frontend-compatible execution/progress fields
    current_step: str | None = Field(
        default=None,
        description="Current workflow step identifier (for polling UI).",
    )
    execution_metadata: dict[str, Any] | None = Field(
        default=None,
        description="Structured execution metadata (nodes/tools/traces).",
    )

    report: str | None = Field(
        default=None,
        description="Generated research report (markdown format)",
    )
    sections: list[dict[str, Any]] | None = Field(
        default=None,
        description="Structured report sections",
    )
    citations: list[dict[str, Any]] | None = Field(
        default=None,
        description="Source citations for the report",
    )
    market_data_summary: dict[str, Any] | None = Field(
        default=None,
        description="Summary of market data retrieved",
    )
    news_summary: dict[str, Any] | None = Field(
        default=None,
        description="Summary of news articles analyzed",
    )
    sentiment_summary: dict[str, Any] | None = Field(
        default=None,
        description="Summary of sentiment analysis",
    )
    message: str | None = Field(
        default=None,
        description="Human-readable status message",
    )
    error: str | None = Field(
        default=None,
        description="Error message if status is FAILED",
    )
    created_at: datetime | None = Field(
        default_factory=datetime.utcnow,
        description="Request creation timestamp",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="Request completion timestamp",
    )
    processing_time_seconds: float | None = Field(
        default=None,
        description="Total processing time in seconds",
    )


class ResearchProgress(BaseModel):
    """Progress update for long-running research requests."""

    request_id: str
    status: ResearchStatus
    current_step: str
    step_progress: float = Field(ge=0.0, le=1.0)
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
