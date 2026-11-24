# EquiPilot AI — Financial Validation

**Project:** EquiPilot AI  
**Date:** 2026-11-24  
**Git SHA:** `0fccaca`

---

## Implemented Financial Calculations

### Revenue & Growth

| Function | Formula | Use Case |
|----------|---------|----------|
| revenue_growth | (current - previous) / previous | YoY/QoQ revenue change |
| eps_growth | (current - previous) / previous | EPS trend analysis |

### Profitability Margins

| Function | Formula | Use Case |
|----------|---------|----------|
| gross_margin | gross_profit / revenue | Production efficiency |
| operating_margin | operating_income / revenue | Operational efficiency |
| net_margin | net_income / revenue | Bottom-line profitability |
| ebitda_margin | ebitda / revenue | Operating cash flow proxy |

### Return Metrics

| Function | Formula | Use Case |
|----------|---------|----------|
| roe | net_income / shareholders_equity | Shareholder return |
| roce | ebit / capital_employed | Capital efficiency |

### Balance Sheet & Liquidity

| Function | Formula | Use Case |
|----------|---------|----------|
| debt_to_equity | total_debt / shareholders_equity | Leverage |
| current_ratio | current_assets / current_liabilities | Short-term liquidity |
| free_cash_flow | operating_cash_flow - capex | Cash available to investors |

### Valuation Multiples

| Function | Formula | Use Case |
|----------|---------|----------|
| pe_ratio | price / eps | Relative valuation |
| pb_ratio | price / book_value | Asset-based valuation |
| ps_ratio | market_cap / revenue | Revenue-based valuation |
| ev_ebitda | enterprise_value / ebitda | Acquisition valuation |

---

## Validation Rules

| Metric | Valid Range | Warning Range |
|--------|------------|---------------|
| gross_margin | [-1, 1] | — |
| operating_margin | [-1, 1] | — |
| net_margin | [-1, 1] | — |
| ebitda_margin | [-1, 1] | — |
| roe | [-1, 5] | Outside [-1, 5] |
| roce | [-1, 5] | Outside [-1, 5] |
| debt_to_equity | ≥ 0 | — |
| current_ratio | ≥ 0 | > 10 (unusually high) |
| pe_ratio | ≥ 0 | > 1000 (unusually high) |

---

## Test Results: 39/39 Pass

All unit tests pass, covering:
- Normal calculation paths
- Edge cases (zero denominators, None values)
- Partial data (compute_all_financials with subset of inputs)
- Validation rules (invalid margins, negative ratios, None values)

---

## No Investment Claims

The following are **NOT** claimed or measured:
- Investment returns or alpha
- Buy/sell recommendations
- Trading signals
- Financial backtesting
- Prediction accuracy

This is an informational equity research assistant only.
