# METRICS_AND_EVALUATION.md — EquiPilot AI

**Project:** EquiPilot AI
**Date:** 2026-11-24

## Agent Metrics

| Metric | Value | Unit | Evidence |
|---|---:|---|---|
| Agent classes | 5 | count | `backend/agents/` |
| Graph nodes | 4 | count | `graphs/graph.py` |
| SynthesisAgent in graph | 0 | count | `graphs/graph.py` |

## API Metrics

| Endpoint | p50 | p95 | p99 | Mean | n |
|---|---:|---:|---:|---:|---:|
| /health | 1.47ms | 22.60ms | 34.16ms | 7.85ms | 30 |
| /ready | 2.00ms | 23.94ms | 25.72ms | 7.82ms | 30 |
| /metrics | 1.35ms | 25.33ms | 26.92ms | 5.86ms | 30 |
| /version | 1.48ms | 18.97ms | 54.42ms | 7.82ms | 30 |

## Graph Execution Metrics

| Metric | Value | Unit | Evidence |
|---|---:|---|---|---|
| End-to-end execution | ~704ms | ms | Single run |
| Tools completed | market_data, sentiment | count | Single run |
| Tools failed | none | count | Single run |

> **WARNING:** Single execution only. Not statistically significant. No LLM API calls made.

## Test Metrics

| Metric | Value |
|---|---:|
| Tests passed | 257 |
| Tests failed | 3 |
| Coverage | Not measured |

## Evaluation Gaps

| Gap | Impact | Priority |
|---|---|---:|
| No OPENAI_API_KEY | Cannot test LLM synthesis | High |
| No NEWS_API_KEY | Cannot test news integration | High |
| No human-labeled sentiment data | Cannot measure sentiment accuracy | High |
| No live deployment | Cannot test production health | Medium |
| Financial backtesting | NOT APPLICABLE | Prohibited without historical data |
