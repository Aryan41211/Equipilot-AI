from __future__ import annotations


class EntityResolutionError(Exception):
    """Base class for Entity Resolution related errors."""


class EntityNotFoundError(EntityResolutionError):
    """Raised when no matching entity is found for the input."""


class AmbiguousEntityError(EntityResolutionError):
    """Raised when multiple entities match the input ambiguously."""


class EntityValidationError(EntityResolutionError):
    """Raised when entity resolution input validation fails."""


def entity_error_details(
    *,
    message: str,
    entity: str | None = None,
) -> str:
    """Helper to create consistent error messages."""
    if entity:
        return f"{message} (entity={entity})"
    return message
