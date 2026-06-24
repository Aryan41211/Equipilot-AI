# EquiPilot AI - Data Sources Documentation

## Overview

This document describes all external data sources used by EquiPilot AI, their purpose in the system, integration patterns, and limitations.

---

## 1. yfinance (Yahoo Finance)

### Purpose
Primary source for **market data** including real-time and historical equity prices, volumes, fundamentals, and technical indicators.

### Data Provided
| Category | Fields |
|----------|--------|
| **Price Data** | Open, High, Low, Close, Adjusted Close, Volume |
| **Fundamentals** | Market Cap, P/E Ratio, EPS, Dividend Yield, Beta, 52-week High/Low |
| **Financials** | Income Statement, Balance Sheet, Cash Flow (quarterly/annual) |
| **Technical** | Moving Averages, RSI, MACD (computed from price data) |
| **Metadata** | Company name, sector, industry, currency, exchange |

### Integration
```python
# Backend service wrapper (backend/services/market_service.py)
import yfinance as yf

ticker = yf.Ticker("AAPL")
data = ticker.history(period="1y")
info = ticker.info
financials = ticker.financials
```

### Rate Limits
- **Unofficial API**: No official rate limits published
- **Best Practice**: Cache responses, batch requests, implement exponential backoff
- **Recommended**: Max 100 requests/minute per IP

### Limitations
- No official SLA or support
- Data may be delayed (15-20 minutes for real-time)
- Fundamental data updates quarterly
- No options/futures data
- Subject to Yahoo Finance Terms of Service

### Error Handling
- Network timeouts → retry with backoff
- Invalid ticker → return structured error
- Missing data fields → return None with logging

---

## 2. News API (Placeholder)

### Purpose
Source for **financial news articles** relevant to queried tickers and market topics.

### Data Provided
| Field | Description |
|-------|-------------|
| `title` | Article headline |
| `description` | Article summary/snippet |
| `content` | Full article text (when available) |
| `url` | Source URL |
| `source` | Publisher name |
| `published_at` | Publication timestamp |
| `author` | Article author |
| `category` | News category (business, markets, etc.) |

### Integration Pattern
```python
# Backend service wrapper (backend/services/news_service.py)
# TODO: Implement with actual news provider (e.g., NewsAPI, Alpha Vantage, Finnhub)

class NewsService:
    async def fetch_news(
        self,
        tickers: List[str],
        date_from: datetime,
        date_to: datetime,
        limit: int = 20
    ) -> List[NewsArticle]:
        # Implementation depends on chosen provider
        pass
```

### Potential Providers
| Provider | Free Tier | Paid Features |
|----------|-----------|---------------|
| **NewsAPI.org** | 100 req/day | Historical, more sources |
| **Alpha Vantage** | 25 req/day | Premium endpoints |
| **Finnhub** | 60 req/min | WebSocket, more data |
| **Polygon.io** | Limited | Real-time, archives |
| **Benzinga** | Trial | Professional grade |

### Rate Limits (Provider Dependent)
- Typical free tiers: 100-500 requests/day
- Paid tiers: 1000+ requests/minute
- Implement caching and request deduplication

### Limitations
- Free tiers insufficient for production
- Article full text often behind paywalls
- Relevance filtering required
- Duplicate articles across sources
- Language/region coverage varies

---

## 3. OpenAI API (ChatGPT)

### Purpose
**LLM synthesis engine** for:
- Query understanding and routing
- Sentiment analysis of news articles
- Research report generation
- Summarization and insight extraction

### Models Used
| Task | Recommended Model | Reason |
|------|-------------------|--------|
| Router/Classification | `gpt-4o-mini` | Fast, cost-effective |
| Sentiment Analysis | `gpt-4o-mini` | Structured output |
| Report Synthesis | `gpt-4o` | High-quality reasoning |
| Summarization | `gpt-4o-4o-mini` | Cost-effective |

### Integration
```python
# Backend service wrapper (backend/services/llm_service.py)
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def generate_report(prompt: str, model: str = "gpt-4o") -> str:
    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        response_format={"type": "json_object"}
    )
    return response.choices[0].message.content
```

### Rate Limits (Tier Dependent)
| Tier | RPM (Requests/min) | TPM (Tokens/min) |
|------|-------------------|------------------|
| Free | 3 | 40,000 |
| Tier 1 | 500 | 200,000 |
| Tier 2 | 5,000 | 1,000,000 |
| Tier 3 | 10,000 | 4,000,000 |

### Cost Management
- Use `gpt-4o-mini` for classification/sentiment
- Cache repeated queries
- Implement token counting for budget tracking
- Set max_tokens per request

### Limitations
- Hallucination risk - always cite sources
- Context window limits (128k for gpt-4o)
- Latency (2-10 seconds per request)
- Cost scales with usage
- No real-time data access

### Prompt Engineering Guidelines
- Use structured output (JSON schema)
- Include few-shot examples
- Explicitly request citations
- Set temperature low (0.1-0.3) for factual tasks
- Use system prompts for role definition

---

## Data Flow Summary

```
User Query
    │
    ▼
┌────────────────────────────────────────┐
│         Router Agent (OpenAI)          │
│  • Classifies query intent             │
│  • Extracts tickers                    │
│  • Determines required data sources    │
└────────────────────────────────────────┘
    │
    ├──────────────────┬──────────────────┐
    ▼                  ▼                  ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  yfinance    │ │   News API   │ │  OpenAI      │
│  (Market)    │ │  (News)      │ │  (Sentiment) │
└──────────────┘ └──────────────┘ └──────────────┘
    │                  │                  │
    └──────────────────┼──────────────────┘
                       ▼
            ┌────────────────────┐
            │  Synthesis Agent   │
            │     (OpenAI)       │
            └────────────────────┘
                       │
                       ▼
            ┌────────────────────┐
            │  Research Report   │
            └────────────────────┘
```

---

## Configuration

All data source credentials configured via environment variables:

```env
# .env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
OPENAI_MODEL_MINI=gpt-4o-mini

NEWS_API_KEY=your_news_api_key
NEWS_API_PROVIDER=newsapi  # or alphavantage, finnhub, etc.

YFINANCE_CACHE_TTL=300  # seconds
```

---

## Data Quality & Validation

### Market Data Validation
- Price sanity checks (no negative prices, reasonable ranges)
- Volume validation (non-negative)
- Timestamp continuity checks
- Cross-reference with multiple periods

### News Validation
- Deduplication by title + source
- Relevance scoring against query tickers
- Date range filtering
- Source credibility weighting

### LLM Output Validation
- JSON schema validation for structured outputs
- Citation verification against source documents
- Confidence scoring for key claims
- Fallback to template on parsing failure

---

## Compliance & Legal

### yfinance
- Educational/research use only
- No redistribution of raw data
- Attribution required
- Check Yahoo Finance Terms of Service

### News APIs
- Respect individual provider ToS
- No full-text redistribution without license
- Attribution typically required
- Commercial use may require paid tier

### OpenAI
- Data not used for training (API default)
- No PII in prompts
- Follow OpenAI Usage Policies
- Consider data residency requirements

---

## Monitoring & Observability

### Metrics to Track
- API latency per data source
- Error rates by source
- Token usage and costs (OpenAI)
- Cache hit rates
- Data freshness (age of latest data)

### Alerting
- API key expiration/rotation
- Rate limit approaching
- Data quality degradation
- Cost threshold exceeded