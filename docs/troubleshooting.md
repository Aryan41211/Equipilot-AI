# EquiPilot AI — Troubleshooting Guide

## Overview

This guide covers common issues encountered during development, deployment, and operation of EquiPilot AI. Each issue includes the likely cause and recommended solution.

---

## Installation Issues

### Python Version Mismatch

**Error**:
```
RuntimeError: Python 3.12 or higher is required
```

**Cause**: The project requires Python 3.12+ for features like `asynccontextmanager` and modern type hints.

**Solution**:
```bash
# Check your Python version
python --version

# Install Python 3.12+ from python.org or use pyenv
pyenv install 3.12.10
pyenv local 3.12.10
```

### Dependency Installation Failures

**Error**:
```
ERROR: Could not find a version that satisfies the requirement fastapi==0.115.0
```

**Cause**: Outdated pip or incompatible Python version.

**Solution**:
```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install with relaxed version constraints
pip install -r requirements.txt --no-deps
pip install -r requirements.txt
```

### Virtual Environment Issues

**Error**:
```
ModuleNotFoundError: No module named 'fastapi'
```

**Cause**: Dependencies installed outside the active virtual environment.

**Solution**:
```bash
# Verify virtual environment is activated
which python  # Should point to your venv

# On Windows
where python  # Should show venv\Scripts\python.exe

# Reinstall if needed
pip install -r requirements.txt
```

---

## Configuration Issues

### Missing API Keys

**Error** (at startup):
```
Configuration warning: OPENAI_API_KEY not set - LLM features will not work
```

**Cause**: `OPENAI_API_KEY` environment variable is not set.

**Solution**:
```bash
# Copy and edit the environment file
cp .env.example .env

# Set your OpenAI API key in .env
OPENAI_API_KEY=sk-your-key-here
```

### Invalid Environment Variable

**Error**:
```
pydantic_core.ValidationError: 1 validation error for Settings
log_level
  Value error, log_level must be one of {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
```

**Cause**: An environment variable has an invalid value.

**Solution**: Check `.env` for typos. Valid values:
- `LOG_LEVEL`: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- `LOG_FORMAT`: `json` or `text`
- `ENVIRONMENT`: `development`, `staging`, or `production`
- `NEWS_API_PROVIDER`: `newsapi`, `alphavantage`, or `finnhub`

### Production Validation Errors

**Error** (in production mode):
```
OPENAI_API_KEY is required in production
SECRET_KEY is required in production
BACKEND_RELOAD must be false in production
```

**Cause**: Required production settings are missing or misconfigured.

**Solution**:
```env
ENVIRONMENT=production
OPENAI_API_KEY=sk-your-key
SECRET_KEY=your-random-secret-key
BACKEND_RELOAD=false
```

---

## Runtime Issues

### Application Won't Start

**Error**:
```
Error: Failed to initialize research graph
```

**Cause**: LangGraph graph initialization failed, possibly due to missing dependencies or configuration.

**Solution**:
```bash
# Check the full error in logs
uvicorn backend.app:app --host 0.0.0.0 --port 8000 --log-level debug

# Verify all dependencies are installed
pip list | grep langgraph
pip list | grep langchain
```

### Port Already in Use

**Error**:
```
ERROR: [Errno 10048] error while attempting to bind on address ('0.0.0.0', 8000): address already in use
```

**Cause**: Another process is using the required port.

**Solution**:
```bash
# Find the process using the port
# On Linux/macOS
lsof -i :8000
kill -9 <PID>

# On Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or use a different port
BACKEND_PORT=8001 uvicorn backend.app:app --host 0.0.0.0 --port 8001
```

### Rate Limiting Errors

**Error**:
```
429 Too Many Requests
{
  "detail": "Rate limit exceeded",
  "request_id": "...",
  "error_type": "rate_limit_exceeded"
}
```

**Cause**: Too many requests sent within the rate limit window.

**Solution**:
```bash
# Increase rate limit in .env
REQUEST_RATE_LIMIT=200

# Or check nginx rate limits in nginx.conf
# Increase burst or rate values
```

### Request Timeout

**Error**:
```
504 Gateway Timeout
{
  "detail": "Sentiment analysis timed out",
  "request_id": "...",
  "error_type": "sentiment_timeout"
}
```

**Cause**: External API (OpenAI, News API) took too long to respond.

**Solution**:
```bash
# Increase timeouts in .env
LLM_API_TIMEOUT=120
NEWS_API_TIMEOUT=60
MARKET_DATA_TIMEOUT=60
```

---

## Docker Issues

### Docker Build Fails

**Error**:
```
ERROR: failed to solve: process "/bin/sh -c pip install ..." did not complete successfully
```

**Cause**: Network issues during dependency installation or incompatible package versions.

**Solution**:
```bash
# Retry with no cache
docker build --no-cache --target production -t equipilot-ai:latest .

# Check Docker network connectivity
docker run --rm python:3.12-slim pip install --timeout=60 requests
```

### Container Exits Immediately

**Error**:
```
docker compose ps
NAME                STATUS
equipilot-backend   Exited (1) 2 seconds ago
```

**Cause**: Application error on startup (missing env vars, import errors).

