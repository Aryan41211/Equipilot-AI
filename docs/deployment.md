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

#### CORS (deny-by-default in production)
- Production **does not** allow wildcard origins (`*`).
- Backend CORS is controlled by `CORS_ORIGINS`.
- If **no** production origins are configured, CORS remains **disabled** (deny-by-all) and a warning is logged.

**Set `ENVIRONMENT=production` and configure origins:**

**JSON array format**
```bash
ENVIRONMENT=production
CORS_ORIGINS=["https://your-frontend.streamlit.app"]
```

**Comma-separated format**
```bash
ENVIRONMENT=production
CORS_ORIGINS=https://your-frontend.streamlit.app,https://mycompany.com
```

#### Development
- Development allows local Streamlit hosts:
  - http://localhost:8501 / http://127.0.0.1:8501
  - http://localhost:3000 / http://127.0.0.1:3000

#### Other security controls
- Rate limiting via slowapi
- Security headers (CSP, HSTS, XSS)
- Request ID tracking for audit trails

---

## Platform Runbooks

EquiPilot AI is an **informational equity research assistant**. It does not execute
trades, generate trading signals, or give buy/sell recommendations, and deploying it
does not change that.

| Runbook | Deploys | Runs on |
|---------|---------|---------|
| **A** | Backend API | Railway |
| **B** | Frontend UI | Streamlit Community Cloud |
| **C** | Full stack | Docker Compose |

A + B is the production path. C is the all-in-one path for local machines and VPS hosts.

### Port and variable reference

Read this table before any runbook. Every value below is read by the code as written.

| Variable | Read by | Default | Meaning |
|----------|---------|---------|---------|
| `PORT` | `backend/config.py` → `settings.backend_port`; frontend `CMD` (`--server.port=${PORT:-8501}`) | `8000` backend / `8501` frontend | Platform-injected. **Never hardcode it.** |
| `BACKEND_PORT` | same, only as a fallback | `8000` | Ignored when `PORT` is set. |
| `BACKEND_HOST` | `settings.backend_host` | `0.0.0.0` | Backend bind address. |
| `HEALTH_CHECK_PORT` | `frontend/healthz.py` only | `9090` | Docker healthz sidecar port. Not used by the Streamlit app. |
| `HEALTH_CHECK_HOST` | `frontend/healthz.py` only | `0.0.0.0` | Docker healthz sidecar bind address. |
| `EQUIPILOT_API_URL` | `frontend/app.py`, `frontend/components/sidebar.py` | `""` (unset) | Railway host, no path. Unset means the research UI is inert. |
| `EQUIPILOT_HEALTH_URL` | `frontend/app.py` only | `""` (unset) | Railway host **plus** `/health`. Used verbatim. |
| `CORS_ORIGINS` | `backend/config.py` `parse_cors_origins` | `[]` | JSON array or comma-separated. See Runbook A step 3. |

There is no `FRONTEND_PORT`. It was removed once the frontend `CMD` began reading
`${PORT}`; `backend/config.py` still declares an unread `frontend_port` field, and
nothing consumes it.

### Endpoint layout — the asymmetry that trips people up

| Endpoint | Path | Registered in |
|----------|------|---------------|
| Liveness | `/health` | `backend/app.py` — **root**, not under `/api/v1` |
| Readiness | `/ready` | `backend/app.py` — **root**, returns `503` when startup errors exist |
| Version | `/version` | `backend/app.py` — root |
| Metrics | `/metrics` | `backend/app.py` — root |
| OpenAPI docs | `/docs` | `backend/app.py` — root |
| Research API | `/api/v1/research`, `/api/v1/research/{request_id}`, `/api/v1/research/{request_id}/status` | `backend/app.py` under `settings.api_prefix` (`/api/v1`) |

Only the research API lives under `/api/v1`. Health endpoints are at the root, so
`https://<host>/api/v1/health` returns `404`.

---

## Runbook A — Backend on Railway

### A.0 Build-stage prerequisite

The repository's root `Dockerfile` is deployable to Railway as-is. The
`production` stage is the **last** stage in the multi-stage build, and Docker
builds the last stage by default. Since Railway does not support `--target`,
deploying the root `Dockerfile` builds and runs the `production` stage with the
backend `CMD` (`python -m backend.app`). No additional Dockerfile is required.

### A.1 Create the service

