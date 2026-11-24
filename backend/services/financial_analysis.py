"""EquiPilot AI — Financial Analysis Validation.

Implements financial calculation functions for equity research reports:
- Revenue growth, gross margin, operating margin, net margin
- EBITDA margin, EPS growth, ROE, ROCE
- Debt-to-equity, current ratio, free cash flow, operating cash flow
- Valuation multiples (P/E, P/B, P/S, EV/EBITDA)

All functions are pure calculations with comprehensive unit tests.
No external API calls. Works with synthetic data for validation.
"""

from __future__ import annotations

from typing import Any


def safe_divide(numerator: float | None, denominator: float | None) -> float | None:
    """Safely divide two numbers, returning None if denominator is zero or None."""
    if numerator is None or denominator is None:
        return None
    if denominator == 0:
        return None
    return numerator / denominator


def revenue_growth(current_revenue: float, previous_revenue: float) -> float | None:
    """Calculate revenue growth rate.

    Args:
        current_revenue: Revenue in current period
        previous_revenue: Revenue in previous period

    Returns:
        Growth rate as decimal (e.g., 0.15 = 15% growth), or None if invalid
    """
    if current_revenue is None or previous_revenue is None or previous_revenue == 0:
        return None
    return (current_revenue - previous_revenue) / previous_revenue


def gross_margin(gross_profit: float, revenue: float) -> float | None:
    """Calculate gross margin percentage.

    Args:
        gross_profit: Gross profit
        revenue: Total revenue

    Returns:
        Gross margin as decimal (e.g., 0.40 = 40%), or None if invalid
    """
    return safe_divide(gross_profit, revenue)


def operating_margin(operating_income: float, revenue: float) -> float | None:
    """Calculate operating margin percentage.

    Args:
        operating_income: Operating income (EBIT)
        revenue: Total revenue

    Returns:
        Operating margin as decimal, or None if invalid
    """
    return safe_divide(operating_income, revenue)


def net_margin(net_income: float, revenue: float) -> float | None:
    """Calculate net margin percentage.

    Args:
        net_income: Net income
        revenue: Total revenue

    Returns:
        Net margin as decimal, or None if invalid
    """
    return safe_divide(net_income, revenue)


def ebitda_margin(ebitda: float, revenue: float) -> float | None:
    """Calculate EBITDA margin percentage.

    Args:
        ebitda: EBITDA
        revenue: Total revenue

    Returns:
        EBITDA margin as decimal, or None if invalid
    """
    return safe_divide(ebitda, revenue)


def eps_growth(current_eps: float, previous_eps: float) -> float | None:
    """Calculate EPS growth rate.

    Args:
        current_eps: Current earnings per share
        previous_eps: Previous earnings per share

    Returns:
        Growth rate as decimal, or None if invalid
    """
    if previous_eps is None or previous_eps == 0:
        return None
    return (current_eps - previous_eps) / previous_eps


def roe(net_income: float, shareholders_equity: float) -> float | None:
    """Calculate Return on Equity (ROE).

    Args:
        net_income: Net income
        shareholders_equity: Shareholders' equity

    Returns:
        ROE as decimal, or None if invalid
    """
    return safe_divide(net_income, shareholders_equity)


def roce(ebit: float, capital_employed: float) -> float | None:
    """Calculate Return on Capital Employed (ROCE).

    Args:
        ebit: Earnings before interest and tax
        capital_employed: Total assets minus current liabilities

    Returns:
        ROCE as decimal, or None if invalid
    """
    return safe_divide(ebit, capital_employed)


def debt_to_equity(total_debt: float, shareholders_equity: float) -> float | None:
    """Calculate Debt-to-Equity ratio.

    Args:
        total_debt: Total debt
        shareholders_equity: Shareholders' equity

    Returns:
        D/E ratio, or None if invalid
    """
    return safe_divide(total_debt, shareholders_equity)


def current_ratio(current_assets: float, current_liabilities: float) -> float | None:
    """Calculate Current Ratio.

    Args:
        current_assets: Current assets
        current_liabilities: Current liabilities

    Returns:
        Current ratio, or None if invalid
    """
    return safe_divide(current_assets, current_liabilities)


def free_cash_flow(operating_cash_flow: float, capital_expenditures: float) -> float | None:
    """Calculate Free Cash Flow (FCF).

    Args:
        operating_cash_flow: Cash from operations
        capital_expenditures: Capital expenditures

    Returns:
        FCF value, or None if invalid
    """
    if operating_cash_flow is None or capital_expenditures is None:
        return None
    return operating_cash_flow - capital_expenditures


def pe_ratio(market_price_per_share: float, earnings_per_share: float) -> float | None:
    """Calculate Price-to-Earnings (P/E) ratio.

    Args:
        market_price_per_share: Current stock price
        earnings_per_share: Earnings per share

    Returns:
        P/E ratio, or None if invalid
    """
    return safe_divide(market_price_per_share, earnings_per_share)


def pb_ratio(market_price_per_share: float, book_value_per_share: float) -> float | None:
    """Calculate Price-to-Book (P/B) ratio.

    Args:
        market_price_per_share: Current stock price
        book_value_per_share: Book value per share

    Returns:
        P/B ratio, or None if invalid
    """
    return safe_divide(market_price_per_share, book_value_per_share)


def ps_ratio(market_cap: float, revenue: float) -> float | None:
    """Calculate Price-to-Sales (P/S) ratio.

    Args:
        market_cap: Market capitalization
        revenue: Total revenue

    Returns:
        P/S ratio, or None if invalid
    """
    return safe_divide(market_cap, revenue)


