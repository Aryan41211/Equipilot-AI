# EquiPilot AI - yfinance Tool Tests
# Verifies the include_fundamentals / include_technicals flags are honored.
#
# Note: the @tool-decorated functions are invoked through `.coroutine` (the raw
# async function) because the tool's first parameter is literally named `self`,
# which collides with StructuredTool._arun's own `self` when routed through
# ainvoke(). Calling the coroutine directly matches the style already used in
# tests/test_market_data_tool.py.

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from backend.schemas.market_data import FundamentalsData, MarketData, TechnicalIndicators
from backend.tools.yfinance_tool import get_market_data


def _md() -> MarketData:
    return MarketData(
        ticker="AAPL",
        company_name="Apple Inc.",
        current_price=180.5,
        change_percent=1.2,
        fundamentals=FundamentalsData(pe_ratio=25.0, market_cap=2_800_000_000_000),
        technicals=TechnicalIndicators(rsi_14=55.0, sma_20=175.0),
        data_as_of=datetime(2024, 1, 15),
    )


async def _call(**overrides):
    kwargs = {"self": ["AAPL"], "period": "1y"}
    kwargs.update(overrides)
    with patch(
        "backend.tools.yfinance_tool.market_service.get_market_data",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.return_value = {"AAPL": _md()}
        result = await get_market_data.coroutine(**kwargs)
    return result


class TestIncludeFlags:
    """The include_* flags must gate the serialized sections."""

    @pytest.mark.asyncio
    async def test_defaults_include_fundamentals_exclude_technicals(self):
        result = await _call()
        entry = result["AAPL"]
        assert entry["fundamentals"]["pe_ratio"] == 25.0
        assert entry["technicals"] is None

    @pytest.mark.asyncio
    async def test_include_technicals_true_returns_technicals(self):
        result = await _call(include_technicals=True)
        assert result["AAPL"]["technicals"]["rsi_14"] == 55.0

    @pytest.mark.asyncio
    async def test_include_fundamentals_false_nulls_fundamentals(self):
        result = await _call(include_fundamentals=False)
        assert result["AAPL"]["fundamentals"] is None
        # Non-gated price fields survive.
        assert result["AAPL"]["current_price"] == 180.5

    @pytest.mark.asyncio
    async def test_both_flags_true_returns_both(self):
        result = await _call(include_fundamentals=True, include_technicals=True)
        entry = result["AAPL"]
        assert entry["fundamentals"]["pe_ratio"] == 25.0
        assert entry["technicals"]["sma_20"] == 175.0

    @pytest.mark.asyncio
    async def test_flags_do_not_mutate_source_objects(self):
        """The MarketData objects may be shared via the service cache."""
        source = _md()

        with patch(
            "backend.tools.yfinance_tool.market_service.get_market_data",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_get.return_value = {"AAPL": source}
            await get_market_data.coroutine(
                **{"self": ["AAPL"], "period": "1y", "include_fundamentals": False}
            )

        assert source.fundamentals is not None
        assert source.technicals is not None