1. Push the repository to GitHub.
2. In Railway: **New Project → Deploy from GitHub repo**, select the repo.
3. Railway detects a root `Dockerfile` automatically. **Do not add a `Procfile`** — the
   image `CMD` is the single start command, and Railway errors out when both a build
   file and a start command compete.
4. In the service's **build settings**, set the builder to `Dockerfile` and use the
   default Dockerfile path (the root `Dockerfile`). No `RAILWAY_DOCKERFILE_PATH` is
   required.

### A.2 Variables

Under **Settings → Variables**, add:

| Variable | Value | Consequence if wrong |
|----------|-------|----------------------|
| `OPENAI_API_KEY` | your key | **Startup error in production** — `validate_environment()` records `OPENAI_API_KEY is not set - LLM features unavailable`, so `/ready` returns `503` and `/health` reports `degraded` |
| `SECRET_KEY` | `openssl rand -hex 32` | Warning only: `SECRET_KEY not set - session security may be compromised` |
| `BACKEND_RELOAD` | `false` | Warning only: `BACKEND_RELOAD is enabled in production - disable for performance` |
| `ENVIRONMENT` | `production` | Enables the strict CORS policy and the `OPENAI_API_KEY` check below |
| `LOG_LEVEL` | `INFO` | Default; `DEBUG` is very noisy |
| `LOG_FORMAT` | `json` | Structured logs, already the image default |
| `CORS_ORIGINS` | frontend origin — see A.3 | **Set last** |
| `OPENAI_MODEL` | `gpt-4o` (optional) | Report synthesis |
| `OPENAI_MODEL_MINI` | `gpt-4o-mini` (optional) | Classification and sentiment |
| `NEWS_API_KEY` | optional | Without it, news falls back to free sources |

Only `OPENAI_API_KEY` and a sub-1024 `PORT` are recorded as startup **errors**.
`SECRET_KEY` and `BACKEND_RELOAD` produce `Configuration warning` log lines and nothing
more — set them anyway, but do not expect the deploy to fail if you forget.

Startup errors never kill the process. They are collected into `app.state.startup_errors`,
logged as `Startup completed with errors`, and surfaced by `/ready` as `503` and
`/health` as `"status": "degraded"`. A service can therefore look "up" on Railway's
dashboard while being unready — always check `/ready`.

The `production` image stage already bakes `ENVIRONMENT=production`,
`BACKEND_RELOAD=false`, `LOG_FORMAT=json`, and `PORT=8000` as `ENV` defaults. Setting
them in Railway Variables is still recommended so the service is legible in the
dashboard.

**Do not set `PORT`.** Railway injects it, and `settings.backend_port` reads `PORT`
first (`backend/config.py:115`). Setting it by hand is how a service ends up health-
checking a port it is not listening on.

### A.3 Set `CORS_ORIGINS` last — ordering matters

> [!IMPORTANT]
> **Order of operations. Do not skip ahead.**
>
> 1. Deploy the backend with **`CORS_ORIGINS` unset**. In production an unset value is
>    deny-by-default and logs `CORS_ORIGINS not configured for production; CORS will be
>    deny-by-default.` — the service starts normally.
> 2. Deploy the frontend (Runbook B) and note its **exact** URL, e.g.
>    `https://equipilot-frontend.streamlit.app`.
> 3. Come back, set `CORS_ORIGINS` to that exact URL, and let Railway redeploy.
>
> The frontend URL is not knowable until the frontend is deployed, and guessing it is
> worse than leaving it unset — an allow-list naming an origin that does not exist
> looks identical to a correct one in the logs.

Value format — either works, both are parsed by `parse_cors_origins`:

```bash
# JSON array
CORS_ORIGINS=["https://equipilot-frontend.streamlit.app"]

# comma-separated
CORS_ORIGINS=https://equipilot-frontend.streamlit.app,https://admin.example.com
```

Rules that matter:

- Exact origin: scheme + host + port, **no trailing slash**. `https://app.streamlit.app/`
  will not match.
- To allow the Railway origin too, list it alongside the Streamlit origin.
- A malformed value in production **fails fast by design**: a value starting with `[`
  that is not valid JSON raises `CORS_ORIGINS JSON parsing failed`, and a non-empty
  value that parses to an empty allow-list logs ERROR and raises
  `CORS_ORIGINS parsed to empty allow-list in production`. This is deliberate — a
  silently-empty allow-list looks like a CORS bug that never gets fixed.

