# EquiPilot AI - Repository Audit Report

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