# BASELINE_METRICS.md — EquiPilot AI

**Project:** EquiPilot AI — Agentic Equity Research Platform
**Baseline date:** 2026-11-24
**Git baseline commit:** a58a5bd

## Test Baseline

| Metric | Value | Unit | Evidence | Confidence |
|---|---:|---|---|---|
| Tests passed | 257 | count | `pytest tests` | HIGH |
| Tests failed | 3 | count | `pytest tests` | HIGH |
| Tests skipped | 0 | count | `pytest tests` | HIGH |

> **Note:** 3 failures are environment-related (deploy config docs, frontend connection test) — not core logic failures.

## Functional Baseline

| Feature | Status | Evidence | Confidence |
|---|---|---|---|
| Router agent | Implemented (code exists) | `backend/agents/router_agent.py` | HIGH |
| Market data agent | Implemented (code exists) | `backend/agents/market_agent.py` | HIGH |
| News agent | Implemented (code exists) | `backend/agents/news_agent.py` | HIGH |
| Sentiment agent | Implemented (code exists) | `backend/agents/sentiment_agent.py` | HIGH |
| Synthesis agent | Implemented (code exists, NOT wired) | `backend/agents/synthesis_agent.py` | MEDIUM |
| yfinance integration | Implemented (code exists) | `backend/tools/yfinance_tool.py` | MEDIUM |
| LLM-based sentiment | Implemented (code exists, needs API key) | `backend/services/sentiment_service.py` | MEDIUM |
| Citation generation | Implemented (code exists, NOT wired) | `backend/agents/synthesis_agent.py` | MEDIUM |
| Risk factor generation | Implemented (code exists, NOT wired) | `backend/agents/synthesis_agent.py` | MEDIUM |
| Health endpoint | Implemented + measured | `/health` returns 200 | HIGH |
| Metrics endpoint | Implemented + measured | `/metrics` returns 200 | HIGH |
| Readiness endpoint | Implemented + measured | `/ready` returns 200 | HIGH |
| Version endpoint | Implemented + measured | `/version` returns 200 | HIGH |
| Rate limiting | Implemented (code exists) | `backend/middleware/production.py` | HIGH |
| Security headers | Implemented (code exists) | `backend/middleware/production.py` | HIGH |
| Docker/Nginx | Configured (not built) | `docker-compose.yml`, `Dockerfile`, `nginx.conf` | MEDIUM |

## Graph Baseline

| Component | Count | Status |
|---|---|---|
| Agent classes | 5 | All exist |
| Graph nodes (compiled) | 4 | router, parallel_tools, merge_results, research |
| SynthesisAgent in graph | 0 | NOT wired |
| Active report | Placeholder | "(No LLM integration.)" |
| Citations in API | None | `citations=None` |

## API Latency Baseline

| Endpoint | p50 | p95 | p99 | Mean | n |
|---|---:|---:|---:|---:|---:|
| /health | 1.47ms | 22.60ms | 34.16ms | 7.85ms | 30 |
| /ready | 2.00ms | 23.94ms | 25.72ms | 7.82ms | 30 |
| /metrics | 1.35ms | 25.33ms | 26.92ms | 5.86ms | 30 |
| /version | 1.48ms | 18.97ms | 54.42ms | 7.82ms | 30 |

## Graph Execution Baseline

| Metric | Value | Unit | Evidence |
|---|---:|---|---|
| End-to-end execution | ~704ms | ms | Single run (placeholder report) |
| Tools completed | market_data, sentiment | count | Single run |
| Tools failed | none | count | Single run |

## Known Issues

1. SynthesisAgent not wired into compiled graph (4 nodes instead of 5)
2. Active report is placeholder ("No LLM integration")
3. Citations not returned (`citations=None`)
4. No OPENAI_API_KEY configured (LLM features not testable)
5. No NEWS_API_KEY configured (news features use fallback)
6. No live deployment URL
7. Financial prediction accuracy not evaluated (no backtest)

## Known Limitations

- All metrics based on single run (not statistically significant)
- No external API calls made (no API keys)
- Financial accuracy claims prohibited (no backtest)