**Solution**:
```bash
# Check container logs
docker compose logs backend

# Common causes:
# - Missing OPENAI_API_KEY
# - Invalid Python import
# - Port already in use on host
```

### Health Check Failing

**Error**:
```
docker compose ps
NAME                STATUS
equipilot-backend   unhealthy
```

**Cause**: Health check endpoint is not responding correctly.

**Solution**:
```bash
# Check if the app is running inside the container
docker exec equipilot-backend curl http://localhost:8000/health

# Check health check configuration in docker-compose.yml
# Ensure start_period is long enough for initialization
```

### Read-Only Filesystem Errors

**Error**:
```
OSError: [Errno 30] Read-only file system: '/app/tmp'
```

**Cause**: The container has a read-only filesystem but the application needs to write to a specific location.

**Solution**:
```bash
# Add tmpfs mount in docker-compose.yml
services:
  backend:
    tmpfs:
      - /tmp
```

---

## API Issues

### 404 Not Found

**Error**:
```json
{
  "detail": "Not Found",
  "request_id": "...",
  "error_type": "http_error"
}
```

**Cause**: Requested endpoint does not exist or URL is incorrect.

**Solution**:
```bash
# Verify the endpoint exists
curl http://localhost:8000/openapi.json | python -m json.tool

# Check the correct URL format
# Research endpoints use /api/v1/ prefix
curl http://localhost:8000/api/v1/research
```

### 422 Validation Error

**Error**:
```json
{
  "detail": "field required (type=value_error.missing)",
  "request_id": "...",
  "error_type": "validation_error"
}
```

**Cause**: Request body is missing required fields or has invalid types.

**Solution**:
```bash
# Ensure all required fields are present
curl -X POST "http://localhost:8000/api/v1/research" \
  -H "Content-Type: application/json" \
  -d '{"query": "Analyze AAPL"}'

# Check the schema at /docs for field requirements
```

### CORS Errors

**Error** (in browser console):
```
Access to fetch at 'http://localhost:8000/api/v1/research' from origin 'http://localhost:8501' has been blocked by CORS policy
```

**Cause**: The frontend origin is not in the allowed CORS origins list.

**Solution**:
```env
# Add the frontend URL to CORS_ORIGINS
CORS_ORIGINS=["http://localhost:8501","http://localhost:3000","http://127.0.0.1:8501"]
```

---

## External Service Issues

### OpenAI API Errors

**Error**:
```
openai.AuthenticationError: Incorrect API key provided
```

**Cause**: Invalid or expired OpenAI API key.

**Solution**:
```bash
# Verify your API key
echo $OPENAI_API_KEY

# Test the key directly
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Check OpenAI dashboard for key status
# https://platform.openai.com/api-keys
```

### OpenAI Rate Limit

**Error**:
```
openai.RateLimitError: Rate limit exceeded for API key
```

**Cause**: Exceeded OpenAI API rate limits (varies by tier).

**Solution**:
```bash
# Check your rate limit tier
# https://platform.openai.com/account/limits

# Implement retry with backoff (already built into services)
# Reduce concurrent requests
MAX_CONCURRENT_REQUESTS=5
```

### yfinance Data Issues

**Error**:
```
yfinance.TickerError: Failed to get data for ticker 'INVALID'
```

**Cause**: Invalid ticker symbol or network issue.

**Solution**:
```bash
# Verify the ticker symbol
# Valid examples: AAPL, MSFT, GOOGL, AMZN

# Check network connectivity
python -c "import yfinance as yf; print(yf.Ticker('AAPL').info.get('longName'))"
```

### News API Issues

**Error**:
```
News API request failed: API key not valid
```

**Cause**: Invalid or expired News API key.

**Solution**:
```bash
# Verify your News API key
# Test with your provider's test endpoint

# Or disable news features
ENABLE_NEWS_FETCHING=false
```

---

## Logging and Debugging

### Enable Debug Logging

```bash
# Set log level to DEBUG
LOG_LEVEL=DEBUG

# Or pass directly to uvicorn
uvicorn backend.app:app --log-level debug
```

### View Structured Logs

```bash
# Pretty-print JSON logs
docker compose logs backend | python -m json.tool

# Filter by request ID
docker compose logs backend | grep "550e8400"

# Filter by log level
docker compose logs backend | grep '"level": "error"'
```

### Test Endpoints with curl

```bash
# Health check
curl -v http://localhost:8000/health

# Check response headers
curl -I http://localhost:8000/health

# Submit research request
curl -X POST "http://localhost:8000/api/v1/research" \
  -H "Content-Type: application/json" \
  -d '{"query": "Analyze AAPL"}'
```

---

## Getting Help

If you encounter an issue not covered here:

1. **Check logs**: `docker compose logs -f`
2. **Enable debug mode**: Set `LOG_LEVEL=DEBUG`
3. **Search GitHub issues**: [github.com/Aryan41211/equipilot-ai/issues](https://github.com/Aryan41211/equipilot-ai/issues)
4. **Open a new issue**: Include logs, environment details, and steps to reproduce

---

## Related Documentation

- [Architecture](architecture.md) — System architecture overview
- [API Reference](api.md) — Complete API documentation
- [Deployment Guide](deployment.md) — Production deployment instructions
- [Testing Guide](testing.md) — How to run and write tests