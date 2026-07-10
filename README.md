# EquiPilot AI 📈

Agentic equity research — built with **FastAPI**, **LangGraph**, and a **Streamlit** frontend.

> **Informational only.** EquiPilot AI is designed for education and research context. It does **not** execute trades, does **not** provide investment advice, and does **not** generate trading signals.

---

## Project Overview

EquiPilot AI exists to make equity research workflows more **reproducible**, **auditable**, and **easy to review**.

It orchestrates market data retrieval, news summarization, and structured LLM synthesis into consistent, frontend-renderable research reports.

### Key highlights
- Graph-orchestrated research pipeline (**LangGraph**)
- Production-ready API with health/readiness/metrics (**FastAPI**)
- Consistent, UI-friendly report rendering (**Streamlit**)
- Rate limiting, security headers, and structured logging

---

## Features

- Submit a research request using a **ticker/company name** plus a **natural language query**
- Poll for workflow progress and results via **request ID**
- Render structured reports with **executive summary**, section cards, and **citations** (when available)
- Provide backend health & readiness probes for orchestration

---

## Architecture (high level)

```mermaid
flowchart LR
  U[User] --> S[Streamlit Frontend]
  S -->|POST /api/v1/research| A[FastAPI Backend]
  A -->|LangGraph Orchestration| G[Research Workflow Graph]
  G --> M[Market Data Tools]
  G --> N[News Tools]
  G --> L[LLM Synthesis]
  A -->|GET /api/v1/research/{id}| S
  S --> R[Report Rendering]
```

*The diagram is intentionally high-level and omits implementation details.*

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Pydantic |
| Orchestration | LangGraph |
| Frontend | Streamlit |
| AI/ML | OpenAI (GPT-4o / GPT-4o-mini) |
| Deployment | Docker, Nginx |
| Observability | Structured logging + metrics |

---

## Installation

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Only variable names are shown here—configure using your deployment environment.

```env
OPENAI_API_KEY=
NEWS_API_KEY=
SECRET_KEY=

EQUIPILOT_API_URL=
EQUIPILOT_HEALTH_URL=

CORS_ORIGINS=
ENVIRONMENT=
```

---

## API Overview (public endpoints)

- `GET /health`
- `GET /ready`
- `GET /version`
- `GET /metrics`
- `POST /api/v1/research`
- `GET /api/v1/research/{request_id}`
- `GET /api/v1/research/{request_id}/status`

---

## Project Structure

```text
backend/
frontend/
frontend/components/
backend/prompts/
backend/services/
backend/graphs/
backend/tools/

docs/
tests/
```

---

## Deployment

This repository supports production-style deployment via Docker multi-stage builds and Nginx.

---

## Roadmap

- Improve report rendering ergonomics
- Expand tool coverage for additional data sources
- Add more integration tests and e2e coverage

---

## Contributing

Contributions are welcome.

---

## License

MIT

---

## ⚠️ Important Disclaimer

> **EquiPilot AI is an informational equity research assistant. It does NOT provide investment advice.**

This system is designed for **educational and informational purposes only**. It does not:
- Execute trades or place orders
- Give buy/sell/hold recommendations
- Generate trading signals or price predictions
- Claim to provide financial or investment advice

**Always consult a qualified financial advisor before making investment decisions.**

---

## Table of Contents

- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Running Locally](#running-locally)
- [Environment Variables](#environment-variables)
- [API Overview](#api-overview)
- [Streamlit Dashboard](#streamlit-dashboard)
- [Example Workflow](#example-workflow)
- [Testing](#testing)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## Features

### Core Capabilities

| Feature | Description |
|---------|-------------|
| **Multi-Source Data Aggregation** | Combines market data (yfinance), financial news, and sentiment analysis into unified reports |
| **Agentic Research Workflow** | LangGraph-powered orchestration with specialized agents for routing, data collection, analysis, and synthesis |
| **Real-Time Market Data** | Fetches current and historical equity data including prices, volumes, fundamentals, and technical indicators |
| **News & Sentiment Analysis** | Processes financial news articles with LLM-powered sentiment scoring and key theme extraction |
| **LLM-Powered Synthesis** | Uses OpenAI GPT-4o to generate coherent, well-structured research reports with source citations |
| **Interactive Web UI** | Streamlit-based frontend for natural language query input and report visualization |
| **RESTful API** | FastAPI backend with comprehensive endpoints for programmatic access and integration |
| **Production Ready** | Health checks, rate limiting, security headers, structured logging |

### Production Features

- **Health Monitoring**: `/health` (liveness), `/ready` (readiness), `/version`, `/metrics` endpoints
- **Security**: CORS, CSP, HSTS, XSS protection headers; rate limiting via slowapi
- **Observability**: Structured JSON logging with request IDs, metrics collection, exception tracking
- **Configuration**: Pydantic-settings with environment validation, production mode enforcement

---

## Architecture Overview

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Streamlit)                      │
│  Query Input → Progress Tracking → Report Visualization     │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                       │
│  Request Validation → Rate Limiting → Response Formatting   │
│  Security Headers → Request ID → Structured Logging         │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                LangGraph Orchestration                       │
│                                                              │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐ │
│  │ Router   │──▶│  Market  │──▶│  News    │──▶│Sentiment │ │
│  │ Agent    │   │  Data    │   │  Agent   │   │ Agent    │ │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘ │
│       │              │              │              │        │
│       └──────────────┴──────────────┴──────────────┘        │
│                          │                                   │
│                          ▼                                   │
│                   ┌──────────────┐                           │
│                   │  Synthesis   │                           │
│                   │  Agent (LLM) │                           │
│                   └──────────────┘                           │
│                          │                                   │
│                          ▼                                   │
│                   ┌──────────────┐                           │
│                   │  Research    │                           │
│                   │  Report      │                           │
│                   └──────────────┘                           │
└─────────────────────────────────────────────────────────────┘
    │
    └──────────────────┬──────────────────┬──────────────────┐
                       ▼                  ▼                  ▼
              ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
              │  yfinance    │   │  News API    │   │  OpenAI API  │
              │  Market Data │   │  News Data   │   │  LLM         │
              └──────────────┘   └──────────────┘   └──────────────┘
```

For detailed architecture documentation, see [docs/architecture.md](docs/architecture.md).

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend Framework** | [FastAPI](https://fastapi.tiangolo.com) | High-performance async API server |
| **Agent Orchestration** | [LangGraph](https://langchain-ai.github.io/langgraph/) | Stateful agent workflow management |
| **Frontend** | [Streamlit](https://streamlit.io) | Interactive data application UI |
| **LLM Provider** | [OpenAI](https://openai.com) | GPT-4o / GPT-4o-mini for analysis and synthesis |
| **Market Data** | [yfinance](https://pypi.org/project/yfinance/) | Yahoo Finance data access |
| **Configuration** | [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) | Type-safe environment configuration |
| **Data Processing** | [pandas](https://pandas.pydata.org) | Data manipulation and analysis |
| **Validation** | [pydantic](https://docs.pydantic.dev) | Request/response schema validation |
| **Rate Limiting** | [slowapi](https://github.com/laurentS/slowapi) | API rate limiting |
| **Logging** | [structlog](https://www.structlog.org) | Structured JSON logging |

---

## Project Structure

```
equipilot-ai/
│
├── README.md                    # Project documentation
├── CLAUDE.md                    # AI assistant context
├── .env.example                 # Environment variable template
├── requirements.txt             # Python dependencies
├── backend/                     # FastAPI + LangGraph backend
│   ├── app.py                   # Application factory, routes, middleware
│   ├── config.py                # Pydantic settings management
│   ├── schemas/                 # Request/response Pydantic models
│   │   ├── research.py
│   │   ├── market_data.py
│   │   ├── news.py
│   │   ├── sentiment.py
│   │   └── report.py
│   ├── services/                # Business logic and external integrations
│   │   ├── market_service.py
│   │   ├── news_service.py
│   │   ├── sentiment_service.py
│   │   └── llm_service.py
│   ├── agents/                  # LangGraph agent definitions
│   │   ├── router_agent.py
│   │   ├── market_agent.py
│   │   ├── news_agent.py
│   │   ├── sentiment_agent.py
│   │   └── synthesis_agent.py
│   ├── tools/                   # LangGraph function tools
│   │   ├── market_data_tool.py
│   │   ├── news_tool.py
│   │   └── sentiment_tool.py
│   ├── prompts/                 # LLM prompt templates
│   │   ├── router_prompts.py
│   │   ├── synthesis_prompts.py
│   │   └── sentiment_prompts.py
│   ├── graphs/                  # LangGraph workflow definitions
│   │   ├── graph.py
│   │   └── state.py
│   ├── middleware/              # Production middleware
│   │   ├── __init__.py
│   │   └── production.py        # Security, metrics, rate limiting
│   ├── exceptions/              # Domain exception hierarchy
│   │   ├── __init__.py
│   │   ├── handlers.py          # Centralized exception handlers
│   │   ├── entity_resolution_exceptions.py
│   │   ├── sentiment_exceptions.py
│   │   └── synthesis_exceptions.py
│   └── utils/                   # Utilities
│       ├── logger.py            # Structured logging setup
│       ├── helpers.py
│       ├── validators.py
│       └── formatters.py
│
├── frontend/                    # Streamlit frontend
│   ├── app.py                   # Main application entry point
│   └── components/              # Reusable UI components
│       ├── query_form.py
│       ├── report_display.py
│       ├── progress_tracker.py
│       └── sidebar.py
│
├── docs/                        # Documentation
│   ├── architecture.md          # System architecture
│   ├── api.md                   # API reference
│   ├── deployment.md            # Deployment guide
│   ├── testing.md               # Testing guide
│   ├── troubleshooting.md       # Common issues
│   └── DATA_SOURCES.md          # Data source details
│
└── tests/                       # Test suite
    ├── test_production.py       # Production readiness tests
    ├── test_dynamic_routing.py
    ├── test_e2e_integration.py
    ├── test_entity_resolution_service.py
    ├── test_entity_resolution_tool.py
    ├── test_frontend_components.py
    ├── test_langgraph_market_news_integration.py
    ├── test_market_data_service.py
    ├── test_market_data_tool.py
    ├── test_sentiment_service.py
    ├── test_sentiment_tool.py
    └── test_synthesis_agent.py
```

---

## Quick Start

### Prerequisites

- Python 3.12+
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))
- (Optional) News API key for news features

### Installation

```bash
# Clone the repository
git clone https://github.com/Aryan41211/equipilot-ai.git
cd equipilot-ai

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys (see Environment Variables section)
```

## Running Locally

### Start the Backend

```bash
# From project root
uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

### Start the Frontend

In a separate terminal:

```bash
# From project root
streamlit run frontend/app.py --server.port 8501 --server.headless true
```

The dashboard will be available at `http://localhost:8501`.

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | **Yes** | — | OpenAI API key for LLM access |
| `OPENAI_MODEL` | No | `gpt-4o` | Primary model for report synthesis |
| `OPENAI_MODEL_MINI` | No | `gpt-4o-mini` | Cost-effective model for classification |
| `NEWS_API_KEY` | No | — | News API key (NewsAPI, Alpha Vantage, Finnhub) |
| `NEWS_API_PROVIDER` | No | `newsapi` | News provider selection |
| `ENVIRONMENT` | No | `development` | `development`, `staging`, or `production` |
| `BACKEND_HOST` | No | `0.0.0.0` | Backend server bind address |
| `BACKEND_PORT` | No | `8000` | Backend server port |
| `BACKEND_RELOAD` | No | `true` | Enable auto-reload (disable in production) |
| `BACKEND_WORKERS` | No | `2` | Number of uvicorn workers (1-8) |
| `LOG_LEVEL` | No | `INFO` | Logging level: DEBUG, INFO, WARNING, ERROR |
| `LOG_FORMAT` | No | `json` | Log format: `json` (production) or `text` (dev) |
| `SECRET_KEY` | In production | — | Secret key for session signing |
| `CORS_ORIGINS` | No | `["http://localhost:8501"]` | Allowed CORS origins |
| `REQUEST_RATE_LIMIT` | No | `100` | Requests per minute limit |

See [.env.example](.env.example) for a complete template.

---

## API Overview

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Liveness check — returns service status |
| `GET` | `/ready` | Readiness check — returns 503 if not ready |
| `GET` | `/version` | Application version information |
| `GET` | `/metrics` | Request metrics and performance data |
| `POST` | `/api/v1/research` | Submit a new equity research query |
| `GET` | `/api/v1/research/{id}` | Retrieve research results by ID |
| `GET` | `/api/v1/research/{id}/status` | Check research request status |

### Example: Submit Research Query

```bash
curl -X POST "http://localhost:8000/api/v1/research" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze Apple Inc. recent performance and outlook",
    "tickers": ["AAPL"],
    "options": {
      "include_news": true,
      "include_sentiment": true,
      "lookback_days": 30
    }
  }'
```

### Example: Check Health

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "services": {
    "openai": true,
    "news_api": false
  },
  "errors": []
}
```

For complete API documentation, see [docs/api.md](docs/api.md).

---

## Streamlit Dashboard

The Streamlit frontend provides an interactive interface for:

1. **Query Input**: Natural language research queries with optional ticker specification
2. **Progress Tracking**: Real-time visibility into the research workflow stages
3. **Report Visualization**: Formatted research reports with sections, citations, and data tables
4. **History**: Access to previously submitted research requests

Access the dashboard at `http://localhost:8501` after starting the frontend.

---

## Example Workflow

### 1. Submit a Research Query

```
Query: "What is the current market sentiment and financial health of Microsoft?"
Tickers: MSFT
```

### 2. Agent Workflow Execution

The LangGraph orchestrator executes the following steps:

1. **Router Agent**: Classifies query intent, extracts ticker `MSFT`, determines required data sources
2. **Market Data Agent**: Fetches MSFT price data, fundamentals (P/E, EPS, market cap), 52-week range
3. **News Agent**: Retrieves recent MSFT news articles from configured news provider
4. **Sentiment Agent**: Analyzes news articles for bullish/bearish sentiment, key themes, risk factors
5. **Synthesis Agent**: Combines all data into a structured research report using GPT-4o

### 3. Research Report Output

The generated report includes:
- **Executive Summary**: Key findings and overview
- **Market Data Analysis**: Price trends, valuation metrics, technical indicators
- **News Summary**: Recent developments and market reactions
- **Sentiment Analysis**: Bullish/bearish breakdown, key themes, sentiment score
- **Risk Factors**: Identified risks and uncertainties
- **Sources**: Citations for all data points

---

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=term-missing

# Run specific test file
pytest tests/test_production.py -v

# Run by category
pytest -k "health" tests/
```

For detailed testing documentation, see [docs/testing.md](docs/testing.md).

---

## Roadmap

### Short Term
- [ ] WebSocket support for real-time research progress updates
- [ ] Redis caching layer for market data and API responses
- [ ] Database persistence for research history and user sessions
- [ ] Authentication and authorization system

### Medium Term
- [ ] Multi-model LLM support (Anthropic Claude, Google Gemini)
- [ ] Custom agent plugins and tool registry
- [ ] PDF report export functionality
- [ ] Email report delivery

### Long Term
- [ ] Portfolio tracking and watchlist management
- [ ] Comparative analysis across multiple equities
- [ ] Backtesting framework for research strategies
- [ ] Community-contributed agent marketplace

---

## Contributing

Contributions are welcome! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Guidelines

- Follow existing code patterns and architecture
- Add tests for new functionality
- Update documentation for API changes
- Run linting before submitting: `ruff check . && black .`
- Ensure all tests pass: `pytest`

---

## License

Distributed under the MIT License. See `LICENSE` for more information.

---

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com), [LangGraph](https://langchain-ai.github.io/langgraph/), and [Streamlit](https://streamlit.io)
- Market data provided by [yfinance](https://pypi.org/project/yfinance/)
- LLM capabilities powered by [OpenAI](https://openai.com)

---

<p align="center">
  <sub>EquiPilot AI — Informational equity research. Not investment advice.</sub>
</p>