# PERFORMANCE_BENCHMARKS.md — EquiPilot AI

**Project:** EquiPilot AI
**Benchmark date:** 2026-11-24
**Hardware:** Developer workstation, 16 CPU cores, 15.65 GB RAM, CPU-only
**Software:** Python 3.12.10

## API Latency

| Endpoint | p50 | p95 | p99 | Mean | n |
|---|---:|---:|---:|---:|---:|
| /health | 1.47ms | 22.60ms | 34.16ms | 7.85ms | 30 |
| /ready | 2.00ms | 23.94ms | 25.72ms | 7.82ms | 30 |
| /metrics | 1.35ms | 25.33ms | 26.92ms | 5.86ms | 30 |
| /version | 1.48ms | 18.97ms | 54.42ms | 7.82ms | 30 |

## Graph Execution

| Metric | Value |
|---|---:|
| End-to-end execution | ~704ms (single run, placeholder report) |
| Tools completed | market_data, sentiment |
| Tools failed | none |

> **NOTE:** Single execution only. Not statistically significant. No LLM API calls made (no OPENAI_API_KEY configured).

## Agent Execution

| Component | Count | Status |
|---|---|---|
| Agent classes | 5 | All exist |
| Graph nodes | 4 | router, parallel_tools, merge_results, research |
| SynthesisAgent in graph | 0 | NOT wired |

## Evaluation Gaps

| Gap | Impact | Priority |
|---|---|---:|
| No OPENAI_API_KEY | Cannot test LLM synthesis | High |
| No NEWS_API_KEY | Cannot test news integration | High |
| No human-labeled sentiment data | Cannot measure sentiment accuracy | High |
| No live deployment | Cannot test production health | Medium |