> [!NOTE]
> As built today, the frontend calls the backend **server-side** — every request in
> `frontend/app.py` is a Python `requests` call made by the Streamlit process, and no
> browser-side `fetch` to the backend exists. Server-to-server calls ignore CORS, so
> browser CORS is not currently on the critical path. Set the allow-list anyway: it
> costs nothing, it keeps the logs honest about intent, and it keeps the deployment
> correct if a browser-side call or an embedded view is ever added.

### A.4 Watch the startup log

Deploy, then read the log. `LOG_FORMAT=json` gives one JSON object per line. This is
the real shape of the two lines that matter:

```json
{"port": 8080, "host": "0.0.0.0", "cors_origins_raw": "[\"https://equipilot-frontend.streamlit.app\"]", "cors_origins_raw_detected_format": "json_array_candidate", "cors_origins_parsed": ["https://equipilot-frontend.streamlit.app"], "openai_api_key_present": true, "event": "StartupConfig", "logger": "backend.app", "level": "info", "timestamp": "..."}
{"healthy": true, "error_count": 0, "event": "Backend startup complete", "logger": "backend.app", "level": "info", "timestamp": "..."}
```

Field by field, from `backend/app.py`'s lifespan:

| Field | Meaning |
|-------|---------|
| `port` | The port actually bound — Railway's injected `PORT`. If this is `8000`, Railway did not inject one. |
| `host` | Bind address, normally `0.0.0.0`. |
| `cors_origins_raw` | The raw `CORS_ORIGINS` string, or `null` when unset. |
| `cors_origins_raw_detected_format` | One of `empty_or_missing`, `json_array_candidate`, `comma_separated`, `single_value`. |
| `cors_origins_parsed` | The list handed to `CORSMiddleware.allow_origins`. |
| `openai_api_key_present` | `true`/`false` only. The key itself is never logged. |

`Backend startup complete` carries `healthy` and `error_count`. Also expect
`Starting EquiPilot AI backend`, `Research graph initialized successfully`, and
`Exception handlers registered`.

If `error_count` is not `0`, the preceding `Startup completed with errors` line names
the failures.

### A.5 Verify

```bash
curl -fsS https://<your-railway-domain>/health
curl -fsS https://<your-railway-domain>/ready
curl -fsS https://<your-railway-domain>/version
```

| Endpoint | Healthy response |
|----------|------------------|
| `/health` | `200` `{"status": "healthy", "version": ..., "services": {"openai": true, "news_api": false}, "errors": []}` |
| `/ready` | `200` `{"status": "ready", "version": ...}` |
| `/version` | `200` `{"name": "EquiPilot AI", "version": ..., "api_version": "/api/v1"}` |

Both health endpoints stay at the **root** — no `/api/v1` prefix. A `503` from `/ready`
means startup errors were recorded; the body lists them. `/health` returns `200` with
`"status": "degraded"` in that same case, so probe `/ready` when you want a hard
pass/fail.

---

## Runbook B — Frontend on Streamlit Community Cloud

### B.1 Create the app

1. Push the repository to GitHub.
2. Go to **share.streamlit.io → New app → Deploy from GitHub**.
3. **Main file path:** `frontend/app.py`.
4. **Deployments → Python version:** `3.12` — matches `runtime.txt`.
5. Click **Deploy**.

Streamlit Community Cloud installs `requirements.txt` from the repository root. It
does **not** use the repository `Dockerfile`, so the frontend `CMD` and the port-9090
healthz sidecar play no part here. `HEALTH_CHECK_PORT` and `HEALTH_CHECK_HOST` are read
by `frontend/healthz.py` alone and can be ignored for this runbook.

`.streamlit/config.toml` is committed and picked up automatically — it sets
`headless = true`, `enableCORS = false`, and the theme. `.streamlit/secrets.toml` is
gitignored; never commit it.

### B.2 Secrets — the two URLs, and why they differ

Under **Settings → Secrets**:

| Key | Value |
|-----|-------|
| `EQUIPILOT_API_URL` | `https://<your-railway-domain>` |
| `EQUIPILOT_HEALTH_URL` | `https://<your-railway-domain>/health` |

`frontend/app.py` reads only these two. Without `EQUIPILOT_API_URL` the dashboard
renders but research submission and status polling are disabled, and the header shows
`EQUIPILOT_API_URL not configured for this deployment.`

