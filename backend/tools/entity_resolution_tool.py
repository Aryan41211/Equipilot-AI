# EquiPilot AI - Entity Resolution Tool
# Tool for resolving natural-language financial entities to canonical tickers

from typing import Dict, Any
from backend.services.entity_resolution_service import (
    entity_resolution_service,
)
from backend.exceptions.entity_resolution_exceptions import (
    AmbiguousEntityError,
    EntityNotFoundError,
    EntityValidationError,
)
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class EntityResolutionTool:
    """Tool for resolving financial entities in natural language queries."""

    @staticmethod
    async def resolve_entity(text: str) -> Dict[str, Any]:
        """
        Resolve natural-language financial entity to canonical ticker.

        Args:
            text: Input text containing entity name or ticker.

        Returns:
            Dictionary with resolved entity or structured error.
        """
        logger.info("Resolving entity", text=text)

        try:
            result = await entity_resolution_service.resolve(text=text)
            return result.model_dump()
        except EntityNotFoundError as e:
            logger.warning("Entity not found", text=text, error=str(e))
            return {
                "ticker": None,
                "error": str(e),
                "error_type": "entity_not_found",
            }
        except AmbiguousEntityError as e:
            logger.warning("Ambiguous entity", text=text, error=str(e))
            return {
                "ticker": None,
                "error": str(e),
                "error_type": "ambiguous_entity",
            }
        except EntityValidationError as e:
            logger.warning("Entity validation error", text=text, error=str(e))
            return {
                "ticker": None,
                "error": str(e),
                "error_type": "validation_error",
            }
        except Exception as e:
            logger.error("Unexpected entity resolution error", text=text, error=str(e))
            return {
                "ticker": None,
                "error": f"Unexpected error: {str(e)}",
                "error_type": "unexpected_error",
            }


async def resolve_entity(text: str) -> Dict[str, Any]:
    """Resolve natural-language financial entity to canonical ticker."""
    return await EntityResolutionTool.resolve_entity(text)