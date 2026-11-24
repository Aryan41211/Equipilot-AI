# IMPLEMENTATION_ROADMAP.md — EquiPilot AI

**Project:** EquiPilot AI
**Roadmap date:** 2026-11-24

## Completed

| Task | Status | Description |
|---|---|---|
| Wire SynthesisAgent into graph | DONE | Added as 5th node in LangGraph workflow |
| Add citations to API response | DONE | `citations` field now populated from synthesis |
| Add citation fields to GraphState | DONE | `citations`, `synthesis_result` fields |
| Wire SynthesisAgent into app.py response | DONE | `get_research()` returns citations |
| 257 tests passing | DONE | 3 pre-existing failures (env-related) |

## In Progress

| Task | Status | Description |
|---|---|---|
| Market data reliability testing | PLANNED | Requires yfinance API access |
| Sentiment evaluation dataset | PLANNED | Requires human-labeled data |
| Citation validation | PLANNED | Requires source references |

## Not Started

| Task | Status |
|---|---|
| LLM-based synthesis with real API key | NOT STARTED | Requires OPENAI_API_KEY |
| News API integration | NOT STARTED | Requires NEWS_API_KEY |
| Live deployment | NOT STARTED | Docker/Nginx configured, not deployed |
| Financial backtesting | NOT APPLICABLE | Prohibited without historical data |

## Acceptance Criteria

| Criterion | Status |
|---|---|
| All 5 agents connected | NOT STARTED |
| Complete graph execution | NOT STARTED |
| Synthesis functional | NOT STARTED |
| Citations validated | NOT STARTED |
| Market data provenance | NOT STARTED |
| Error handling tested | PARTIAL (code review) |
| Agent evaluation reproducible | NOT STARTED |
| Critical tests passing | DONE (257 passed) |
