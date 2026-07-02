# EquiPilot AI — API Reference

## Overview

EquiPilot AI exposes a RESTful API via FastAPI. The API is organized into two categories:

1. **Health & Monitoring** — Endpoints for liveness, readiness, version, and metrics
2. **Research** — Endpoints for submitting and retrieving equity research

**Base URL**: `http://localhost:8000` (or your deployed host)
**API Prefix**: `/api/v1`
**OpenAPI Docs**: `http://localhost:8000/docs`
**ReDoc**: `http://localhost:8000/redoc`

---

## Authentication

EquiPilot AI does not currently require authentication. API keys for external services (OpenAI, News API) are configured server-side via environment variables.

---

## Common Response Format

### Success Response

```json
{
  "field_1": "value",
  "field_2": "value"
}
```

### Error Response

```json
{
  "detail": "Error description",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "error_type": "error_category"
}
```

Every error response includes:
- `detail` — Human-readable error description
- `request_id` — Unique identifier for request tracing
- `error_type` — Machine-readable error category for programmatic handling

---

## Health & Monitoring Endpoints

### GET /health

Liveness check endpoint. Returns the current health status of the application.

**Purpose**: Used by Railway, load balancers, and monitoring systems to determine if the application is running.

**Rate Limiting**: Exempt from general rate limits (separate health check limit).

**Response**:

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `"healthy"` or `"degraded"` |
| `version` | string | Application version |
| `services` | object | Service configuration status |
| `services.openai` | boolean | Whether OpenAI API key is configured |
| `services.news_api` | boolean | Whether News API key is configured |
| `errors` | array | Startup errors (empty when healthy) |

**Example Request**:
```bash
curl http://localhost:8000/health
```

**Example Response (Healthy)**:
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

**Example Response (Degraded)**:
```json
{
  "status": "degraded",
  "version": "0.1.0",
  "services": {
    "openai": false,
    "news_api": false
  },
  "errors": [
    "OPENAI_API_KEY is not set - LLM features unavailable"
  ]
}
```

**Status Codes**:
- `200 OK` — Always returns 200 (use `/ready` for readiness)

---

### GET /ready

Readiness check endpoint. Indicates whether the application is ready to serve traffic.

**Purpose**: Used for readiness probes by monitoring and CI/CD systems. Returns 503 when startup errors exist (e.g., missing API keys, graph initialization failure).

**Rate Limiting**: Exempt from general rate limits.

**Response**:

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `"ready"` or `"not_ready"` |
| `version` | string | Application version |
| `errors` | array | Startup errors (only present when not ready) |

**Example Request**:
```bash
curl http://localhost:8000/ready
```

**Example Response (Ready)**:
```json
{
  "status": "ready",
  "version": "0.1.0"
}
```

**Example Response (Not Ready)**:
```json
{
  "status": "not_ready",
  "errors": [
    "Failed to initialize research graph"
  ]
}
```

**Status Codes**:
- `200 OK` — Application is ready
- `503 Service Unavailable` — Application is not ready

---

### GET /version

Returns application version information.

**Purpose**: Used for deployment verification and CI/CD pipeline validation.

**Response**:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Application name |
| `version` | string | Semantic version number |
| `api_version` | string | API route prefix |

**Example Request**:
```bash
curl http://localhost:8000/version
```

**Example Response**:
```json
{
  "name": "EquiPilot AI",
  "version": "0.1.0",
  "api_version": "/api/v1"
}
```

**Status Codes**:
- `200 OK` — Success

---

### GET /metrics

Returns request metrics for monitoring systems.

**Purpose**: Provides visibility into API performance and usage patterns.

**Response**:

| Field | Type | Description |
|-------|------|-------------|
| `requests_total` | object | Request count by endpoint path |
| `requests_by_status` | object | Request count by HTTP status code |
| `average_response_time_ms` | number | Average response time in milliseconds |
| `active_requests` | integer | Currently active request count |

**Example Request**:
```bash
curl http://localhost:8000/metrics
```

**Example Response**:
```json
{
  "requests_total": {
    "/health": 42,
    "/version": 10,
    "/api/v1/research": 5
  },
  "requests_by_status": {
    "200": 55,
    "404": 2
  },
  "average_response_time_ms": 12.34,
  "active_requests": 0
}
```

**Status Codes**:
- `200 OK` — Success

**Note**: Metrics are stored in-memory and reset on application restart. For production, integrate with Prometheus or a similar monitoring system.

---

## Research Endpoints

All research endpoints are prefixed with `/api/v1`.

### POST /api/v1/research

Submit a new equity research query for processing.

**Purpose**: Initiates the agentic research workflow. The request is validated and queued for processing.

**Rate Limiting**: Subject to API rate limits (configurable via `REQUEST_RATE_LIMIT`).

**Request Body**:

