from __future__ import annotations

import pytest

from backend.tools.entity_resolution_tool import EntityResolutionTool, resolve_entity


@pytest.mark.asyncio
async def test_exact_match_returns_ticker():
    result = await resolve_entity("TCS.NS")
    assert result["ticker"] == "TCS.NS"
    assert result["exchange"] == "NSE"
    assert result["error"] is None
    assert result["error_type"] is None


@pytest.mark.asyncio
async def test_alias_match_returns_canonical():
    result = await resolve_entity("what is the valuation of Apple Inc")
    assert result["ticker"] == "AAPL"
    assert result["exchange"] == "NASDAQ"
    assert result["resolved_entity"] == "Apple Inc."


@pytest.mark.asyncio
async def test_company_name_match():
    result = await resolve_entity("Tata Consultancy Services")
    assert result["ticker"] == "TCS.NS"
    assert result["resolved_entity"] == "Tata Consultancy Services"


@pytest.mark.asyncio
async def test_unknown_entity_returns_structured_error():
    result = await resolve_entity("Nonexistent Corp")
    assert result["ticker"] is None
    assert result["error"] is not None
    assert result["error_type"] == "entity_not_found"
    assert "Nonexistent Corp" in result["error"]


@pytest.mark.asyncio
async def test_empty_input_returns_validation_error():
    result = await resolve_entity("")
    assert result["ticker"] is None
    assert result["error_type"] == "validation_error"


@pytest.mark.asyncio
async def test_whitespace_input_returns_validation_error():
    result = await resolve_entity("   ")
    assert result["ticker"] is None
    assert result["error_type"] == "validation_error"


@pytest.mark.asyncio
async def test_confidence_score_present():
    result = await resolve_entity("NVDA")
    assert "confidence" in result
    assert result["confidence"] == 1.0


@pytest.mark.asyncio
async def test_aliases_returned():
    result = await resolve_entity("Tesla")
    assert result["aliases"] == ["tesla", "tesla motors", "tsla", "tesla.com"]


@pytest.mark.asyncio
async def test_tool_successful_response_contract():
    result = await EntityResolutionTool.resolve_entity("AAPL")
    assert "ticker" in result
    assert "exchange" in result
    assert "confidence" in result


@pytest.mark.asyncio
async def test_multiple_entities_raises_ambiguous():
    result = await resolve_entity("apple tesla")
    assert result["ticker"] is None
    assert result["error_type"] == "ambiguous_entity"