> [!IMPORTANT]
> **The two values are deliberately asymmetric, and getting it backwards breaks the app.**
>
> | | Value | Why |
> |---|-------|-----|
> | `EQUIPILOT_API_URL` | bare host, **no path** | Every research call goes through `build_backend_url()`, which appends `/api/v1` exactly once. Supplying the bare host is the intended form. Including `/api/v1` yourself also works — the function normalizes and will not double it — but the bare host is what the code is written around. |
> | `EQUIPILOT_HEALTH_URL` | host **plus `/health`** | `/health` is registered at the application **root**, not under `/api/v1`. This value is requested verbatim, never through `build_backend_url`, so the `/health` suffix is your job to add. |
>
> The trap: `https://<host>/api/v1/health` returns `404`. That is not a broken
> deployment — that endpoint has never existed.

### B.3 CORS

Streamlit Community Cloud and Railway are different origins. The backend's
`CORS_ORIGINS` allow-list must contain the exact Streamlit URL, including scheme and
with no trailing slash. See Runbook A step 3 — set it after this app has a URL.

### B.4 Confirm it is wired up

On first load the header status indicator reads **API Connected** (green dot) once the
health check succeeds, or **API Disconnected** (red dot) with the configured URL
printed beneath it. A red dot while the Railway backend is cold-starting is expected
for the first few seconds; it should turn green within the 3-second health-check
timeout plus cold-start time.

> [!NOTE]
> The sidebar's *System status* widget now resolves the health check via the
> `EQUIPILOT_HEALTH_URL` setting, with a root-relative `/health` fallback, hitting the
> root `/health` endpoint (not under `/api/v1`). When `EQUIPILOT_HEALTH_URL` is
> configured, the widget uses it verbatim; otherwise it falls back to
> `build_backend_url("health")` behavior corrected to target `/health`. As a result,
> the System Status widget reports **Connected** on a healthy deployment. The header
> indicator also uses `EQUIPILOT_HEALTH_URL` when set and is accurate.

---

## Runbook C — Full stack with Docker Compose

### C.1 Requirements

- Docker with Compose **v2.24 or newer**. `docker-compose.yml` uses the long-form
  `env_file` syntax:

  ```yaml
  env_file:
    - path: .env
      required: false
  ```

  Older Compose rejects it outright. The `required: false` is what lets `docker compose
  config` and `docker compose up` work on a clean checkout where `.env` is absent —
  `.env` is gitignored, so a fresh clone never has one.

  ```bash
  docker compose version   # must report v2.24.0 or newer
  ```

### C.2 Bring it up

```bash
cp .env.example .env      # then fill in OPENAI_API_KEY and SECRET_KEY
docker compose config     # optional: validate before building
docker compose up -d --build
docker compose ps
```

All three services report `healthy`:

| Service | Build target | Container ports | Host ports |
|---------|--------------|-----------------|------------|
| `backend` | `production` | 8000 | `http://localhost:8000` |
| `frontend` | `frontend` | 8501, 9090 | `http://localhost:8501`, `http://localhost:9090` |
| `nginx` | `nginx` | 80 | `http://localhost` |

The frontend runs two processes in one container: Streamlit on 8501 and the
`frontend/healthz.py` sidecar on 9090. Compose sets the frontend's
`EQUIPILOT_API_URL=http://backend:8000`, so the UI talks to the backend directly by
service name and never traverses nginx.

The backend service runs with `ENVIRONMENT: development`, so the production CORS
fail-fast path in Runbook A does **not** apply here. Note that `docker-compose.yml` sets
that in the service's `environment:` block, which takes precedence over `env_file` — put
`ENVIRONMENT=production` in `.env` and this stack will still run in development mode.

### C.3 Where things are exposed

```bash
curl -fsS http://localhost/healthz        # {"status":"ok"}         - nginx itself
curl -fsS http://localhost:9090/healthz   # {"status":"ok"}         - frontend sidecar
curl -fsS http://localhost:8000/health    # {"status":"healthy",..} - backend
curl -fsS http://localhost:8000/ready     # {"status":"ready",..}
```

Then open `http://localhost` for the UI.

`nginx.conf` routes exactly three things:

