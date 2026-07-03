# CLAUDE.md — EquiPilot AI Project Context

## Repository Understanding

This repository contains **EquiPilot AI** — an agentic equity research system built with Python, FastAPI, LangGraph, and Streamlit.

**Key Principle**: This is an **informational equity research assistant only**. It does NOT:
- Execute trades
- Give buy/sell recommendations
- Generate trading signals
- Claim investment advice

## Working Guidelines

### Context Management
- **Read this file first** — it contains all essential project context
- **Never rescan the whole repository** — only read files related to the current task
- **Preserve architecture** — maintain the modular structure (backend/frontend separation, core/schemas/services/agents/tools/graphs separation)
- **Continue previous implementation** — build upon existing foundations

### Code Style
- Keep prompts concise
- Use type hints (pydantic models)
- Follow existing patterns in the codebase
- Document all public interfaces

### Task Completion Reporting
When completing work, explain in two parts:
1. **Technical Explanation** — Files created, architecture decisions, dependencies
2. **User-Friendly Explanation** — What was created, why it was created

## Project Structure

```
equipilot-ai/
├── CLAUDE.md
├── README.md
├── AUDIT_REPORT.md          # Repository audit findings
├── .env.example
├── requirements.txt         # Runtime dependencies
├── requirements-dev.txt     # Development dependencies
├── pyproject.toml           # Tool configuration
├── backend/
│   ├── app.py              # FastAPI app factory & routes
│   ├── config.py           # Pydantic settings management
│   ├── core/               # 🔵 NEW: Centralized infrastructure
│   │   ├── __init__.py
│   │   ├── constants.py    # Enums, status codes, constants
│   │   └── exceptions.py   # Base exception hierarchy
│   ├── schemas/            # Pydantic request/response models
│   ├── services/           # Business logic & external integrations
│   ├── agents/             # LangGraph agent definitions
│   ├── tools/              # LangGraph function tools
│   ├── prompts/            # LLM prompt templates
│   ├── graphs/             # LangGraph workflow definitions
│   ├── middleware/         # Production middleware
│   ├── exceptions/         # Domain exception hierarchy & handlers
│   └── utils/              # Utility functions (logger, helpers, validators)
├── frontend/
│   ├── app.py             # Streamlit main application
│   ├── healthz.py         # Docker health check server
│   └── components/        # Reusable UI components
├── docs/
│   ├── architecture.md    # System architecture
│   ├── api.md             # API reference
│   ├── deployment.md      # Deployment guide
│   ├── testing.md         # Testing guide
│   └── troubleshooting.md # Common issues
└── tests/                 # Comprehensive test suite
```

## Technology Stack

- **Backend**: Python 3.12, FastAPI 0.115, LangGraph 0.2
- **Frontend**: Streamlit 1.39
- **LLM**: OpenAI (GPT-4o / GPT-4o-mini)
- **Data**: yfinance, News API, Alpha Vantage, Finnhub
- **Config**: pydantic-settings
- **Logging**: structlog (structured JSON)
- **Testing**: pytest, pytest-asyncio

## Key Architecture Decisions

### Centralized Infrastructure (`backend/core/`)
- **constants.py**: Application-wide enums (`ExecutionStatus`, `ResearchIntent`, `ErrorType`) eliminate hardcoded strings
- **exceptions.py**: Base `EquiPilotError` class for all domain exceptions

### Exception Hierarchy
```
EquiPilotError
├── ConfigurationError
├── ServiceError
├── ToolError
├── ProviderError
└── ValidationError
```

### UI Design System
- Single design system: `frontend/components/design_system_ui.py`
- Duplicates (`design_system.py`, `design_system_clean.py`) archived

### Dependency Management
- `requirements.txt`: Runtime dependencies only
- `requirements-dev.txt`: Testing & development tools