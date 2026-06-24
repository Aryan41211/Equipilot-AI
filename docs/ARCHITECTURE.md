# EquiPilot AI - System Architecture

## Overview

EquiPilot AI follows a modular, agent-based architecture using LangGraph for workflow orchestration. The system separates concerns into distinct layers: API, orchestration, agents, tools, and data processing.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                           │
│  ┌─────────────────┐         ┌─────────────────────────────┐   │
│  │   Streamlit     │         │      REST API (FastAPI)     │   │
│  │   Frontend      │◄────────┤   /api/v1/research          │   │
│  └─────────────────┘         └─────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Layer (FastAPI)                        │
│  • Request validation (Pydantic)                                │
│  • Authentication/Authorization                                 │
│  • Rate limiting                                                │
│  • Response formatting                                          │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                   LangGraph Orchestration                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  Research Graph                          │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │    │
│  │  │ Router   │─►│  Market  │─►│  News    │─►│Sentiment│  │    │
│  │  │ Agent    │  │  Data    │  │  Agent   │  │ Agent  │  │    │
│  │  └──────────┘  │  Agent   │  └──────────┘  └────────┘  │    │
│  │                 └──────────┘              │             │    │
│  │                      │                    ▼             │    │
│  │                 ┌──────────┐  ┌──────────────────┐     │    │
│  │                 │Synthesis │◄─│  LLM Synthesis   │     │    │
│  │                 │  Agent   │  │  (OpenAI)        │     │    │
│  │                 └──────────┘  └──────────────────┘     │    │
│  │                      │                                 │    │
│  │                      ▼                                 │    │
│  │                 ┌──────────┐                           │    │
│  │                 │  Output  │                           │    │
│  │                 │ Formatter│                           │    │
│  │                 └──────────┘                           │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│   yfinance       │ │   News API       │ │   OpenAI API     │
│   (Market Data)  │ │   (News Data)    │ │   (LLM)          │
└──────────────────┘ └──────────────────┘ └──────────────────┘
```

## Data Flow

### 1. User Query Input
- User submits research query via Streamlit UI or REST API
- Query validated against `ResearchRequest` schema
- Request ID generated for tracking

### 2. LangGraph Router Agent
- Entry point of the research workflow
- Analyzes query intent and determines required tools
- Routes to appropriate agents based on query type
- Maintains conversation state

### 3. Market Data Agent (yfinance)
- Fetches real-time and historical market data
- Retrieves: price, volume, fundamentals, technical indicators
- Returns structured `MarketData` schema

### 4. News Agent
- Queries news API for relevant financial news
- Filters by ticker, date range, relevance
- Returns structured `NewsArticle` schema list

### 5. Sentiment Analysis Agent
- Processes news articles for sentiment scoring
- Uses LLM or specialized sentiment model
- Returns `SentimentAnalysis` with scores and key themes

### 6. LLM Synthesis Agent
- Receives all collected data (market, news, sentiment)
- Uses structured prompts to generate research report
- Outputs structured `ResearchReport` schema

### 7. Output Formatter
- Formats report for API response
- Formats report for Streamlit display
- Handles citations and source attribution

## Component Details

### Backend Modules

#### `backend/app.py`
- FastAPI application factory
- Route registration
- Middleware configuration
- Exception handlers

#### `backend/config.py`
- Pydantic Settings for configuration
- Environment variable loading
- API keys, model settings, timeouts

#### `backend/schemas/`
- `research.py` - Request/response models
- `market_data.py` - Market data models
- `news.py` - News article models
- `sentiment.py` - Sentiment analysis models
- `report.py` - Research report models

#### `backend/services/`
- `market_service.py` - yfinance wrapper
- `news_service.py` - News API wrapper
- `llm_service.py` - OpenAI client wrapper
- `sentiment_service.py` - Sentiment analysis logic

#### `backend/agents/`
- `router_agent.py` - Query routing logic
- `market_agent.py` - Market data retrieval
- `news_agent.py` - News retrieval
- `sentiment_agent.py` - Sentiment analysis
- `synthesis_agent.py` - Report generation

#### `backend/tools/`
- `yfinance_tool.py` - yfinance function tools
- `news_tool.py` - News API function tools
- `sentiment_tool.py` - Sentiment analysis tools

#### `backend/prompts/`
- `router_prompts.py` - Router system prompts
- `synthesis_prompts.py` - Report generation prompts
- `sentiment_prompts.py` - Sentiment analysis prompts

#### `backend/graphs/`
- `research_graph.py` - Main LangGraph workflow
- `state.py` - Graph state definition

#### `backend/utils/`
- `helpers.py` - Common utilities
- `validators.py` - Input validation
- `formatters.py` - Output formatting

### Frontend Modules

#### `frontend/app.py`
- Streamlit page configuration
- Main application layout
- Session state management

#### `frontend/components/`
- `query_form.py` - Research query input
- `report_display.py` - Report rendering
- `progress_tracker.py` - Workflow progress UI
- `sidebar.py` - Navigation and settings

## State Management

### LangGraph State Schema
```python
class ResearchState(TypedDict):
    query: str
    tickers: List[str]
    market_data: Optional[MarketData]
    news_articles: List[NewsArticle]
    sentiment: Optional[SentimentAnalysis]
    report: Optional[ResearchReport]
    errors: List[str]
    current_step: str
```

## Error Handling

- Each agent handles its own errors gracefully
- Errors collected in state for debugging
- Partial results returned on failure
- Structured error responses via API

## Security Considerations

- API keys stored in environment variables only
- No secrets in code or logs
- Rate limiting on API endpoints
- Input validation on all endpoints
- CORS configured for frontend origin

## Scalability Considerations

- Stateless FastAPI workers
- LangGraph checkpointing for long workflows
- Async I/O for external API calls
- Caching layer for market data (future)
- Horizontal scaling via load balancer

## Future Extensions

- WebSocket support for real-time updates
- Caching layer (Redis) for market data
- Database persistence for research history
- Authentication/authorization
- Multi-model LLM support
- Custom agent plugins