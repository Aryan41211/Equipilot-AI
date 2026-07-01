# EquiPilot AI — System Architecture

## Overview

EquiPilot AI follows a modular, agent-based architecture using LangGraph for workflow orchestration. The system separates concerns into distinct layers: API, orchestration, agents, tools, and data processing. This design enables maintainability, testability, and extensibility.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              User Interface                                 │
│  ┌─────────────────────────────┐          ┌─────────────────────────────┐   │
│  │     Streamlit Frontend      │          │     REST API (FastAPI)      │   │
│  │  • Query Input              │◄────────►│  • /api/v1/research         │   │
│  │  • Progress Tracking        │   HTTP   │  • /health, /ready         │   │
│  │  • Report Visualization     │          │  • /version, /metrics      │   │
│  └─────────────────────────────┘          └─────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          API Layer (FastAPI)                                 │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   CORS       │  │  Security    │  │   Metrics    │  │   Rate       │    │
│  │  Middleware  │  │   Headers    │  │  Middleware  │  │  Limiting    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Request    │  │  Exception   │  │  Structured  │  │  Pydantic    │    │
│  │     ID       │  │   Handlers   │  │   Logging    │  │  Validation  │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      LangGraph Orchestration                                │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         Research Graph                               │    │
│  │                                                                      │    │
│  │  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐         │    │
│  │  │    Router    │────▶│    Market    │────▶│     News     │         │    │
│  │  │    Agent     │     │  Data Agent  │     │    Agent     │         │    │
│  │  └──────────────┘     └──────────────┘     └──────────────┘         │    │
│  │         │                                                           │    │
│  │         │                    ┌──────────────┐                       │    │
│  │         └───────────────────▶│  Sentiment   │                       │    │
│  │                              │    Agent     │                       │    │
│  │                              └──────────────┘                       │    │
│  │                                     │                               │    │
│  │                                     ▼                               │    │
│  │                              ┌──────────────┐                       │    │
│  │                              │  Synthesis   │                       │    │
│  │                              │  Agent (LLM) │                       │    │
│  │                              └──────────────┘                       │    │
│  │                                     │                               │    │
│  │                                     ▼                               │    │
│  │                              ┌──────────────┐                       │    │
│  │                              │   Output     │                       │    │
│  │                              │  Formatter   │                       │    │
│  │                              └──────────────┘                       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         ▼                          ▼                          ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│    yfinance      │    │    News API      │    │   OpenAI API     │
│  (Market Data)   │    │  (News Data)     │    │   (LLM)          │
│                  │    │                  │    │                  │
│ • Price/Volume   │    │ • Articles       │    │ • GPT-4o         │
│ • Fundamentals   │    │ • Headlines      │    │ • GPT-4o-mini    │
│ • Financials     │    │ • Sources        │    │ • Structured     │
│ • Technical      │    │ • Timestamps     │    │   Output         │
└──────────────────┘    └──────────────────┘    └──────────────────┘
```

---

## Layer Architecture

### 1. Presentation Layer

**Streamlit Frontend** (`frontend/`)
- Provides an interactive web interface for submitting research queries
- Displays real-time progress of the research workflow
- Renders formatted research reports with data tables and citations
- Manages session state for query history

**REST API** (`backend/app.py`)
- FastAPI application with automatic OpenAPI documentation
- Endpoints for research submission, retrieval, and status checking
- Health monitoring endpoints for orchestration systems
- Request validation using Pydantic schemas

### 2. API Middleware Layer

The middleware stack processes every request in order:

| Middleware | Order | Purpose |
|-----------|-------|---------|
| CORS | 1st | Allows cross-origin requests from frontend |
| Rate Limiting | 2nd | Enforces request rate limits per client IP |
| Security Headers | 3rd | Adds CSP, HSTS, XSS protection headers |
| Metrics | 4th | Tracks request counts, durations, status codes |
| Request ID | 5th | Generates unique UUID for each request |
| Request Logging | 6th | Logs request/response with structured format |

### 3. Orchestration Layer (LangGraph)

**Research Graph** (`backend/graphs/`)
- Defines the state machine for the research workflow
- Manages state transitions between agents
- Handles error recovery and partial results
- Supports checkpointing for long-running workflows

**State Schema**:
```python
class ResearchState(TypedDict):
    query: str                          # Original user query
    tickers: List[str]                  # Extracted ticker symbols
    market_data: Optional[MarketData]   # Collected market data
    news_articles: List[NewsArticle]    # Fetched news articles
    sentiment: Optional[SentimentData]  # Sentiment analysis results
    report: Optional[ResearchReport]    # Generated research report
    errors: List[str]                   # Accumulated errors
    current_step: str                   # Current workflow stage
