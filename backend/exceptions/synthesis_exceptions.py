from __future__ import annotations

from backend.core.exceptions import EquiPilotError, format_error_detail


class SynthesisError(EquiPilotError):
    """Base class for synthesis related errors."""


class SynthesisTimeoutError(SynthesisError):
    """Raised when the LLM provider times out during synthesis."""


class SynthesisProviderError(SynthesisError):
    """Raised when the LLM provider returns an operational failure."""


class SynthesisMalformedResponseError(SynthesisError):
    """Raised when the LLM returns a malformed response (non-JSON / missing keys)."""


class SynthesisValidationError(SynthesisError):
    """Raised when parsed synthesis output fails schema validation."""


# Backward-compatible alias
synthesis_error_details = format_error_detail