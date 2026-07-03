# EquiPilot AI - Base Exception Hierarchy
# Centralized base exception classes for all domain exceptions

from __future__ import annotations


class EquiPilotError(Exception):
    """Base exception for all EquiPilot AI errors."""


class ConfigurationError(EquiPilotError):
    """Raised when application configuration is invalid."""


class ServiceError(EquiPilotError):
    """Base class for service-level errors."""


class ToolError(EquiPilotError):
    """Base class for tool-level errors."""


class ProviderError(EquiPilotError):
    """Base class for external provider errors."""


class ValidationError(EquiPilotError):
    """Base class for validation errors."""


def format_error_detail(*, message: str, entity: str | None = None, provider: str | None = None) -> str:
    """Create consistent error detail strings.

    Args:
        message: The error message.
        entity: Optional entity name for context.
        provider: Optional provider name for context.

    Returns:
        Formatted error detail string.
    """
    parts = [message]
    if entity:
        parts.append(f"(entity={entity})")
    if provider:
        parts.append(f"(provider={provider})")
    return " ".join(parts)