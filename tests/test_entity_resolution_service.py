from __future__ import annotations

import pytest
from backend.services.entity_resolution_service import (
    EntityResolutionService,
    entity_error_details,
    entity_resolution_service,
)
from backend.exceptions.entity_resolution_exceptions import (
    AmbiguousEntityError,
    EntityNotFoundError,
    EntityValidationError,
)
from backend.schemas.entity_resolution import EntityType


class TestEntityResolutionServiceExactMatch:
    def test_exact_ticker_match_nse(self):
        service = EntityResolutionService()
        result = asyncio_run(service.resolve("TCS.NS"))
        assert result.ticker == "TCS.NS"
        assert result.exchange == "NSE"
        assert result.entity_type == EntityType.NSE_TICKER

    def test_exact_company_name_match(self):
        service = EntityResolutionService()
        result = asyncio_run(service.resolve("Apple Inc."))
        assert result.ticker == "AAPL"
        assert result.exchange == "NASDAQ"
        assert result.resolved_entity == "Apple Inc."


class TestEntityResolutionServiceAliasMatch:
    def test_alias_match_lower_case(self):
        service = EntityResolutionService()
        result = asyncio_run(service.resolve("tell me about apple"))
        assert result.ticker == "AAPL"
        assert result.exchange == "NASDAQ"

    def test_alias_match_nse(self):
        service = EntityResolutionService()
        result = asyncio_run(service.resolve("tcs stock"))
        assert result.ticker == "TCS.NS"

    def test_alias_among_other_text(self):
        service = EntityResolutionService()
        result = asyncio_run(service.resolve("What is the PE ratio of Infosys?"))
        assert result.ticker == "INFY.NS"


class TestEntityResolutionServiceCaseInsensitive:
    def test_upper_case_input(self):
        service = EntityResolutionService()
        result = asyncio_run(service.resolve("RELIANCE.NS"))
        assert result.ticker == "RELIANCE.NS"

    def test_lower_case_input(self):
        service = EntityResolutionService()
        result = asyncio_run(service.resolve("reliance.ns"))
        assert result.ticker == "RELIANCE.NS"

    def test_mixed_case_input(self):
        service = EntityResolutionService()
        result = asyncio_run(service.resolve("NvidiA"))
        assert result.ticker == "NVDA"


class TestEntityResolutionServiceAmbiguous:
    def test_ambiguous_entity_raises_error(self):
        service = EntityResolutionService()
        with pytest.raises(AmbiguousEntityError):
            asyncio_run(service.resolve("apple tesla"))

    def test_ambiguous_multiple_tickers(self):
        service = EntityResolutionService()
        service.add_entity("APPL.NS", "Apple India", exchange="NSE", aliases=["india apple"])
        service.add_entity("APPLE.NS", "Apple Global", exchange="NSE", aliases=["global apple"])
        with pytest.raises(AmbiguousEntityError):
            asyncio_run(service.resolve("india apple global apple"))


class TestEntityResolutionServiceUnknown:
    def test_unknown_entity_raises_error(self):
        service = EntityResolutionService()
        with pytest.raises(EntityNotFoundError):
            asyncio_run(service.resolve("Unknown Company XYZ"))


class TestEntityResolutionServiceValidation:
    def test_empty_input_raises_validation_error(self):
        service = EntityResolutionService()
        with pytest.raises(EntityValidationError):
            asyncio_run(service.resolve(""))

    def test_whitespace_input_raises_validation_error(self):
        service = EntityResolutionService()
        with pytest.raises(EntityValidationError):
            asyncio_run(service.resolve("   "))


class TestEntityResolutionServiceExtensions:
    def test_add_entity_nse(self):
        service = EntityResolutionService()
        service.add_entity("WIPRO.NS", "Wipro Limited", exchange="NSE", aliases=["wipro"])
        result = asyncio_run(service.resolve("wipro"))
        assert result.ticker == "WIPRO.NS"
        assert result.entity_type == EntityType.PUBLIC_COMPANY

    def test_add_entity_nasdaq(self):
        service = EntityResolutionService()
        service.add_entity("META", "Meta Platforms", exchange="NASDAQ", aliases=["meta", "facebook"])
        result = asyncio_run(service.resolve("facebook"))
        assert result.ticker == "META"

    def test_extended_entity_resolved_in_registry(self):
        service = EntityResolutionService()
        service.add_entity("TEST.NS", "Test Company", exchange="NSE")
        result = asyncio_run(service.resolve("TEST.NS"))
        assert result.ticker == "TEST.NS"


def asyncio_run(coro):
    """Helper to run async code in sync tests."""
    import asyncio
    return asyncio.get_event_loop().run_until_complete(coro)