```

### 4. Agent Layer

Each agent is a specialized LangGraph node with a specific responsibility:

| Agent | File | Responsibility |
|-------|------|----------------|
| **Router Agent** | `agents/router_agent.py` | Classifies query intent, extracts tickers, determines required tools |
| **Market Data Agent** | `agents/market_agent.py` | Orchestrates market data collection via yfinance |
| **News Agent** | `agents/news_agent.py` | Fetches and filters financial news articles |
| **Sentiment Agent** | `agents/sentiment_agent.py` | Analyzes news for sentiment scoring and theme extraction |
| **Synthesis Agent** | `agents/synthesis_agent.py` | Generates final research report using LLM |

### 5. Tool Layer

Tools are reusable functions that agents call to interact with external systems:

| Tool | File | External System |
|------|------|-----------------|
| `get_market_data` | `tools/market_data_tool.py` | yfinance |
| `get_news` | `tools/news_tool.py` | News API |
| `analyze_sentiment` | `tools/sentiment_tool.py` | OpenAI |

### 6. Service Layer

Services wrap external API calls with error handling, caching, and retry logic:

| Service | File | Wraps |
|---------|------|-------|
| `MarketService` | `services/market_service.py` | yfinance |
| `NewsService` | `services/news_service.py` | News API |
| `SentimentService` | `services/sentiment_service.py` | OpenAI |
| `LLMService` | `services/llm_service.py` | OpenAI |

### 7. Data Layer (Schemas)

Pydantic models define the structure of all data flowing through the system:

| Schema File | Models |
|-------------|--------|
| `schemas/research.py` | `ResearchRequest`, `ResearchResponse`, `ResearchStatus` |
| `schemas/market_data.py` | `PriceData`, `FundamentalsData`, `MarketData`, `MarketDataResponse` |
| `schemas/news.py` | `NewsArticle`, `NewsResponse` |
| `schemas/sentiment.py` | `SentimentData`, `SentimentResponse` |
| `schemas/report.py` | `Citation`, `ReportSection`, `ResearchReport` |

---

## Data Flow

### Request Lifecycle

```
1. User submits query via Streamlit or API
         │
2. FastAPI validates request against ResearchRequest schema
         │
3. Request ID generated, request logged
         │
4. Rate limit checked, security headers added
         │
5. LangGraph research graph begins execution
         │
6. Router Agent classifies query, extracts tickers
         │
7. Market Data Agent fetches price/fundamental data
         │
8. News Agent retrieves relevant news articles
         │
9. Sentiment Agent analyzes news for sentiment
         │
10. Synthesis Agent generates report via LLM
         │
11. Output Formatter structures the final response
         │
12. Response returned to user with request ID
```

### Error Handling Flow

```
Agent Error Occurred
         │
         ▼
┌─────────────────────┐
│  Error Caught by    │
│  Agent Error Handler│
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  Error Added to     │
│  State.errors list  │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  Workflow Continues │
│  with Partial Data  │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  API Exception      │
│  Handler Formats    │
│  Error Response     │
└─────────────────────┘
```

---

## Production Infrastructure

### Deployment Architecture

```
Internet
    │
    ▼
┌──────────┐
│  nginx   │  Port 80/443 — Reverse proxy, SSL termination, rate limiting
└──────────┘
    │
    ├──────────────────┐
    ▼                  ▼
┌──────────┐    ┌──────────┐
│ Backend  │    │ Frontend │
│ :8000    │    │ :8501    │
│ FastAPI  │    │Streamlit │
└──────────┘    └──────────┘
```

### Container Architecture

Each service runs in a Docker container with:
- **Read-only filesystem** — prevents unauthorized writes
- **Non-root user** — limits blast radius of security breaches
- **Resource limits** — CPU and memory constraints
- **Health checks** — liveness and readiness probes
- **Structured logging** — JSON output to stdout

### Monitoring

| Endpoint | Purpose | Used By |
|----------|---------|---------|
| `/health` | Liveness check — is the app running? | Docker, K8s, load balancers |
| `/ready` | Readiness check — is the app ready for traffic? | Docker, K8s |
| `/version` | Version info for deployment verification | CI/CD, operators |
| `/metrics` | Request counts, durations, active requests | Monitoring systems |

---

## Security Architecture

### Defense in Depth

| Layer | Protection |
|-------|-----------|
| **Network** | nginx reverse proxy, rate limiting |
| **Transport** | HTTPS (via nginx SSL termination) |
| **Application** | CORS, CSP, HSTS, XSS headers |
| **Input** | Pydantic request validation |
| **Runtime** | Non-root user, read-only filesystem |
| **Secrets** | Environment variables only, never in code |

### Exception Handling

All exceptions produce a consistent JSON envelope:

```json
{
  "detail": "Human-readable error description",
  "request_id": "uuid-for-tracing",
  "error_type": "machine_readable_error_code"
}
```

Domain exceptions map to appropriate HTTP status codes:

| Exception | HTTP Status |
|-----------|-------------|
| `EntityNotFoundError` | 404 Not Found |
| `AmbiguousEntityError` | 409 Conflict |
| `SentimentTimeoutError` | 504 Gateway Timeout |
| `SynthesisTimeoutError` | 504 Gateway Timeout |
| `ValidationError` | 422 Unprocessable Entity |

---

## Configuration Management

Configuration is managed through Pydantic Settings with environment variable loading:

```
.env file
    │
    ▼
Settings class (backend/config.py)
    │
    ├── Field validators (type checking, value constraints)
    ├── Computed properties (is_development, has_openai)
    ├── Validation methods (validate_required_settings)
    └── Cached singleton (get_settings())
```

---

## Scalability Considerations

- **Stateless API** — FastAPI workers are stateless, enabling horizontal scaling
- **Async I/O** — All external API calls use async/await for non-blocking I/O
- **LangGraph Checkpointing** — Enables workflow persistence and recovery
- **Caching** — Market data caching via TTL (configurable)
- **Load Balancing** — nginx distributes traffic across backend workers

---

## Related Documentation

- [API Reference](api.md) — Complete API endpoint documentation
- [Deployment Guide](deployment.md) — Production deployment instructions
- [Testing Guide](testing.md) — How to run and write tests
- [Data Sources](DATA_SOURCES.md) — External data provider details
- [Troubleshooting](troubleshooting.md) — Common issues and solutions