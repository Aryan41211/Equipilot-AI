from __future__ import annotations

from typing import Dict, List, Optional, Tuple
from backend.exceptions.entity_resolution_exceptions import (
    AmbiguousEntityError,
    EntityNotFoundError,
    EntityValidationError,
)
from backend.schemas.entity_resolution import (
    EntityResolution,
    EntityResolutionResponse,
    EntityType,
)
from backend.utils.logger import get_logger

logger = get_logger(__name__)


_ENTITY_REGISTRY: Dict[str, Dict] = {
    "RELIANCE.NS": {
        "name": "Reliance Industries",
        "exchange": "NSE",
        "aliases": ["reliance", "reliance industries", "ril", "rili"],
        "type": EntityType.NSE_TICKER,
    },
    "TCS.NS": {
        "name": "Tata Consultancy Services",
        "exchange": "NSE",
        "aliases": ["tcs", "tata consultancy services", "tata", "tcsg"],
        "type": EntityType.NSE_TICKER,
    },
    "INFY.NS": {
        "name": "Infosys",
        "exchange": "NSE",
        "aliases": ["infosys", "infy", "infy.ns"],
        "type": EntityType.NSE_TICKER,
    },
    "AAPL": {
        "name": "Apple Inc.",
        "exchange": "NASDAQ",
        "aliases": ["apple", "apple inc", "aapl", "apple.com"],
        "type": EntityType.NASDAQ_TICKER,
    },
    "MSFT": {
        "name": "Microsoft Corporation",
        "exchange": "NASDAQ",
        "aliases": ["microsoft", "microsoft corp", "msft", "msft.com"],
        "type": EntityType.NASDAQ_TICKER,
    },
    "GOOGL": {
        "name": "Alphabet Inc.",
        "exchange": "NASDAQ",
        "aliases": ["alphabet", "alphabet inc", "google", "googl"],
        "type": EntityType.NASDAQ_TICKER,
    },
    "NVDA": {
        "name": "NVIDIA Corporation",
        "exchange": "NASDAQ",
        "aliases": ["nvidia", "nvidia corp", "nvda", "nvidia.com"],
        "type": EntityType.NASDAQ_TICKER,
    },
    "TSLA": {
        "name": "Tesla Inc.",
        "exchange": "NASDAQ",
        "aliases": ["tesla", "tesla motors", "tsla", "tesla.com"],
        "type": EntityType.NASDAQ_TICKER,
    },
    "AMZN": {
        "name": "Amazon.com Inc.",
        "exchange": "NASDAQ",
        "aliases": ["amazon", "amazon.com", "amzn", "amazon inc"],
        "type": EntityType.NASDAQ_TICKER,
    },
}

_ALIAS_INDEX: Dict[str, str] = {}
for ticker, data in _ENTITY_REGISTRY.items():
    for alias in data["aliases"]:
        _ALIAS_INDEX[alias.lower()] = ticker


class EntityResolutionService:
    """Production-ready service for resolving financial entities to canonical tickers."""

    def __init__(self) -> None:
        self._registry = dict(_ENTITY_REGISTRY)
        self._alias_index = dict(_ALIAS_INDEX)

    async def resolve(
        self,
        text: str,
        ticker: Optional[str] = None,
    ) -> EntityResolutionResponse:
        """
        Resolve natural-language financial entity to canonical ticker.

        Args:
            text: Input text containing entity name or ticker.
            ticker: Optional pre-extracted ticker (used as hint).

        Returns:
            EntityResolutionResponse with resolved entity or error.

        Raises:
            EntityValidationError: If input text is empty or invalid.
        """
        if not text or not text.strip():
            raise EntityValidationError(entity_error_details(message="Input text is empty"))

        text_upper = text.upper().strip()
        text_lower = text.lower().strip()

        for reg_ticker, reg_data in self._registry.items():
            if reg_ticker.upper() == text_upper:
                return self._build_response(reg_ticker, reg_data, text)

            if reg_data["name"].upper() == text_upper:
                return self._build_response(reg_ticker, reg_data, text)

        matches: List[Tuple[str, Dict]] = []
        for reg_ticker, reg_data in self._registry.items():
            if reg_ticker.upper() in text_upper:
                matches.append((reg_ticker, reg_data))
            elif reg_data["name"].upper() in text_upper:
                matches.append((reg_ticker, reg_data))

        for alias, reg_ticker in self._alias_index.items():
            if alias in text_lower:
                matches.append((reg_ticker, self._registry[reg_ticker]))

        unique_matches = list({m[0]: m for m in matches}.values())

        if len(unique_matches) == 0:
            raise EntityNotFoundError(
                entity_error_details(message="Entity not found", entity=text)
            )

        if len(unique_matches) > 1:
            raise AmbiguousEntityError(
                entity_error_details(
                    message=f"Multiple entities match: {', '.join(m[0] for m in unique_matches)}",
                    entity=text,
                )
            )

        reg_ticker, reg_data = unique_matches[0]
        return self._build_response(reg_ticker, reg_data, text)

    def _build_response(
        self,
        ticker: str,
        data: Dict,
        original_text: str,
    ) -> EntityResolutionResponse:
        """Build structured resolution response."""
        return EntityResolutionResponse(
            input_text=original_text,
            ticker=ticker,
            exchange=data.get("exchange"),
            confidence=1.0,
            entity_type=data.get("type"),
            resolved_entity=data.get("name"),
            aliases=data.get("aliases", []),
        )

    def add_entity(
        self,
        ticker: str,
        name: str,
        exchange: Optional[str] = None,
        aliases: Optional[List[str]] = None,
        entity_type: EntityType = EntityType.PUBLIC_COMPANY,
    ) -> None:
        """
        Register a new entity in the resolution registry.

        This allows extending supported entities without modifying the service.
        """
        self._registry[ticker] = {
            "name": name,
            "exchange": exchange,
            "aliases": aliases or [],
            "type": entity_type,
        }
        for alias in (aliases or []):
            self._alias_index[alias.lower()] = ticker


def entity_error_details(
    *,
    message: str,
    entity: Optional[str] = None,
) -> str:
    """Helper to create consistent error messages."""
    if entity:
        return f"{message} (entity={entity})"
    return message


entity_resolution_service = EntityResolutionService()