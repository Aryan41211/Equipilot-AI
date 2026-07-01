from __future__ import annotations


class SentimentError(Exception):
    """Base class for Sentiment analysis related errors."""


class SentimentTimeoutError(SentimentError):
    """Raised when the sentiment provider times out."""


class SentimentProviderError(SentimentError):
    """Raised when the sentiment provider (LLM) returns an operational failure."""


class SentimentMalformedResponseError(SentimentError):
    """Raised when the LLM returns a malformed response (non-JSON / missing keys)."""


class SentimentValidationError(SentimentError):
    """Raised when parsed sentiment output fails schema validation."""


def sentiment_error_details(
    *,
    message: str,
    provider: str | None = None,
) -> str:
    """Helper to create consistent error messages."""
    if provider:
        return f"{message} (provider={provider})"
    return message
