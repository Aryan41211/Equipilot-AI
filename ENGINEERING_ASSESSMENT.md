# ENGINEERING_ASSESSMENT.md — EquiPilot AI

**Project:** EquiPilot AI — Agentic Equity Research Platform
**Assessment date:** 2026-11-24
**Maturity level:** LEVEL 2 — TESTED

## Architecture

```
Streamlit UI → FastAPI → LangGraph Orchestration → Agents/Tools → External APIs
                                          ↓
                                  In-memory research store
```

## Agent Graph

| Component | Count | Status |
|---|---|---|
| Agent classes | 5 | All exist (Router, Market Data, News, Sentiment, Synthesis) |
| Graph nodes (compiled) | 4 | router, parallel_tools, merge_results, research |
| SynthesisAgent in graph | 0 | NOT wired |

## Components

| Component | Status | Evidence |
|---|---|---|
| Router agent | Implemented | `backend/agents/router_agent.py` |
| Market data agent | Implemented | `backend/agents/market_agent.py` |
| News agent | Implemented | `backend/agents/news_agent.py` |
| Sentiment agent | Implemented | `backend/agents/sentiment_agent.py` |
| Synthesis agent | Implemented, NOT wired | `backend/agents/synthesis_agent.py` |
| yfinance integration | Implemented | `backend/tools/yfinance_tool.py` |
| LLM sentiment | Implemented (needs API key) | `backend/services/sentiment_service.py` |
| Health endpoints | Implemented + measured | `/health`, `/ready`, `/version`, `/metrics` |
| Rate limiting | Implemented | `backend/middleware/production.py` |
| Security headers | Implemented | `backend/middleware/production.py` |

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

## Known Issues

1. SynthesisAgent not wired into compiled graph
2. Active report is placeholder ("No LLM integration")
3. Citations not returned (`citations=None`)
4. No OPENAI_API_KEY/NEWS_API_KEY configured
5. No live deployment URL
6. Financial prediction accuracy not evaluated (no backtest — prohibited)

## Assessment Summary

| Area | Rating | Notes |
|---|---|---|
| Architecture | Good | Modular FastAPI + LangGraph |
| Code Quality | Good | Type hints, pydantic models, exception handling |
| Testing | Good | 257 tests passing |
| Security | Good | Rate limiting, security headers, CORS |
| Performance | Measured | API p50 ~1.5ms |
| Agent Quality | Measured | Graph execution ~704ms |
| ML/AI Quality | Not measured | No LLM API key configured |
| Observability | Good | Structured logging, metrics endpoint |
| Deployment | Configured | Docker/Nginx, not tested |
