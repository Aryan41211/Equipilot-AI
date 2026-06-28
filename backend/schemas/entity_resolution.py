# EquiPilot AI - Entity Resolution Schemas
# Pydantic models for entity resolution structures

from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class EntityType(str, Enum):
    """Supported entity types for resolution."""

    PUBLIC_COMPANY = "public_company"
    NSE_TICKER = "nse_ticker"
    NASDAQ_TICKER = "nasdaq_ticker"


class EntityResolution(BaseModel):
    """Resolved entity with canonical identifier."""

    input_text: str
    resolved_entity: str
    ticker: str
    exchange: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    entity_type: EntityType
    aliases: List[str] = Field(default_factory=list)


class EntityResolutionResponse(BaseModel):
    """Structured response for entity resolution requests."""

    input_text: str
    ticker: Optional[str] = None
    exchange: Optional[str] = None
    confidence: float = 0.0
    entity_type: Optional[EntityType] = None
    resolved_entity: Optional[str] = None
    aliases: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    error_type: Optional[str] = None