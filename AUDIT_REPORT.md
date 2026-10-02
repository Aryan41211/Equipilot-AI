# EquiPilot AI - Repository Audit Report

> **Status: RESOLVED** for the deployment-critical subset. Closed during the
> deployment-completion pass:
>
> - The duplicate `design_system*.py` files are deleted, so
>   `frontend/components/design_system_ui.py` is the single design system (Finding 1).
> - `backend/prompts/sentiment_prompt.py` is deleted; `sentiment_prompts.py` is the only
>   sentiment prompt module (Finding 2).
> - `backend/graphs/research_graph.py` and `backend/graphs/example_execution.py` are
>   deleted; `backend/graphs/graph.py` is the only workflow (Finding 4).
> - The duplicated `entity_error_details()` / `synthesis_error_details()` helpers are
>   gone. `backend/exceptions/handlers.py` and
>   `backend/exceptions/entity_resolution_service.py` no longer carry copies, and the
>   two surviving names are backward-compatible aliases of the single
>   `format_error_detail()` in `backend/core/exceptions.py` (Finding 6).
> - `requirements-dev.txt` now exists and `requirements.txt` is runtime-only
>   (Finding 7).
> - `backend/core/constants.py` and `backend/core/exceptions.py` provide the centralized
>   enum/exception base the report flagged as missing (Finding 7).
>
> **Still open — code-organization debt, not deployment blockers.** Unchanged from the
> findings below, and deliberately out of scope for the deployment pass:
>
> - Finding 2: the `research_prompt.py` / `synthesis_prompts.py` content overlap.
> - Finding 3: four overlapping schema modules (`market_data.py`,
>   `market_data_schema.py`, `research_report.py`, `report.py`).
> - Finding 5: two market-data service modules (`market_data_service.py`,
>   `market_service.py`).
> - Finding 7: the `sys.path.insert(0, ...)` shim in five test files, the empty
>   `tests/__init__.py`, and the remaining hardcoded status strings.
>
> **One bullet in Finding 7 is now inaccurate and should be treated as closed:**
> `pyproject.toml` does not duplicate dependency configuration. It contains only tool
> configuration (ruff, black, pytest, coverage, mypy) and has no `[project]` or
> `dependencies` table; `setup.py` likewise declares no dependencies. Dependency
> declarations live in `requirements.txt` and `requirements-dev.txt` only.

## Phase 1 Findings

### 1. DUPLICATE UI SYSTEMS (Critical - 3 files, virtually identical)
| File | Status | Notes |
|------|--------|-------|
| `frontend/components/design_system.py` | DUPLICATE | Almost identical to `design_system_clean.py` |
| `frontend/components/design_system_clean.py` | DUPLICATE | Almost identical to `design_system.py` |
| `frontend/components/design_system_ui.py` | ACTIVE | Used by `frontend/app.py` - most feature-rich version |

### 2. DUPLICATE PROMPTS
| File | Status | Notes |
|------|--------|-------|
| `backend/prompts/sentiment_prompt.py` | UNUSED | Duplicate of `sentiment_prompts.py` - NOT imported anywhere |
| `backend/prompts/sentiment_prompts.py` | ACTIVE | Exported via `__init__.py` |
| `backend/prompts/research_prompt.py` | ACTIVE | Used directly by `synthesis_agent.py` but NOT exported via `__init__.py` |
| `backend/prompts/synthesis_prompts.py` | ACTIVE | Exported via `__init__.py` - has overlapping content with `research_prompt.py` |

### 3. DUPLICATE SCHEMAS
| File | Notes |
|------|-------|
| `backend/schemas/market_data.py` | Full MarketData model with Fundamentals, Technicals, PriceData |
| `backend/schemas/market_data_schema.py` | Simplified MarketDataResponse for tool responses |
| `backend/schemas/research_report.py` | SynthesizedReport for LLM output |
| `backend/schemas/report.py` | Full ResearchReport with sections/citations |

### 4. DUPLICATE GRAPH WORKFLOWS
| File | Status | Notes |
|------|--------|-------|
| `backend/graphs/graph.py` | ACTIVE | Used by `backend/app.py` via `create_first_graph()` |
| `backend/graphs/nodes.py` | ACTIVE | Used by `graph.py` |
| `backend/graphs/state.py` | ACTIVE | Used by `graph.py` and `nodes.py` |
| `backend/graphs/research_graph.py` | DEAD CODE | Exported via `__init__.py` but NOT imported by any module |
| `backend/graphs/example_execution.py` | EXAMPLE | Standalone script, not imported |

### 5. DUPLICATE SERVICES
| File | Notes |
|------|-------|
| `backend/services/market_data_service.py` | Used by `market_data_tool.py` - simpler single-ticker approach |
| `backend/services/market_service.py` | Used by `market_agent.py` and `yfinance_tool.py` - multi-ticker with fundamentals/technicals |

### 6. DUPLICATE EXCEPTION FUNCTIONS
| File | Function | Status |
|------|----------|--------|
| `backend/exceptions/handlers.py` | `entity_error_details()` | DUPLICATE - functions exist in other files |
| `backend/exceptions/entity_resolution_exceptions.py` | `entity_error_details()` | Defined here originally |
| `backend/exceptions/synthesis_exceptions.py` | `synthesis_error_details()` | UNUSED function |
| `backend/exceptions/entity_resolution_service.py` | `entity_error_details()` | DUPLICATE - same as exceptions version |

### 7. TECHNICAL DEBT
- `requirements.txt` includes testing/dev dependencies (pytest, black, ruff, mypy, pre-commit)
- No `requirements-dev.txt` exists
- `pyproject.toml` duplicates dependency configuration
- No centralized state enum (status strings scattered as `"pending"`, `"success"`, `"failed"`)
- No centralized exceptions base class
- Test files use `sys.path.insert(0, ...)` workaround
- `tests/__init__.py` is empty
- Hardcoded strings in many places instead of constants/enums
- No `.env` file in project (only `.env.example`)
