# EquiPilot AI - Exceptions Package
# Centralized exception hierarchy for the application

from backend.exceptions.entity_resolution_exceptions import (
    AmbiguousEntityError,
    EntityNotFoundError,
    EntityResolutionError,
    EntityValidationError,
    entity_error_details,
)
from backend.exceptions.sentiment_exceptions import (
    SentimentError,
    SentimentMalformedResponseError,
    SentimentProviderError,
    SentimentTimeoutError,
    SentimentValidationError,
    sentiment_error_details,
)
from backend.exceptions.synthesis_exceptions import (
    SynthesisError,
    SynthesisTimeoutError,
    SynthesisValidationError,
)

__all__ = [
    # Entity resolution
    "EntityResolutionError",
    "EntityNotFoundError",
    "AmbiguousEntityError",
    "EntityValidationError",
    "entity_error_details",
    # Sentiment
    "SentimentError",
    "SentimentTimeoutError",
    "SentimentProviderError",
    "SentimentMalformedResponseError",
    "SentimentValidationError",
    "sentiment_error_details",
    # Synthesis
    "SynthesisError",
    "SynthesisTimeoutError",
    "SynthesisValidationError",
]
