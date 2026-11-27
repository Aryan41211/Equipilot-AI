# PHASE 4 — EquiPilot AI Data Provenance

**Project:** EquiPilot AI — Agentic Equity Research System
**Phase:** 4 — Benchmark Breakthrough
**Date:** 2026-11-25
**Git SHA:** 5087a7a

---

## 1. Data Sources

| Source | Type | Status | Usage |
|--------|------|--------|-------|
| yfinance | Market data | Rate-limited | Market data tool |
| News API / Alpha Vantage / Finnhub | News | Not configured (no API key) | News tool |
| LLM (OpenAI GPT-4o) | Generation | Not configured (no credits) | Synthesis agent |
| Synthetic financial data | Testing | ✅ Available | Financial validation benchmarks |
| Synthetic citation data | Testing | ✅ Available | Citation metrics benchmarks |

---

## 2. Data Provenance Tracking

| Aspect | Implementation |
|--------|---------------|
| Source attribution | Each data source tracked in execution metadata |
| Reporting period | Not tracked (synthetic data only) |
| Currency normalization | Not implemented (all data in USD) |
| Missing-data handling | safe_divide returns None for None/zero denominators |
| Timestamp tracking | _get_timestamp() for each node execution |
| Stale-data detection | Not implemented |
| Financial statement consistency | validate_financial_metrics() checks ranges |

---

## 3. Financial Data Quality Checks

| Check | Implemented | Details |
|-------|-------------|---------|
| Zero denominators | ✅ | safe_divide returns None |
| Negative values | ✅ | Allows negative margins, ROE, etc. |
| Missing values (None) | ✅ | safe_divide returns None for None inputs |
| Different currencies | ❌ | Not implemented |
| Different reporting periods | ❌ | Not implemented |
| Restated figures | ❌ | Not implemented |
| Stale financial information | ❌ | Not implemented |

---

## 4. Reproduction

```bash
cd "C:\projects\Equipilot AI"
python scripts/phase4/financial_validation_benchmark.py
python scripts/phase4/citation_metrics_benchmark.py
```

All data is synthetic — no real financial data, market data, or LLM output is used in benchmarks.
