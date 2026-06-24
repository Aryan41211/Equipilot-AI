# EquiPilot AI - Backend Configuration
# Centralized configuration management using Pydantic Settings

from functools import lru_cache
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # OpenAI Configuration
    # -------------------------------------------------------------------------
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key for LLM access",
    )
    openai_model: str = Field(
        default="gpt-4o",
        description="Primary model for report synthesis",
    )
    openai_model_mini: str = Field(
        default="gpt-4o-mini",
        description="Cost-effective model for classification/sentiment",
    )
    llm_api_timeout: int = Field(
        default=60,
        description="Timeout for OpenAI API calls in seconds",
    )
    llm_max_tokens: int = Field(
        default=4000,
        description="Maximum tokens per LLM response",
    )
    llm_temperature: float = Field(
        default=0.3,
        description="Temperature for LLM generation",
    )

    # -------------------------------------------------------------------------
    # News API Configuration
    # -------------------------------------------------------------------------
    news_api_key: str = Field(
        default="",
        description="News API key (NewsAPI, Alpha Vantage, or Finnhub)",
    )
    news_api_provider: str = Field(
        default="newsapi",
        description="News provider: newsapi, alphavantage, finnhub",
    )
    news_api_timeout: int = Field(
        default=30,
        description="Timeout for news API calls in seconds",
    )
    news_max_articles: int = Field(
        default=20,
        description="Maximum articles to fetch per query",
    )
    news_lookback_days: int = Field(
        default=7,
        description="Days to look back for news articles",
    )

    # -------------------------------------------------------------------------
    # Market Data Configuration
    # -------------------------------------------------------------------------
    yfinance_cache_ttl: int = Field(
        default=300,
        description="yfinance cache TTL in seconds",
    )
    market_data_timeout: int = Field(
        default=30,
        description="Timeout for market data calls in seconds",
    )

    # -------------------------------------------------------------------------
    # Backend Server Configuration
    # -------------------------------------------------------------------------
    backend_host: str = Field(
        default="0.0.0.0",
        description="Backend server host",
    )
    backend_port: int = Field(
        default=8000,
        description="Backend server port",
    )
    backend_reload: bool = Field(
        default=True,
        description="Enable auto-reload in development",
    )

    # -------------------------------------------------------------------------
    # Frontend Configuration
    # -------------------------------------------------------------------------
    frontend_port: int = Field(
        default=8501,
        description="Streamlit frontend port",
    )

    # -------------------------------------------------------------------------
    # API Configuration
    # -------------------------------------------------------------------------
    api_prefix: str = Field(
        default="/api/v1",
        description="API route prefix",
    )
    cors_origins: List[str] = Field(
        default=["http://localhost:8501", "http://localhost:3000"],
        description="Allowed CORS origins",
    )

    # -------------------------------------------------------------------------
    # Rate Limiting & Concurrency
    # -------------------------------------------------------------------------
    max_concurrent_requests: int = Field(
        default=10,
        description="Maximum concurrent requests",
    )
    request_rate_limit: int = Field(
        default=100,
        description="Requests per minute limit",
    )

    # -------------------------------------------------------------------------
    # Feature Flags
    # -------------------------------------------------------------------------
    enable_caching: bool = Field(
        default=True,
        description="Enable response caching",
    )
    enable_sentiment_analysis: bool = Field(
        default=True,
        description="Enable sentiment analysis pipeline",
    )
    enable_news_fetching: bool = Field(
        default=True,
        description="Enable news fetching pipeline",
    )

    # -------------------------------------------------------------------------
    # Logging Configuration
    # -------------------------------------------------------------------------
    log_level: str = Field(
        default="INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR",
    )
    log_format: str = Field(
        default="json",
        description="Log format: json or text",
    )

    # -------------------------------------------------------------------------
    # Computed Properties
    # -------------------------------------------------------------------------
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.backend_reload

    @property
    def has_news_api(self) -> bool:
        """Check if news API is configured."""
        return bool(self.news_api_key)

    @property
    def has_openai(self) -> bool:
        """Check if OpenAI is configured."""
        return bool(self.openai_api_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()