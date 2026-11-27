# PHASE 4 — EquiPilot AI Evaluation

**Project:** EquiPilot AI — Agentic Equity Research System
**Phase:** 4 — Benchmark Breakthrough
**Date:** 2026-11-25
**Git SHA:** 5087a7a
**Environment:** 16 CPU cores, 15.65 GB RAM, CPU-only

---

## 1. Graph Architecture Fix

Phase 3 fixed the orphaned `merge_results` node. Phase 4 verifies end-to-end execution:

| Node | Status | Role |
|------|--------|------|
| router | ✅ Operational | Extracts ticker, classifies intent |
| parallel_tools | ✅ Operational | Concurrent market data + news + sentiment |
| synthesis | ⚠️ Placeholder | Falls back to placeholder (no LLM API key) |
| research | ✅ Operational | Assembles final report |
| merge_results | ✅ Operational | Merges intermediate results (fixed in Phase 3) |

**Graph flow:** router → parallel_tools → synthesis → research → merge_results → END

## 2. Financial Validation

All 13 financial calculation functions validated against 4 reference cases (TechCorp, DistressedCo, StartupCo, UtilityCo):

| Metric | Cases Tested | All Passed |
|--------|-------------|------------|
| revenue_growth | 4 | ✅ |
| gross_margin | 4 | ✅ |
| operating_margin | 4 | ✅ |
| net_margin | 4 | ✅ |
| ebitda_margin | 4 | ✅ |
| eps_growth | 4 | ✅ |
| roe | 4 | ✅ |
| roce | 4 | ✅ |
| debt_to_equity | 4 | ✅ |
| current_ratio | 4 | ✅ |
| free_cash_flow | 4 | ✅ |
| pe_ratio | 4 | ✅ |
| pb_ratio | 4 | ✅ |
| ps_ratio | 4 | ✅ |
| ev_ebitda | 4 | ✅ |

**Edge cases tested (11/11 passed):** zero denominators, None inputs, negative values.

## 3. Citation Metrics

| Metric | Value | Target |
|--------|-------|--------|
| Mean citation precision | 0.8000 | 0.95+ |
| Mean citation coverage | 0.6333 | 0.85+ |
| Mean unsupported claim rate | 0.3667 | <0.05 |
| Precision matches expected | 5/5 | 100% |
| Coverage matches expected | 4/5 | 100% |

**Note:** Coverage mismatch on cite-002 due to rounding (0.6667 vs 0.67 expected). All precision values match exactly.

## 4. Agent Performance

| Metric | Value |
|--------|-------|
| Test queries | 5 |
| Successful executions | 2/5 |
| Failed executions | 3/5 (yfinance rate-limited) |
| Success rate | 0.4000 |
| p50 latency | 21,430ms |
| p95 latency | 25,486ms |

**Note:** High latency due to yfinance rate limiting (3 retries per query, 3-second delays). No LLM API key configured — synthesis falls back to placeholder.

## 5. Limitations

- No OPENAI_API_KEY — LLM synthesis not measurable
- yfinance rate-limited — live market data testing limited
- Only 4 financial reference cases (synthetic data)
- Only 5 citation test cases (synthetic data)
- No human review of report quality

## 6. Reproduction

```bash
cd "C:\projects\Equipilot AI"
python scripts/phase4/financial_validation_benchmark.py
python scripts/phase4/citation_metrics_benchmark.py

# Output: experiment_results/phase4/financial_validation_results.json
# Output: experiment_results/phase4/citation_and_performance_results.json
```
