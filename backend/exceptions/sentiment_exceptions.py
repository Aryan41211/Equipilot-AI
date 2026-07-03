from __future__ import annotations

from backend.core.exceptions import EquiPilotError, format_error_detail


class SentimentError(EquiPilotError):
    """Base class for Sentiment analysis related errors."""


class SentimentTimeoutError(SentimentError):
    """Raised when the sentiment provider times out."""


class SentimentProviderError(SentimentError):
    """Raised when the sentiment provider (LLM) returns an operational failure."""


class SentimentMalformedResponseError(SentimentError):
    """Raised when the LLM returns a malformed response (non-JSON / missing keys)."""


class SentimentValidationError(SentimentError):
    """Raised when parsed sentiment output fails schema validation."""


# Backward-compatible alias
sentiment_error_details = format_error_detail