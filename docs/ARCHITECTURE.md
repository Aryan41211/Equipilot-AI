# EquiPilot AI — Architecture Guide

## Overview

EquiPilot AI is an agentic equity research system built with a modular, layered architecture. The system ingests natural language queries and produces structured research reports by orchestrating specialized agents for market data, news, and sentiment analysis.

## Architecture Principles

- **Separation of Concerns**: Each layer has distinct responsibilities
- **Modular Design**: Plug-and-play agents, tools, and services
- **Centralized Configuration**: All settings via `backend/config.py` and `backend/core/constants.py`
- **Centralized Logging**: Structured JSON logging via structlog
- **Centralized Exception Handling**: Unified error responses with request tracking
- **Backward Compatibility**: Public APIs preserved through refactoring

## Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                       │
│        Streamlit Frontend (frontend/app.py)                 │
│        FastAPI REST API (backend/app.py)                    │
├─────────────────────────────────────────────────────────────┤
│                     Orchestration Layer                      │
│        LangGraph Workflows (backend/graphs/)                │
│        Agent Definitions (backend/agents/)                  │
├─────────────────────────────────────────────────────────────┤
│                     Business Logic Layer                     │
│        Services (backend/services/)                         │
│        Tools (backend/tools/)                               │
├─────────────────────────────────────────────────────────────┤
│                     Data Layer                               │
│        Schemas (backend/schemas/)                           │
│        External APIs (yfinance, NewsAPI, OpenAI)            │
├─────────────────────────────────────────────────────────────┤
│                     Core Infrastructure                      │
│        Configuration (backend/config.py)                    │
│        Constants & Enums (backend/core/)                    │
│        Logging (backend/utils/logger.py)                    │
│        Exception Handling (backend/exceptions/)             │
│        Middleware (backend/middleware/)                     │
└─────────────────────────────────────────────────────────────┘
```

## Module Responsibilities

### Core (`backend/core/`)
- **constants.py**: Application-wide enums, status codes, error types
- **exceptions.py**: Base exception hierarchy

### Configuration (`backend/config.py`)
- Pydantic-based settings management
- Environment variable loading
- Production mode enforcement

### Schemas (`backend/schemas/`)
- **research.py**: API request/response models
- **market_data.py**: Market data structures
- **news.py**: News article models
- **sentiment.py**: Sentiment analysis models
- **report.py**: Research report structures
- **entity_resolution.py**: Entity resolution models

### Services (`backend/services/`)
- **llm_service.py**: OpenAI API wrapper
- **market_service.py**: yfinance market data
- **news_service.py**: News API integration
- **sentiment_service.py**: LLM-powered sentiment analysis
- **entity_resolution_service.py**: Ticker resolution

### Agents (`backend/agents/`)
- **router_agent.py**: Query classification and routing
- **market_agent.py**: Market data collection agent
- **news_agent.py**: News collection agent
- **sentiment_agent.py**: Sentiment analysis agent
- **synthesis_agent.py**: Report generation agent

### Graphs (`backend/graphs/`)
- **graph.py**: Dynamic LangGraph workflow
- **nodes.py**: Workflow node implementations
- **state.py**: Graph state schema

### Tools (`backend/tools/`)
- **market_data_tool.py**: LangGraph-compatible market data tool
- **news_tool.py**: LangGraph-compatible news tool
- **sentiment_tool.py**: LangGraph-compatible sentiment tool
- **entity_resolution_tool.py**: Entity resolution tool

### Middleware (`backend/middleware/`)
- **production.py**: Rate limiting, security headers, metrics

### Utils (`backend/utils/`)
- **logger.py**: Structured logging setup
- **helpers.py**: Common utility functions
- **validators.py**: Input validation utilities

## Data Flow

1. **User Query** → Streamlit frontend sends request to FastAPI
2. **API Validation** → FastAPI validates request via Pydantic schemas
3. **LangGraph Workflow** → Orchestrator routes through agents:
   - Router Agent → Classifies intent, extracts tickers
   - Market Data Agent → Fetches price/fundamentals
   - News Agent → Fetches relevant news
   - Sentiment Agent → Analyzes news sentiment
   - Synthesis Agent → Generates structured report
4. **Response** → Research report returned via API

## Extension Points

- **New Data Sources**: Add new services in `backend/services/`
- **New Tools**: Add LangGraph-compatible tools in `backend/tools/`
- **New Agents**: Add agent classes in `backend/agents/`
- **New Schemas**: Add Pydantic models in `backend/schemas/`
- **Custom Middleware**: Add in `backend/middleware/`