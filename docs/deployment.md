# EquiPilot AI — Deployment Guide

## Overview

This guide covers production deployment of EquiPilot AI using Docker and Docker Compose. The application is designed to run as a set of containerized microservices behind an nginx reverse proxy.

---

## Prerequisites

### System Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| RAM | 2 GB | 4 GB |
| Disk | 10 GB | 20 GB |
| Docker Engine | 24+ | 24+ |
| Docker Compose | v2+ | v2+ |

### Required Accounts

- **OpenAI API key** — [Get one here](https://platform.openai.com/api-keys)
- **News API key** (optional) — For news features

---

## Deployment Options

### Option 1: Docker Compose (Recommended)

#### 1. Clone and Configure

```bash
git clone https://github.com/Aryan41211/equipilot-ai.git
cd equipilot-ai

# Create environment file
cp .env.example .env
```

#### 2. Set Environment Variables

Edit `.env` with your production values:

```env
# Required
OPENAI_API_KEY=sk-your-openai-api-key

# Production settings
ENVIRONMENT=production
BACKEND_RELOAD=false
BACKEND_WORKERS=4
LOG_LEVEL=INFO
LOG_FORMAT=json
SECRET_KEY=your-random-secret-key-here

# Optional
NEWS_API_KEY=your-news-api-key
```

#### 3. Deploy

```bash
# Build and start all services
docker compose up --build -d

# Verify deployment
docker compose ps
docker compose logs --tail=50
```

#### 4. Verify Health

```bash
# Check all health endpoints
curl http://localhost:80/health
curl http://localhost:80/ready
curl http://localhost:80/version
```

### Option 2: Manual Deployment

#### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with production values
```

#### 3. Start Services

```bash
# Start backend
uvicorn backend.app:app --host 0.0.0.0 --port 8000 --workers 4

# In a separate terminal, start frontend
streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0
```

---

## Docker Images

### Build Stages

The Dockerfile defines four build stages:

| Stage | Base | Purpose | Size |
|-------|------|---------|------|
| `base` | python:3.12-slim | Dependency installation | ~1.2 GB |
| `production` | python:3.12-slim | Backend runtime | ~400 MB |
| `frontend` | production | Frontend runtime | ~420 MB |
| `development` | base | Hot-reload development | ~1.3 GB |

### Build Commands

```bash
# Production backend
docker build --target production -t equipilot-ai:latest .

# Frontend
docker build --target frontend -t equipilot-ai:frontend .

# Development
docker build --target development -t equipilot-ai:dev .
```

### Image Optimization

The Dockerfile includes several optimizations:

- **Multi-stage builds** — Only runtime dependencies in final image
- **Non-root user** — `appuser` with UID 1000
- **Read-only filesystem** — Prevents unauthorized writes
- **Python optimizations** — `PYTHONDONTWRITEBYTECODE`, `PYTHONUNBUFFERED`
- **uvloop/httptools** — Faster async event loop and HTTP parsing

---

## Docker Compose Services

### Service Overview

| Service | Image | Port | Dependencies |
|---------|-------|------|--------------|
| `backend` | equipilot-ai:latest | 8000 | — |
| `frontend` | equipilot-ai:latest | 8501 | backend (healthy) |
| `nginx` | nginx:alpine | 80, 443 | backend, frontend |

### Resource Limits

```yaml
backend:
  deploy:
    resources:
      limits:
        cpus: "1.0"
        memory: "1G"
      reservations:
        cpus: "0.5"
        memory: "512M"

frontend:
  deploy:
    resources:
      limits:
        cpus: "0.5"
        memory: "512M"

nginx:
  deploy:
    resources:
      limits:
        cpus: "0.5"
        memory: "256M"
```

### Health Checks

Each service includes a health check:

```yaml
backend:
  healthcheck:
    test: ["CMD", "python", "-c", "import urllib.request; import json; resp = urllib.request.urlopen('http://localhost:8000/health'); data = json.loads(resp.read()); assert data.get('status') in ('healthy', 'degraded')"]
    interval: 15s
    timeout: 5s
    retries: 3
    start_period: 10s
```

### Logging Configuration

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

---

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for LLM access | `sk-proj-...` |

### Production-Required

| Variable | Description | Reason |
|----------|-------------|--------|
| `SECRET_KEY` | Secret key for session signing | Required in production mode |
| `ENVIRONMENT=production` | Deployment environment | Enables production validation |
| `BACKEND_RELOAD=false` | Disable auto-reload | Performance and stability |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_MODEL` | `gpt-4o` | Primary LLM model |
| `OPENAI_MODEL_MINI` | `gpt-4o-mini` | Cost-effective model |
| `NEWS_API_KEY` | — | News API key |
| `NEWS_API_PROVIDER` | `newsapi` | News provider |
| `BACKEND_HOST` | `0.0.0.0` | Bind address |
| `BACKEND_PORT` | `8000` | Server port |
| `BACKEND_WORKERS` | `2` | Worker processes |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_FORMAT` | `json` | Log format |
| `CORS_ORIGINS` | `["http://localhost:8501"]` | Allowed origins |
| `REQUEST_RATE_LIMIT` | `100` | Requests per minute |

---

## Health Endpoints

| Endpoint | Method | Purpose | Expected Status |
|----------|--------|---------|-----------------|
| `/health` | GET | Liveness check | 200 (always) |
| `/ready` | GET | Readiness check | 200 (ready) / 503 (not ready) |
| `/version` | GET | Version info | 200 |
| `/metrics` | GET | Performance metrics | 200 |

### Monitoring Configuration

**Docker Compose health check**:
```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import urllib.request; import json; resp = urllib.request.urlopen('http://localhost:8000/health'); data = json.loads(resp.read()); assert data.get('status') in ('healthy', 'degraded')"]
  interval: 15s
  timeout: 5s
  retries: 3
  start_period: 10s
```

**Kubernetes probe**:
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 15

readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 15
```

---

## Nginx Configuration

The nginx reverse proxy provides:

- **SSL termination** — HTTPS support (requires SSL certificates in `./ssl/`)
- **Rate limiting** — Separate zones for health, API, and general traffic
- **Security headers** — CSP, HSTS, XSS protection, CORS
- **Request routing** — Proxies to backend and frontend services
- **Logging** — Structured access logs with request IDs

### SSL Setup

1. Place SSL certificates in `./ssl/` directory:
   ```
   ssl/
   ├── equipilot.crt
   └── equipilot.key
   ```

2. Update nginx.conf to enable HTTPS:
   ```nginx
   server {
       listen 443 ssl;
       ssl_certificate /etc/nginx/ssl/equipilot.crt;
       ssl_certificate_key /etc/nginx/ssl/equipilot.key;
       # ... rest of configuration
   }
   ```

---

## Security Considerations

### Production Checklist

- [ ] `ENVIRONMENT=production` is set
- [ ] `BACKEND_RELOAD=false` is set
- [ ] `SECRET_KEY` is set to a random value
- [ ] `OPENAI_API_KEY` is configured
- [ ] SSL certificates are installed
- [ ] Firewall allows only ports 80/443
- [ ] Docker containers run as non-root user
- [ ] Read-only filesystem is enabled
- [ ] Resource limits are configured
- [ ] Logging is configured with rotation

### Security Features

| Feature | Implementation |
|---------|---------------|
| **Non-root user** | Docker USER directive |
| **Read-only filesystem** | `read_only: true` in compose |
| **No new privileges** | `no-new-privileges:true` security_opt |
| **Rate limiting** | nginx + slowapi |
| **Security headers** | CSP, HSTS, XSS, CORS |
| **Input validation** | Pydantic schemas |
| **Structured logging** | JSON format with request IDs |

---

## Monitoring & Observability

### Logs

All services log to stdout in JSON format:

```json
{
  "event": "Request completed",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "GET",
  "url": "/health",
  "status_code": 200,
  "timestamp": "2026-07-01T10:00:00Z"
}
```

### Metrics

The `/metrics` endpoint provides:

- Request counts per endpoint
- Request counts per status code
- Average response time
- Active request count

### Health Monitoring

- **Liveness** (`/health`): Is the application running?
- **Readiness** (`/ready`): Is the application ready for traffic?
- **Version** (`/version`): What version is deployed?

---

## Troubleshooting

### Common Issues

**Application returns 503 on /ready**
```
Cause: Startup errors (missing API keys, graph initialization failure)
Solution: Check logs for specific error messages
```

**Docker container exits immediately**
```
Cause: Missing environment variables or configuration errors
Solution: Verify .env file and environment variable names
```

**Rate limiting errors (429)**
```
Cause: Too many requests
Solution: Increase rate limits or implement client-side throttling
```

**OpenAI API errors**
```
Cause: Invalid API key, rate limit exceeded, or network issues
Solution: Verify OPENAI_API_KEY, check OpenAI dashboard for limits
```

For more issues, see [troubleshooting.md](troubleshooting.md).

---

## Upgrading

### Steps

1. Pull latest changes:
   ```bash
   git pull origin main
   ```

2. Rebuild and restart:
   ```bash
   docker compose up --build -d
   ```

3. Verify health:
   ```bash
   curl http://localhost:80/health
   curl http://localhost:80/ready
   ```

### Rollback

```bash
# Revert to previous version
git checkout <previous-tag-or-commit>
docker compose up --build -d
```

---

## Related Documentation

- [Architecture](architecture.md) — System architecture overview
- [API Reference](api.md) — Complete API documentation
- [Testing Guide](testing.md) — How to run and write tests
- [Troubleshooting](troubleshooting.md) — Common issues and solutions