from __future__ import annotations

from backend.core.exceptions import EquiPilotError, format_error_detail


class EntityResolutionError(EquiPilotError):
    """Base class for Entity Resolution related errors."""


class EntityNotFoundError(EntityResolutionError):
    """Raised when no matching entity is found for the input."""


class AmbiguousEntityError(EntityResolutionError):
    """Raised when multiple entities match the input ambiguously."""


class EntityValidationError(EntityResolutionError):
    """Raised when entity resolution input validation fails."""


# Backward-compatible alias
entity_error_details = format_error_detail