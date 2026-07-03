# EquiPilot AI — Deployment Guide

## Prerequisites

- Python 3.12+
- Docker (optional, for containerized deployment)
- OpenAI API key
- (Optional) News API key

## Quick Deploy

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install runtime dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start backend
uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload

# Start frontend (separate terminal)
streamlit run frontend/app.py --server.port 8501
```

### Docker Deployment

```bash
# Build and start all services
docker-compose up --build

# Or build individual services
docker build -t equipilot-backend -f Dockerfile .
```

## Production Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ENVIRONMENT` | Yes | Set to `production` |
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `SECRET_KEY` | Yes | Session signing key |
| `BACKEND_RELOAD` | Yes | Must be `false` in production |

### Monitoring

- **Health**: `/health` endpoint (liveness)
- **Readiness**: `/ready` endpoint (readiness probe)
- **Metrics**: `/metrics` endpoint
- **Logging**: Structured JSON logs via stdout

### Security

- CORS configured via `CORS_ORIGINS`
- Rate limiting via slowapi
- Security headers (CSP, HSTS, XSS)
- Request ID tracking for audit trails