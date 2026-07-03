# EquiPilot AI - Application Constants
# Centralized enums and constants for consistent naming across the codebase

from enum import Enum

# ---------------------------------------------------------------------------
# Application Metadata
# ---------------------------------------------------------------------------
APP_NAME = "EquiPilot AI"
APP_VERSION = "0.1.0"


# ---------------------------------------------------------------------------
# Execution / Workflow Status
# ---------------------------------------------------------------------------
class ExecutionStatus(str, Enum):
    """Canonical workflow execution statuses."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SUCCESS = "success"
    FAILED = "failed"
    NOT_FOUND = "not_found"


# ---------------------------------------------------------------------------
# Application-level status (health checks, readiness)
# ---------------------------------------------------------------------------
class AppStatus(str, Enum):
    """Application-level health/status values."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    READY = "ready"
    NOT_READY = "not_ready"


# ---------------------------------------------------------------------------
# Research Intent categories (from router agent)
# ---------------------------------------------------------------------------
class ResearchIntent(str, Enum):
    """Intent categories for research queries."""

    COMPANY_ANALYSIS = "company_analysis"
    SECTOR_ANALYSIS = "sector_analysis"
    MARKET_OVERVIEW = "market_overview"
    EARNINGS_ANALYSIS = "earnings_analysis"
    NEWS_SENTIMENT = "news_sentiment"
    COMPARISON = "comparison"
    TECHNICAL_ANALYSIS = "technical_analysis"
    GENERAL_QUESTION = "general_question"
    FUNDAMENTALS = "fundamentals"
    NEWS = "news"
    SENTIMENT = "sentiment"
    FULL_RESEARCH = "full_research"


# ---------------------------------------------------------------------------
# Research workflow step identifiers
# ---------------------------------------------------------------------------
class ResearchStep(str, Enum):
    """Pipeline step names used in progress tracking and metadata."""

    INITIALIZED = "initialized"
    ROUTER = "router"
    ENTITY_RESOLUTION = "entity_resolution_tool"
    MARKET_DATA = "market_data_tool"
    NEWS = "news_tool"
    SENTIMENT = "sentiment_tool"
    MERGE_RESULTS = "merge_results"
    RESEARCH = "research"
    COMPLETED = "completed"


# ---------------------------------------------------------------------------
# HTTP error type labels (domain exceptions)
# ---------------------------------------------------------------------------
class ErrorType(str, Enum):
    """Machine-readable error type identifiers."""

    INTERNAL_ERROR = "internal_error"
    HTTP_ERROR = "http_error"
    VALIDATION_ERROR = "validation_error"
    ENTITY_NOT_FOUND = "entity_not_found"
    AMBIGUOUS_ENTITY = "ambiguous_entity"
    ENTITY_VALIDATION = "entity_validation_error"
    SENTIMENT_TIMEOUT = "sentiment_timeout"
    SENTIMENT_PROVIDER = "sentiment_provider_error"
    SENTIMENT_MALFORMED = "sentiment_malformed"
    SENTIMENT_VALIDATION = "sentiment_validation_error"
    SYNTHESIS_TIMEOUT = "synthesis_timeout"
    SYNTHESIS_PROVIDER = "synthesis_provider_error"
    SYNTHESIS_VALIDATION = "synthesis_validation_error"
    INVALID_TICKER = "invalid_ticker"
    DATA_UNAVAILABLE = "data_unavailable"
    RATE_LIMIT = "rate_limit"
    NETWORK_ERROR = "network_error"
    SERVICE_ERROR = "service_error"
    UNEXPECTED_ERROR = "unexpected_error"


# ---------------------------------------------------------------------------
# HTTP Status Codes (domain-specific)
# ---------------------------------------------------------------------------
HTTP_ENTITY_NOT_FOUND = 404
HTTP_AMBIGUOUS_ENTITY = 409
HTTP_SENTIMENT_TIMEOUT = 504
HTTP_SYNTHESIS_TIMEOUT = 504
HTTP_VALIDATION_ERROR = 422
HTTP_RATE_LIMITED = 429


# ---------------------------------------------------------------------------
# Logging Constants
# ---------------------------------------------------------------------------
VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
VALID_LOG_FORMATS = {"json", "text"}
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "json"


# ---------------------------------------------------------------------------
# Data Source Identifiers
# ---------------------------------------------------------------------------
class DataSource(str, Enum):
    """Canonical data source identifiers."""

    YFINANCE = "yfinance"
    NEWSAPI = "newsapi"
    ALPHA_VANTAGE = "alphavantage"
    FINNHUB = "finnhub"
    OPENAI = "openai"
    LLM = "llm"
    UNKNOWN = "unknown"
    ERROR = "error"


# ---------------------------------------------------------------------------
# Cache Defaults
# ---------------------------------------------------------------------------
DEFAULT_CACHE_TTL = 300  # seconds
DEFAULT_REQUEST_TIMEOUT = 30  # seconds
DEFAULT_MAX_ARTICLES = 20
DEFAULT_NEWS_LOOKBACK_DAYS = 7