| Location | Upstream | Notes |
|----------|----------|-------|
| `= /healthz` | nginx itself | Static `{"status":"ok"}`, answered without touching a container |
| `/api/` | `backend:8000` | `proxy_read_timeout 300s` |
| `/` | `frontend:8501` | `proxy_read_timeout 300s`, `proxy_buffering off`, WebSocket upgrade headers |

> [!IMPORTANT]
> **Only `/api/` reaches the backend through nginx.** `/health` and `/ready` are
> registered at the backend's root, so `http://localhost/health` falls through to
> `location /` and hits Streamlit, which returns a `404`. Probe the backend on port
> 8000 directly, as shown above. This is routing, not a fault.

The WebSocket support is what makes Streamlit usable at all behind the proxy: a
`map $http_upgrade $connection_upgrade` block in the `http` context plus
`Upgrade`/`Connection` headers on `location /` mean `/_stcore/stream` returns
`101 Switching Protocols`. Without it the UI would load and then hang on its live
updates.

### C.4 Tear down

```bash
docker compose down                    # keep images
docker compose down -v --rmi all       # also drop volumes and images
```

Use `--rmi all`, not `--rmi local`. Every service here declares a custom tag
(`equipilot-backend:local`, `equipilot-frontend:local`, `equipilot-nginx:local`), and
`local` only removes images *without* a custom tag — it would silently keep all three.

### C.5 Common failures — Compose

| Symptom | Cause | Fix |
|---------|-------|-----|
| `nginx` 502 on `/` | frontend not healthy | `docker compose ps`; `docker compose logs frontend` |
| `nginx` 502 on `/api/` | backend not healthy | `docker compose logs backend` |
| UI loads but updates never arrive | WebSocket blocked at the proxy | Confirm `nginx.conf` still has the `map $http_upgrade $connection_upgrade` block and the upgrade headers on `location /` |
| Research request dies at ~60s | nginx's *default* `proxy_read_timeout` is 60s | `proxy_read_timeout 300s` is set on both `/api/` and `/`; if you edited `nginx.conf`, restore it |
| frontend never becomes healthy | the healthz sidecar and the healthcheck disagree on the port | The container `CMD` backgrounds `python frontend/healthz.py`, which reads `HEALTH_CHECK_PORT` (default `9090`); the image `HEALTHCHECK` and `docker-compose.yml` both pin `9090`. If one side was edited, the healthcheck probes a port nothing is listening on |
| `ENVIRONMENT=production` in `.env` seems ignored | `docker-compose.yml` sets `ENVIRONMENT: development` in the service's `environment:` block, which **overrides** `env_file` | Edit `docker-compose.yml` to change it — `.env` alone cannot switch this stack to production mode |
| `curl http://localhost/health` returns 404 | nginx only proxies `/api/` | Use `http://localhost:8000/health` |
| Compose refuses to parse the file | Compose older than v2.24 | Upgrade Compose; the long-form `env_file` requires it |

### C.6 Common failures — Railway

| Symptom | Cause | Fix |
|---------|-------|-----|
| Service serves the Streamlit UI, not the API | root `Dockerfile` final stage is `nginx` | See A.0 |
| Backend exits immediately at startup | `CORS_ORIGINS` malformed in production | Fix the value; startup fails fast by design (A.3) |
| `StartupConfig.port` is `8000`, not Railway's port | `PORT` set by hand in Variables | Remove it; Railway injects it (A.2) |
| Browser CORS errors | frontend origin missing from `CORS_ORIGINS` | Add the exact Streamlit URL, no trailing slash (A.3) |

---

## Deployment verification checklist

Run top to bottom after any production deploy.

- [ ] `GET /health` → `200`, `"status": "healthy"`, `"errors": []`
- [ ] `GET /ready` → `200` (a `503` names the startup errors in its body)
- [ ] `GET /version` → `200`
- [ ] Startup log contains `StartupConfig` with `port` equal to the platform-assigned
      port, and `openai_api_key_present: true`
- [ ] Startup log contains `Backend startup complete` with `error_count: 0`
- [ ] `CORS_ORIGINS` parsed list contains the exact frontend origin
- [ ] Frontend header shows **API Connected**
- [ ] A real research query returns a completed report

## Scope reminder

EquiPilot AI is an **informational equity research assistant**. It does not execute
trades, produce trading signals, or make buy/sell recommendations. The disclaimer bar
rendered by the frontend states this to users on every screen, and none of the runbooks
above change that boundary.
