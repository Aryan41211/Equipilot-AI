# EquiPilot AI - Backend Configuration
# Centralized configuration management using Pydantic Settings

import os
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.core.constants import (
    APP_NAME,
    APP_VERSION,
    VALID_LOG_FORMATS,
    VALID_LOG_LEVELS,
)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # Application Metadata
    # -------------------------------------------------------------------------
    app_name: str = Field(
        default=APP_NAME,
        description="Application name",
    )
    app_version: str = Field(
        default=APP_VERSION,
        description="Application version",
    )
    environment: str = Field(
        default="development",
        description="Deployment environment: development, staging, production",
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
        default_factory=lambda: int(os.environ.get("PORT", "8000")),
        description="Backend server port (from PORT env var in production)",
    )
    backend_reload: bool = Field(
        default=True,
        description="Enable auto-reload in development",
    )
    backend_workers: int = Field(
        default=2,
        description="Number of uvicorn worker processes",
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
    cors_origins: list[str] = Field(
        default=["*"],
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
    # Security Configuration
    # -------------------------------------------------------------------------
    secret_key: str = Field(
        default="",
        description="Secret key for session signing and encryption",
    )
    allowed_hosts: list[str] = Field(
        default=["*"],
        description="Allowed hostnames for the application",
    )

    # -------------------------------------------------------------------------
    # Computed Properties
    # -------------------------------------------------------------------------
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development" or self.backend_reload

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"

    @property
    def is_staging(self) -> bool:
        """Check if running in staging mode."""
        return self.environment == "staging"

    @property
    def has_news_api(self) -> bool:
        """Check if news API is configured."""
        return bool(self.news_api_key)

    @property
    def has_openai(self) -> bool:
        """Check if OpenAI is configured."""
        return bool(self.openai_api_key)

    # -------------------------------------------------------------------------
    # Field Validators
    # -------------------------------------------------------------------------
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        if v.upper() not in VALID_LOG_LEVELS:
            raise ValueError(f"log_level must be one of {VALID_LOG_LEVELS}")
        return v.upper()

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Validate log format."""
        if v.lower() not in VALID_LOG_FORMATS:
            raise ValueError(f"log_format must be one of {VALID_LOG_FORMATS}")
        return v.lower()

    @field_validator("news_api_provider")
    @classmethod
    def validate_news_provider(cls, v: str) -> str:
        """Validate news API provider."""
        valid_providers = {"newsapi", "alphavantage", "finnhub"}
        if v.lower() not in valid_providers:
            raise ValueError(f"news_api_provider must be one of {valid_providers}")
        return v.lower()

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate deployment environment."""
        valid_environments = {"development", "staging", "production"}
        if v.lower() not in valid_environments:
            raise ValueError(f"environment must be one of {valid_environments}")
        return v.lower()

    @field_validator("backend_workers")
    @classmethod
    def validate_workers(cls, v: int) -> int:
        """Validate worker count."""
        if v < 1:
            raise ValueError("backend_workers must be at least 1")
        if v > 8:
            raise ValueError("backend_workers must not exceed 8")
        return v

    # -------------------------------------------------------------------------
    # Validation Methods
    # -------------------------------------------------------------------------
    def validate_required_settings(self) -> list[str]:
        """Validate required settings for production. Returns list of missing config warnings."""
        warnings = []

        if not self.has_openai:
            warnings.append("OPENAI_API_KEY not set - LLM features will not work")

        if not self.has_news_api:
            warnings.append("NEWS_API_KEY not set - news features will use fallback sources")

        if self.is_production and not self.secret_key:
            warnings.append("SECRET_KEY not set - session security may be compromised")

        if self.is_production and self.backend_reload:
            warnings.append("BACKEND_RELOAD is enabled in production - disable for performance")

        return warnings

    def validate_environment_variables(self) -> list[str]:
        """Validate that all required environment variables are set for the current environment.

        Returns:
            List of missing or invalid environment variable descriptions
        """
        errors = []

        # Production requires all critical keys
        if self.is_production:
            if not self.openai_api_key:
                errors.append("OPENAI_API_KEY is required in production")
            if not self.secret_key:
                errors.append("SECRET_KEY is required in production")
            if self.backend_reload:
                errors.append("BACKEND_RELOAD must be false in production")

        return errors


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()