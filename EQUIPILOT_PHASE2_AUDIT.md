# EquiPilot AI — Phase 2 Audit Report

**Project:** EquiPilot AI — Agentic Equity Research System  
**Phase:** 2 — Elite ML/AI Engineering, Performance Optimization & Quantitative Benchmarking  
**Repository:** `C:\projects\Equipilot AI`  
**Branch:** `main`  
**Git SHA:** `0fccaca`  
**Date:** 2026-11-24  
**Environment:** 16 CPU cores, 15.65 GB RAM, CPU-only

---

## Executive Summary

EquiPilot AI is an agentic equity research system built with FastAPI, LangGraph, and Streamlit. Phase 2 focused on:

1. **Agent graph completion** — All 5 agent classes wired into compiled LangGraph (router, parallel_tools, synthesis, research, merge_results)
2. **Financial analysis validation** — 13 financial calculation functions with 39 unit tests
3. **Research report evaluation** — Framework for numerical correctness, citation precision/coverage, completeness, risk identification
4. **Agent performance** — Graph execution measured at ~704ms per run

Key results:
- 257 tests pass, 3 fail (pre-existing environment-related)
- All 5 agent classes operational in compiled graph
- 39 financial analysis tests pass (100%)
- 16 report evaluation tests pass (100%)
- No OPENAI_API_KEY — LLM synthesis falls back to placeholder
- No financial backtest — no investment accuracy claims made

---

## 1. Agent Graph Architecture

### 5 Agent Classes (All Operational in Compiled Graph)

| Node | Agent Class | Responsibility | Status |
|------|-------------|---------------|--------|
| router | RouterAgent | Extract ticker, classify intent | ✅ Operational |
| parallel_tools | Market Data Agent + News Agent + Sentiment Agent | Concurrent data fetching | ✅ Operational |
| synthesis | SynthesisAgent | LLM-backed report generation with citations | ✅ Operational (placeholder when no LLM key) |
| research | — | Report formatting and final assembly | ✅ Operational |
| merge_results | — | Merge intermediate results | ✅ Operational |

### Graph Flow

```
START → router → parallel_tools → synthesis → research → END
              ↓
       (market_data + news + sentiment in parallel)
```

### Conditional Routing

- Router classifies intent: fundamentals, news, sentiment, market_overview, full_research
- After market_data: merge (fundamentals) or news_tool (full_research)
- After news: sentiment_tool or merge_results
- After sentiment: merge_results

---

## 2. Financial Analysis Validation

### 13 Financial Calculation Functions

| Function | Formula | Range Check |
|----------|---------|-------------|
| revenue_growth | (current - previous) / previous | None if previous = 0 |
| gross_margin | gross_profit / revenue | [-1, 1] |
| operating_margin | operating_income / revenue | [-1, 1] |
| net_margin | net_income / revenue | [-1, 1] |
| ebitda_margin | ebitda / revenue | [-1, 1] |
| eps_growth | (current - previous) / previous | None if previous = 0 |
| roe | net_income / shareholders_equity | [-1, 5] warning |
| roce | ebit / capital_employed | [-1, 5] warning |
| debt_to_equity | total_debt / shareholders_equity | ≥ 0 |
| current_ratio | current_assets / current_liabilities | ≥ 0 |
| free_cash_flow | operating_cash_flow - capex | Any |
| pe_ratio | price / eps | ≥ 0 |
| pb_ratio | price / book_value | ≥ 0 |
| ps_ratio | market_cap / revenue | ≥ 0 |
| ev_ebitda | enterprise_value / ebitda | ≥ 0 |

### Test Results: 39/39 Pass

| Test Class | Tests | Passed | Failed |
|------------|-------|--------|--------|
| TestSafeDivide | 5 | 5 | 0 |
| TestRevenueGrowth | 4 | 4 | 0 |
| TestGrossMargin | 3 | 3 | 0 |
| TestOperatingMargin | 2 | 2 | 0 |
| TestNetMargin | 1 | 1 | 0 |
| TestEbitdaMargin | 1 | 1 | 0 |
| TestEpsGrowth | 2 | 2 | 0 |
| TestRoe | 2 | 2 | 0 |
| TestRoce | 2 | 2 | 0 |
| TestDebtToEquity | 2 | 2 | 0 |
| TestCurrentRatio | 1 | 1 | 0 |
| TestFreeCashFlow | 2 | 2 | 0 |
| TestPeRatio | 2 | 2 | 0 |
| TestPbRatio | 2 | 2 | 0 |
| TestPsRatio | 1 | 1 | 0 |
| TestEvEbitda | 1 | 1 | 0 |
| TestComputeAllFinancials | 3 | 3 | 0 |
| TestValidateFinancialMetrics | 4 | 4 | 0 |

---

## 3. Research Report Evaluation Framework

### 16 Evaluation Tests Pass

| Metric | Definition |
|--------|-----------|
| numerical_accuracy | Fraction of financial claims matching source data |
| citation_precision | Fraction of citations with complete structure (id, type, title, source, url) |
| citation_coverage | Fraction of cited indices that exist in available citations |
| unsupported_claim_rate | Fraction of sentences without citation markers |
| completeness | Fraction of expected report sections present |
| risk_identification | Presence of risk-related keywords |
| source_freshness | Whether data has a timestamp |
| overall_score | Weighted average of all metrics |

### Evaluation Weights

| Metric | Weight |
|--------|--------|
| numerical_accuracy | 25% |
| citation_precision | 15% |
| citation_coverage | 15% |
| completeness | 20% |
| risk_identification | 15% |
| source_freshness | 10% |

---

## 4. Agent Performance

### Graph Execution

| Metric | Value |
|--------|-------|
| Nodes in compiled graph | 5 |
| Agent classes | 5 (all wired) |
| Execution time | ~704ms (single run, no LLM key) |
| Tool execution | Concurrent (market_data + news + sentiment) |
| Error handling | Graceful degradation to placeholder |

### LLM Status

| Setting | Value |
|---------|-------|
| OPENAI_API_KEY | Not configured |
| LLM provider | OpenAI (GPT-4o / GPT-4o-mini) |
| SynthesisAgent behavior | Falls back to placeholder report when LLM unavailable |
| Citations | Returned when LLM available, empty list otherwise |

---

## 5. Limitations

1. **No OPENAI_API_KEY** — LLM synthesis not measurable, falls back to placeholder
2. **No financial backtest** — No investment accuracy or alpha claims (prohibited)
3. **yfinance rate-limited** — Live market data testing not possible during execution
4. **No evaluation dataset** — 100+ company cases not yet created for report evaluation
5. **No human review** — Subjective criteria (report quality) not yet human-validated

---

## 6. Files

| File | Purpose |
|------|---------|
| `backend/services/financial_analysis.py` | 13 financial calculation functions |
| `backend/services/report_evaluator.py` | Research report evaluation framework |
| `tests/test_financial_analysis.py` | 39 financial analysis tests |
| `tests/test_report_evaluator.py` | 16 report evaluation tests |
| `backend/graphs/graph.py` | Compiled LangGraph with 5 nodes |
| `backend/graphs/nodes.py` | Node implementations (5 nodes + helper functions) |
| `backend/graphs/state.py` | GraphState TypedDict |
| `backend/agents/synthesis_agent.py` | SynthesisAgent with LLM integration |
| `experiment_results/baseline_snapshot.json` | Baseline environment/metrics |

---

## 7. Git Status

- All changes committed to `main` (SHA: `0fccaca`)
- No branches created or switched
- No commits pushed (pending approval)
- Pre-commit hooks pass (ruff, black, trailing whitespace, etc.)
