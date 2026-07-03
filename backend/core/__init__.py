# EquiPilot AI - Core Package
# Centralized configuration, logging, constants, and base classes

from backend.core.constants import (
    AppStatus,
    DataSource,
    ErrorType,
    ExecutionStatus,
    ResearchIntent,
    ResearchStep,
    APP_NAME,
    APP_VERSION,
    DEFAULT_CACHE_TTL,
    DEFAULT_MAX_ARTICLES,
    DEFAULT_NEWS_LOOKBACK_DAYS,
    DEFAULT_REQUEST_TIMEOUT,
    HTTP_AMBIGUOUS_ENTITY,
    HTTP_ENTITY_NOT_FOUND,
    HTTP_RATE_LIMITED,
    HTTP_SENTIMENT_TIMEOUT,
    HTTP_SYNTHESIS_TIMEOUT,
    HTTP_VALIDATION_ERROR,
    VALID_LOG_FORMATS,
    VALID_LOG_LEVELS,
)

from backend.core.exceptions import (
    ConfigurationError,
    EquiPilotError,
    ProviderError,
    ServiceError,
    ToolError,
    ValidationError,
    format_error_detail,
)

__all__ = [
    # Constants
    "AppStatus",
    "DataSource",
    "ErrorType",
    "ExecutionStatus",
    "ResearchIntent",
    "ResearchStep",
    "APP_NAME",
    "APP_VERSION",
    "DEFAULT_CACHE_TTL",
    "DEFAULT_MAX_ARTICLES",
    "DEFAULT_NEWS_LOOKBACK_DAYS",
    "DEFAULT_REQUEST_TIMEOUT",
    "HTTP_AMBIGUOUS_ENTITY",
    "HTTP_ENTITY_NOT_FOUND",
    "HTTP_RATE_LIMITED",
    "HTTP_SENTIMENT_TIMEOUT",
    "HTTP_SYNTHESIS_TIMEOUT",
    "HTTP_VALIDATION_ERROR",
    "VALID_LOG_FORMATS",
    "VALID_LOG_LEVELS",
    # Exceptions
    "ConfigurationError",
    "EquiPilotError",
    "ProviderError",
    "ServiceError",
    "ToolError",
    "ValidationError",
    "format_error_detail",
]