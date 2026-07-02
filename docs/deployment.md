# EquiPilot AI — Deployment Guide

## Overview

This guide covers production deployment of EquiPilot AI using two managed platforms:

- **Railway** — Hosts the FastAPI backend as a web service
- **Streamlit Community Cloud** — Hosts the Streamlit frontend

This architecture removes Docker and nginx from the deployment stack, leveraging each platform's native capabilities.

---

## Architecture

```
                    ┌──────────────────────┐
                    │   Streamlit Community │
                    │   Cloud (Frontend)    │
                    │   streamlit.app       │
                    └──────────┬───────────┘
                               │  HTTPS
                               ▼
                    ┌──────────────────────┐
                    │   Railway (Backend)   │
                    │   FastAPI             │
                    │   railway.app         │
                    └──────────────────────┘
```

- **Frontend** (Streamlit) runs on Streamlit Community Cloud and connects to the backend API via `EQUIPILOT_API_URL`
- **Backend** (FastAPI) runs on Railway as a web service, serving the API and health endpoints

---

## Prerequisites

### Required Accounts

| Platform | Purpose | Sign Up |
|----------|---------|---------|
| [Railway](https://railway.app) | Backend (FastAPI) hosting | Free tier available |
| [Streamlit Community Cloud](https://streamlit.io/cloud) | Frontend hosting | Free (linked to GitHub) |
| [OpenAI](https://platform.openai.com) | LLM API key | Pay-as-you-go |

### System Requirements (Local)

| Resource | Minimum |
|----------|---------|
| Python | 3.12+ |
| Git | Latest |

---

## Deployment Steps

### Step 1: Prepare the Repository

```bash
# Clone the repository
git clone https://github.com/Aryan41211/equipilot-ai.git
cd equipilot-ai

# Create a production branch (optional but recommended)
git checkout -b production
```

### Step 2: Deploy Backend to Railway

#### 2.1 Create a Railway Project

1. Log in to [Railway](https://railway.app)
2. Click **New Project** → **Deploy from GitHub repo**
3. Select your `equipilot-ai` repository
4. Railway will auto-detect the Python project

#### 2.2 Configure Railway

Railway needs these settings:

| Setting | Value |
|---------|-------|
| **Root Directory** | `(leave empty — project root)` |
| **Start Command** | `uvicorn backend.app:app --host 0.0.0.0 --port $PORT --workers 2` |
| **Health Check Path** | `/health` |

Railway sets the `PORT` environment variable automatically. The backend binds to `$PORT`.

#### 2.3 Set Environment Variables

In the Railway dashboard, add these environment variables:

| Variable | Value | Notes |
|----------|-------|-------|
| `OPENAI_API_KEY` | `sk-...` | **Required** — Your OpenAI API key |
| `ENVIRONMENT` | `production` | Enables production middleware |
| `BACKEND_RELOAD` | `false` | Disable auto-reload |
| `BACKEND_WORKERS` | `2` | Adjust based on plan |
| `LOG_LEVEL` | `INFO` | Production logging level |
| `LOG_FORMAT` | `json` | Structured JSON logs |
| `SECRET_KEY` | `random-string` | Generate a random secret key |
| `CORS_ORIGINS` | `["https://your-app.streamlit.app"]` | Allow Streamlit Cloud origin |

**Optional variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `NEWS_API_KEY` | — | News API key for news features |
| `NEWS_API_PROVIDER` | `newsapi` | News provider selection |
| `OPENAI_MODEL` | `gpt-4o` | Primary LLM model |
| `OPENAI_MODEL_MINI` | `gpt-4o-mini` | Cost-effective model |
| `REQUEST_RATE_LIMIT` | `100` | Requests per minute |

#### 2.4 Get the Backend URL

Once deployed, Railway provides a URL like:
```
https://equipilot-ai-production.up.railway.app
```

Copy this URL — you'll need it for the frontend configuration.

#### 2.5 Verify Backend

```bash
# Health check
curl https://your-railway-url.up.railway.app/health

# Ready check
curl https://your-railway-url.up.railway.app/ready

# Version info
curl https://your-railway-url.up.railway.app/version
```

Expected health response:
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

---

### Step 3: Deploy Frontend to Streamlit Community Cloud

#### 3.1 Prepare the Frontend Configuration

The frontend needs to know the backend API URL. Configure this via Streamlit secrets.

#### 3.2 Create Streamlit Secrets

Create a `.streamlit/secrets.toml` file in the project root (do NOT commit to git — add to `.gitignore`):

```toml
# .streamlit/secrets.toml
EQUIPILOT_API_URL = "https://your-railway-url.up.railway.app"
EQUIPILOT_HEALTH_URL = "https://your-railway-url.up.railway.app/health"
```

Alternatively, configure secrets directly in the Streamlit Cloud dashboard.

#### 3.3 Deploy to Streamlit Cloud

1. Go to [Streamlit Community Cloud](https://streamlit.io/cloud)
2. Click **New app**
3. Select your GitHub repository
4. Set these configuration values:

| Setting | Value |
|---------|-------|
| **Repository** | `Aryan41211/equipilot-ai` |
| **Branch** | `main` (or `production`) |
| **Main file path** | `frontend/app.py` |
| **Python version** | `3.12` |

5. Under **Advanced settings**, add these secrets:

```toml
EQUIPILOT_API_URL = "https://your-railway-url.up.railway.app"
EQUIPILOT_HEALTH_URL = "https://your-railway-url.up.railway.app/health"
```

6. Click **Deploy**

#### 3.4 Get the Frontend URL

Streamlit Cloud provides a URL like:
```
https://your-app-name.streamlit.app
```

---

## Environment Variables

### Required

| Variable | Platform | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Railway | OpenAI API key for LLM access |
| `EQUIPILOT_API_URL` | Streamlit | Backend API URL for frontend connection |
| `EQUIPILOT_HEALTH_URL` | Streamlit | Backend health endpoint URL |

### Production Settings (Railway)

| Variable | Value | Reason |
|----------|-------|--------|
| `ENVIRONMENT` | `production` | Enables production middleware and validation |
| `BACKEND_RELOAD` | `false` | Performance and stability |
| `SECRET_KEY` | `<random>` | Session signing security |
| `LOG_FORMAT` | `json` | Structured logging for observability |
| `CORS_ORIGINS` | `["https://your-app.streamlit.app"]` | Allow frontend origin |

### Optional (Railway)

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_MODEL` | `gpt-4o` | Primary LLM model |
| `OPENAI_MODEL_MINI` | `gpt-4o-mini` | Cost-effective model |
| `NEWS_API_KEY` | — | News API key |
| `NEWS_API_PROVIDER` | `newsapi` | News provider |
| `BACKEND_WORKERS` | `2` | Worker processes (1-8) |
| `LOG_LEVEL` | `INFO` | Logging level |
| `REQUEST_RATE_LIMIT` | `100` | Requests per minute |

---

## Health Endpoints

The backend exposes these endpoints for monitoring:

| Endpoint | Method | Purpose | Expected Status |
|----------|--------|---------|-----------------|
| `/health` | GET | Liveness check | 200 (always) |
| `/ready` | GET | Readiness check | 200 (ready) / 503 (not ready) |
| `/version` | GET | Version info | 200 |
| `/metrics` | GET | Performance metrics | 200 |

Railway uses the `/health` endpoint for its health check monitoring.

---

## Security Considerations

### Production Checklist

- [ ] `ENVIRONMENT=production` is set on Railway
- [ ] `BACKEND_RELOAD=false` is set
- [ ] `SECRET_KEY` is set to a random value
- [ ] `OPENAI_API_KEY` is configured
- [ ] `CORS_ORIGINS` is set to the Streamlit app URL only
- [ ] `.streamlit/secrets.toml` is NOT committed to git
- [ ] Railway health checks are configured
- [ ] Logging is configured with JSON format

### Security Features

| Feature | Implementation |
|---------|---------------|
| **CORS** | Restricted to Streamlit app origin |
| **Rate limiting** | Slowapi (application-level) |
| **Security headers** | CSP, HSTS, XSS (FastAPI middleware) |
| **Input validation** | Pydantic schemas |
| **Structured logging** | JSON format with request IDs |

---

## Monitoring & Observability

### Logs

**Railway**: View logs in the Railway dashboard under the **Deployments** tab.

**Streamlit Cloud**: View logs in the Streamlit Cloud dashboard under **Manage app** → **Logs**.

### Health Monitoring

- **Liveness** (`/health`): Is the application running?
- **Readiness** (`/ready`): Is the application ready for traffic?
- **Version** (`/version`): What version is deployed?

### Metrics

The `/metrics` endpoint provides:
- Request counts per endpoint
- Request counts per status code
- Average response time
- Active request count

---

## Troubleshooting

### Common Issues

**Backend returns 503 on /ready**
```
Cause: Startup errors (missing API keys, graph initialization failure)
Solution: Check Railway logs for specific error messages
```

**Frontend cannot connect to backend**
```
Cause: CORS misconfiguration or incorrect EQUIPILOT_API_URL
Solution: Verify CORS_ORIGINS on Railway includes the exact Streamlit app URL
```

**Rate limiting errors (429)**
```
Cause: Too many requests
Solution: Increase REQUEST_RATE_LIMIT or implement client-side throttling
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

1. Push changes to your GitHub repository
2. **Railway**: Automatic redeploy from the connected branch
3. **Streamlit Cloud**: Automatic redeploy from the connected branch
4. Verify health:
   ```bash
   curl https://your-railway-url.up.railway.app/health
   curl https://your-railway-url.up.railway.app/ready
   ```

### Rollback

- **Railway**: Go to **Deployments** → select a previous deployment → **Redeploy**
- **Streamlit Cloud**: Go to **Manage app** → **Reboot** or redeploy a previous commit

---

## Related Documentation

- [Architecture](architecture.md) — System architecture overview
- [API Reference](api.md) — Complete API documentation
- [Testing Guide](testing.md) — How to run and write tests
- [Troubleshooting](troubleshooting.md) — Common issues and solutions