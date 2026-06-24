# CLAUDE.md - EquiPilot AI Project Context

## Repository Understanding

This repository contains **EquiPilot AI** - an agentic equity research system built with Python, FastAPI, LangGraph, and Streamlit.

**Key Principle**: This is an **informational equity research assistant only**. It does NOT:
- Execute trades
- Give buy/sell recommendations
- Generate trading signals
- Claim investment advice

## Working Guidelines

### Context Management
- **Read this file first** - it contains all essential project context
- **Never rescan the whole repository** - only read files related to the current task
- **Preserve architecture** - maintain the modular structure (backend/frontend separation, schemas/services/agents/tools/graphs separation)
- **Continue previous implementation** - build upon existing foundations

### Code Style
- Keep prompts concise
- Use type hints (pydantic models)
- Follow existing patterns in the codebase
- Document all public interfaces

### Task Completion Reporting
When completing work, explain in two parts:
1. **Technical Explanation** - Files created, architecture decisions, dependencies
2. **User-Friendly Explanation** - What was created, why it was created

## Project Structure

```
equipilot-ai/
├── CLAUDE.md
├── README.md
├── .env.example
├── requirements.txt
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── schemas/
│   ├── services/
│   ├── agents/
│   ├── tools/
│   ├── prompts/
│   ├── graphs/
│   └── utils/
├── frontend/
│   ├── app.py
│   └── components/
├── docs/
│   ├── ARCHITECTURE.md
│   └── DATA_SOURCES.md
└── tests/
```

## Technology Stack

- **Backend**: Python, FastAPI, LangGraph
- **Frontend**: Streamlit
- **LLM**: OpenAI (ChatGPT API)
- **Data**: yfinance, News API (placeholder)
- **Config**: python-dotenv, pydantic-settings
- **Data Processing**: pandas