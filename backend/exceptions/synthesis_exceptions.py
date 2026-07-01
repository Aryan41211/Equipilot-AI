from __future__ import annotations


class SynthesisError(Exception):
    """Base class for synthesis related errors."""


class SynthesisTimeoutError(SynthesisError):
    """Raised when the LLM provider times out during synthesis."""


class SynthesisProviderError(SynthesisError):
    """Raised when the LLM provider returns an operational failure."""


class SynthesisMalformedResponseError(SynthesisError):
    """Raised when the LLM returns a malformed response (non-JSON / missing keys)."""


class SynthesisValidationError(SynthesisError):
    """Raised when parsed synthesis output fails schema validation."""


def synthesis_error_details(
    *,
    message: str,
    provider: str | None = None,
) -> str:
    """Helper to create consistent error messages."""
    if provider:
        return f"{message} (provider={provider})"
    return message