def ev_ebitda(enterprise_value: float, ebitda: float) -> float | None:
    """Calculate EV/EBITDA multiple.

    Args:
        enterprise_value: Enterprise value
        ebitda: EBITDA

    Returns:
        EV/EBITDA multiple, or None if invalid
    """
    return safe_divide(enterprise_value, ebitda)


def validate_financial_metrics(
    metrics: dict[str, float | None],
) -> dict[str, dict[str, Any]]:
    """Validate a set of financial metrics for consistency and plausibility.

    Checks:
    - Margins should be between -1 and 1 (i.e., -100% to +100%)
    - ROE and ROCE should be between -1 and 5 (reasonable range)
    - Debt-to-equity should be non-negative
    - Current ratio should be non-negative
    - P/E should be positive when both price and EPS are positive

    Args:
        metrics: Dictionary of metric name -> value

    Returns:
        Dictionary of metric name -> validation result
        {
            "metric_name": {
                "value": ...,
                "valid": bool,
                "warnings": [str],
            }
        }
    """
    results: dict[str, dict[str, Any]] = {}

    for name, value in metrics.items():
        result: dict[str, Any] = {"value": value, "valid": True, "warnings": []}

        if value is None:
            result["valid"] = False
            result["warnings"].append("Value is None")
            results[name] = result
            continue

        # Margin checks (should be between -100% and +100%)
        if name in (
            "gross_margin",
            "operating_margin",
            "net_margin",
            "ebitda_margin",
        ) and (value < -1 or value > 1):
            result["valid"] = False
            result["warnings"].append(f"Margin {value} outside [-1, 1] range")

        # ROE/ROCE checks
        if name in ("roe", "roce") and (value < -1 or value > 5):
            result["warnings"].append(f"{name} {value} outside typical [-1, 5] range")

        # Debt-to-equity
        if name == "debt_to_equity" and value < 0:
            result["valid"] = False
            result["warnings"].append("Negative debt-to-equity")

        # Current ratio
        if name == "current_ratio":
            if value < 0:
                result["valid"] = False
                result["warnings"].append("Negative current ratio")
            if value > 10:
                result["warnings"].append(f"Current ratio {value} unusually high")

        # P/E ratio
        if name == "pe_ratio":
            if value < 0:
                result["valid"] = False
                result["warnings"].append("Negative P/E ratio")
            if value > 1000:
                result["warnings"].append(f"P/E ratio {value} unusually high")

        results[name] = result

    return results


def compute_all_financials(
    *,
    revenue: float | None = None,
    previous_revenue: float | None = None,
    gross_profit: float | None = None,
    operating_income: float | None = None,
    net_income: float | None = None,
    ebitda: float | None = None,
    current_eps: float | None = None,
    previous_eps: float | None = None,
    shareholders_equity: float | None = None,
    ebit: float | None = None,
    capital_employed: float | None = None,
    total_debt: float | None = None,
    current_assets: float | None = None,
    current_liabilities: float | None = None,
    operating_cash_flow: float | None = None,
    capital_expenditures: float | None = None,
    market_price: float | None = None,
    book_value_per_share: float | None = None,
    market_cap: float | None = None,
    enterprise_value: float | None = None,
) -> dict[str, float | None]:
    """Compute all available financial metrics from provided data.

    Returns a dictionary of metric name -> computed value (or None if
    insufficient data).
    """
    return {
        "revenue_growth": (
            revenue_growth(revenue, previous_revenue)
            if revenue is not None and previous_revenue is not None
            else None
        ),
        "gross_margin": (
            gross_margin(gross_profit, revenue)
            if gross_profit is not None and revenue is not None
            else None
        ),
        "operating_margin": (
            operating_margin(operating_income, revenue)
            if operating_income is not None and revenue is not None
            else None
        ),
        "net_margin": (
            net_margin(net_income, revenue)
            if net_income is not None and revenue is not None
            else None
        ),
        "ebitda_margin": (
            ebitda_margin(ebitda, revenue) if ebitda is not None and revenue is not None else None
        ),
        "eps_growth": (
            eps_growth(current_eps, previous_eps)
            if current_eps is not None and previous_eps is not None
            else None
        ),
        "roe": (
            roe(net_income, shareholders_equity)
            if net_income is not None and shareholders_equity is not None
            else None
        ),
        "roce": (
            roce(ebit, capital_employed)
            if ebit is not None and capital_employed is not None
            else None
        ),
        "debt_to_equity": (
            debt_to_equity(total_debt, shareholders_equity)
            if total_debt is not None and shareholders_equity is not None
            else None
        ),
        "current_ratio": (
            current_ratio(current_assets, current_liabilities)
            if current_assets is not None and current_liabilities is not None
            else None
        ),
        "free_cash_flow": (
            free_cash_flow(operating_cash_flow, capital_expenditures)
            if operating_cash_flow is not None and capital_expenditures is not None
            else None
        ),
        "pe_ratio": (
            pe_ratio(market_price, current_eps)
            if market_price is not None and current_eps is not None
            else None
        ),
        "pb_ratio": (
            pb_ratio(market_price, book_value_per_share)
            if market_price is not None and book_value_per_share is not None
            else None
        ),
        "ps_ratio": (
            ps_ratio(market_cap, revenue)
            if market_cap is not None and revenue is not None
            else None
        ),
        "ev_ebitda": (
            ev_ebitda(enterprise_value, ebitda)
            if enterprise_value is not None and ebitda is not None
            else None
        ),
    }