```json
{
  "query": "string (required) — Natural language research query",
  "tickers": ["string"] (optional) — Stock ticker symbols",
  "options": {
    "include_news": "boolean (optional, default: true)",
    "include_sentiment": "boolean (optional, default: true)",
    "lookback_days": "integer (optional, default: 30)"
  }
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `query` | string | **Yes** | — | Natural language research question |
| `tickers` | array[string] | No | `[]` | Stock ticker symbols (e.g., `["AAPL", "MSFT"]`) |
| `options.include_news` | boolean | No | `true` | Whether to fetch news articles |
| `options.include_sentiment` | boolean | No | `true` | Whether to perform sentiment analysis |
| `options.lookback_days` | integer | No | `30` | Days to look back for news and data |

**Example Request**:
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

**Example Response (202 Accepted)**:
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "query": "Analyze Apple Inc. recent performance and outlook",
  "tickers": ["AAPL"],
  "message": "Research request accepted. Processing started."
}
```

**Status Codes**:
- `202 Accepted` — Request accepted and queued for processing
- `422 Unprocessable Entity` — Request validation failed (missing/invalid fields)

---

### GET /api/v1/research/{request_id}

Retrieve the results of a previously submitted research request.

**Purpose**: Poll for completed research results using the request ID from the submission response.

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `request_id` | string | UUID of the research request |

**Response**:

| Field | Type | Description |
|-------|------|-------------|
| `request_id` | string | Unique request identifier |
| `status` | string | Current status: `pending`, `processing`, `completed`, `failed`, `not_found` |
| `query` | string | Original research query |
| `tickers` | array[string] | Requested ticker symbols |
| `report` | object | Research report (present when status is `completed`) |
| `message` | string | Status message |

**Example Request**:
```bash
curl http://localhost:8000/api/v1/research/550e8400-e29b-41d4-a716-446655440000
```

**Example Response (Pending)**:
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "query": "Analyze Apple Inc.",
  "tickers": ["AAPL"],
  "message": "Research request is queued for processing."
}
```

**Example Response (Not Found)**:
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "not_found",
  "query": "",
  "tickers": [],
  "message": "Research request not found."
}
```

**Status Codes**:
- `200 OK` — Request found and returned (check `status` field for completion)
- `404 Not Found` — Request ID does not exist

---

### GET /api/v1/research/{request_id}/status

Check the current processing status of a research request.

**Purpose**: Lightweight status check without retrieving the full report.

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `request_id` | string | UUID of the research request |

**Response**: Returns a string value representing the current status.

| Value | Description |
|-------|-------------|
| `"pending"` | Queued and waiting for processing |
| `"processing"` | Research workflow is actively running |
| `"completed"` | Research is complete and results are available |
| `"failed"` | Processing encountered an error |
| `"not_found"` | Request ID does not exist |

**Example Request**:
```bash
curl http://localhost:8000/api/v1/research/550e8400-e29b-41d4-a716-446655440000/status
```

**Example Response**:
```
"pending"
```

**Status Codes**:
- `200 OK` — Status retrieved successfully

---

## Schema Reference

### ResearchRequest

```json
{
  "query": "string",
  "tickers": ["string"],
  "options": {
    "include_news": true,
    "include_sentiment": true,
    "lookback_days": 30
  }
}
```

### ResearchResponse

```json
{
  "request_id": "uuid-string",
  "status": "pending | processing | completed | failed | not_found",
  "query": "string",
  "tickers": ["string"],
  "message": "string"
}
```

### ResearchStatus

String enum: `"pending" | "processing" | "completed" | "failed" | "not_found"`

---

## Error Codes

| Error Type | HTTP Status | Description |
|------------|-------------|-------------|
| `internal_error` | 500 | Unexpected server error |
| `http_error` | 4xx/5xx | Standard HTTP errors |
| `validation_error` | 422 | Request validation failed |
| `entity_not_found` | 404 | Requested entity not found |
| `ambiguous_entity` | 409 | Multiple entities matched |
| `entity_validation_error` | 422 | Entity validation failed |
| `sentiment_timeout` | 504 | Sentiment analysis timed out |
| `sentiment_validation_error` | 422 | Sentiment data validation failed |
| `synthesis_timeout` | 504 | Report generation timed out |
| `synthesis_validation_error` | 422 | Report data validation failed |
| `rate_limit_exceeded` | 429 | Too many requests |

---

## Rate Limiting

Rate limiting is applied at the application level:

### Application Level (SlowAPI)

Requests per minute limit is configurable via the `REQUEST_RATE_LIMIT` environment variable (default: 100).

---

## CORS Configuration

CORS origins are configured via the `CORS_ORIGINS` environment variable:

```env
CORS_ORIGINS=["http://localhost:8501","http://localhost:3000","https://yourdomain.com"]
```

Default value: `["http://localhost:8501", "http://localhost:3000"]`

---

## OpenAPI Specification

An interactive OpenAPI specification is available at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **Raw JSON**: `http://localhost:8000/openapi.json`

These provide a complete, machine-readable specification of all endpoints, schemas, and request/response formats.