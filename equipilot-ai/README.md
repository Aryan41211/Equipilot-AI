# EquiPilot AI

> **An Agentic Equity Research Assistant**

EquiPilot AI is an informational equity research system that leverages agentic AI workflows to gather, analyze, and synthesize market data, news, and sentiment into comprehensive research reports.

## ⚠️ Important Disclaimer

> **EquiPilot AI is an informational equity research assistant and does not provide investment advice.**

This system does not:
- Execute trades
- Give buy/sell recommendations
- Generate trading signals
- Claim to provide investment advice

All outputs are for informational and educational purposes only.

## Features

- **Multi-Source Data Aggregation**: Combines market data (yfinance), news, and sentiment analysis
- **Agentic Research Workflow**: LangGraph-powered orchestration of research agents
- **Real-Time Market Data**: Fetches current and historical equity data
- **News & Sentiment Analysis**: Processes financial news for market sentiment
- **LLM-Powered Synthesis**: Uses OpenAI to generate coherent research reports
- **Interactive Web UI**: Streamlit-based frontend for query input and report viewing
- **RESTful API**: FastAPI backend for programmatic access
- **Modular Architecture**: Clean separation of concerns for maintainability

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend Framework** | FastAPI |
| **Agent Orchestration** | LangGraph |
| **Frontend** | Streamlit |
| **LLM Provider** | OpenAI (ChatGPT API) |
| **Market Data** | yfinance |
| **Configuration** | python-dotenv, pydantic-settings |
| **Data Processing** | pandas |
| **Validation** | pydantic |

## Folder Structure

```
equipilot-ai/
├── CLAUDE.md                 # Project context for AI assistants
├── README.md                 # This file
├── .env.example              # Environment variable template
├── requirements.txt          # Python dependencies
│
├── backend/                  # FastAPI + LangGraph backend
│   ├── app.py                # FastAPI application entry point
│   ├── config.py             # Configuration management
│   ├── schemas/              # Pydantic models (request/response)
│   ├── services/             # Business logic services
│   ├── agents/               # LangGraph agent definitions
│   ├── tools/                # External tool integrations
│   ├── prompts/              # LLM prompt templates
│   ├── graphs/               # LangGraph workflow definitions
│   └── utils/                # Utility functions
│
├── frontend/                 # Streamlit frontend
│   ├── app.py                # Streamlit application entry point
│   └── components/           # Reusable UI components
│
├── docs/                     # Documentation
│   ├── ARCHITECTURE.md       # System architecture
│   └── DATA_SOURCES.md       # Data source documentation
│
└── tests/                    # Test suite
    ├── unit/                 # Unit tests
    ├── integration/          # Integration tests
    └── fixtures/             # Test fixtures
```

## Getting Started

### Prerequisites

- Python 3.10+
- OpenAI API key

### Installation

```bash
# Clone the repository
cd equipilot-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Running the Application

```bash
# Start backend (FastAPI)
cd backend
uvicorn app:app --reload --port 8000

# Start frontend (Streamlit) - in another terminal
cd frontend
streamlit run app.py
```

### Environment Variables

See `.env.example` for all required variables:

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o
NEWS_API_KEY=your_news_api_key  # Optional
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/research` | Submit research query |
| GET | `/api/v1/research/{id}` | Get research report by ID |
| GET | `/api/v1/health` | Health check |

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format
black backend/ frontend/

# Lint
ruff backend/ frontend/

# Type check
mypy backend/
```

## Architecture Overview

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

### High-Level Flow

```
User Query
    ↓
LangGraph Router
    ↓
Market Data Tool (yfinance)
    ↓
News Tool
    ↓
Sentiment Analysis
    ↓
LLM Synthesis (OpenAI)
    ↓
Research Report
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT License - See LICENSE file for details.

## Support

For questions or issues, please open a GitHub issue.