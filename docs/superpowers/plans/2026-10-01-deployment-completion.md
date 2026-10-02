# EquiPilot AI — Deployment Completion Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Take EquiPilot AI from "tests pass locally" to "deployable to Railway (backend) + Streamlit Community Cloud (frontend) with green CI, working Docker images, and documented manual steps."

**Architecture:** Two deployable units. Backend is a FastAPI app served by uvicorn (Railway or Docker). Frontend is a thin Streamlit client that only talks to the backend over HTTPS (`EQUIPILOT_API_URL`). Docker Compose is the local-parity path: separate images for backend / frontend / nginx, built as multi-stage targets from one `Dockerfile`.

**Tech Stack:** Python 3.12, FastAPI 0.115, LangGraph 0.2.34, Streamlit 1.39, Docker multi-stage, GitHub Actions, Railway, Streamlit Community Cloud.

**Spec:** `docs/deployment.md`, `docs/ARCHITECTURE.md`, `CLAUDE.md`, plus the repo's own `TODO.md` / `TOD0.md` / `AUDIT_REPORT.md`.

## Global Constraints

- Python 3.12 exactly. `runtime.txt` stays `3.12`.
- Dependency pinning stays exact (`==`) in `requirements.txt` / `requirements-dev.txt`.
- Runtime deps live in `requirements.txt`; test/lint tooling lives in `requirements-dev.txt`. Never mix them.
- Line length is 100 for both Ruff and Black (`pyproject.toml`).
- Ruff `select` list and `ignore` list in `pyproject.toml` are the source of truth for lint rules — extend with per-file ignores, do not delete rules to silence errors.
- Never log or commit secret values. Logging an API key's *presence* (`bool`) is allowed; logging the value is not.
- Production mode is `ENVIRONMENT=production`. In production CORS is deny-by-default and `CORS_ORIGINS` must parse to a non-empty allow-list or startup fails.
- `BACKEND_RELOAD` must be `false` in production.
- No new top-level dependencies without adding them to the right requirements file with a pinned version.
- The Dockerfile must keep a stage named `AS production` and a stage named `AS frontend` (`tests/test_production.py:471` asserts all three stage names).

---

## Audit Findings — Current State (verified 2026-10-01)

| # | Finding | Evidence |
|---|---|---|
| 1 | Test suite is green: **212 passed** | `python -m pytest tests/ -q` |
| 2 | **Ruff fails: 82 errors** across 17 rule families — CI lint job is red | `python -m ruff check backend/ frontend/ tests/` |
| 3 | **Black fails: 48 files** would be reformatted — CI lint job is red | `python -m black --check backend/ frontend/ tests/` |
| 4 | **CI installs only `requirements.txt`**, which contains no pytest/ruff/black → lint and test jobs would crash even if code were clean | `.github/workflows/ci.yml` + `requirements.txt` |
| 5 | Dockerfile has `AS frontend` stage but it only re-copies `frontend/` — it never installs or starts Streamlit, has no healthcheck, and inherits the backend `CMD` | `Dockerfile:14` |
| 6 | Dockerfile has **no `EXPOSE`** directive and no `ENV` defaults | `Dockerfile` |
| 7 | `docker-compose.yml` builds the `nginx` service from `target: production` — there is **no nginx stage and nginx.conf is never COPY'd**, so the nginx container cannot serve anything | `docker-compose.yml:42-47`, `Dockerfile` |
| 8 | Frontend container healthcheck hits `:9090/healthz` but nothing in the frontend image ever launches `frontend/healthz.py` | `docker-compose.yml:35`, `frontend/healthz.py` |
| 9 | `Procfile` and `Dockerfile` both define a start command → Railway ambiguity (open item #1 in `TODO.md`) | `Procfile`, `Dockerfile:27` |
| 10 | `backend/app.py` `_run_graph()` already uses `await compiled.ainvoke(...)` — the `asyncio.to_thread` item in `TOD0.md` is **obsolete** | `backend/app.py:470` |
| 11 | Startup `StartupConfig` log line (PORT, CORS raw/format/parsed, OpenAI key presence) **already implemented** — `TODO.md` items 3–5 are done | `backend/app.py:92-116` |
| 12 | CORS parse failure in production already raises — `TODO.md` item 8 done | `backend/config.py` `enforce_environment_cors` |
| 13 | LLM client is already lazily constructed — `TODO.md` item 2 done | `backend/services/llm_service.py:20-36` |
| 14 | **181 `.pyc` files are tracked in git** | `git ls-files \| grep .pyc` |
| 15 | **181 stray file** at repo root: `s -ExecutionPolicy RemoteSigned) ; (& ?c?projects...Activate.ps1?)` | root listing |
| 16 | `.gitignore:28` ignores `.streamlit/` but `.streamlit/config.toml` is force-tracked — future edits to it will be silently ignored | `git check-ignore -v .streamlit/config.toml` |
| 17 | No `.pre-commit-config.yaml`, no `.github/CODEOWNERS`, no `.github/dependabot.yml` | filesystem check |
| 18 | CI has no deploy job, no dependency scanning, no Docker build validation | `.github/workflows/ci.yml` |
| 19 | `.dockerignore` excludes `tests/` but not `archive/`, `docs/`, `.github/`, `*.md` | `.dockerignore` |
| 20 | `AUDIT_REPORT.md` duplicate-file cleanup is stale — `design_system*.py` duplicates are gone, `research_graph.py` moved to `archive/`, `requirements-dev.txt` now exists | `AUDIT_REPORT.md` vs filesystem |

---

## File Structure

Files created or modified by this plan:

```
.github/
  workflows/ci.yml                    MODIFY  lint+test+build matrix, add docker build validation
  dependabot.yml                     CREATE  pip + github-actions updates
  CODEOWNERS                         CREATE  required-review routing
Dockerfile                            MODIFY  real frontend stage, nginx stage, EXPOSE, ENV
.dockerignore                         MODIFY  exclude archive/, docs/, .github/, md
docker-compose.yml                    MODIFY  correct targets, commands, healthchecks
Procfile                              DELETE   resolved by Dockerfile CMD (single start command)
nginx.conf                            MODIFY  add /healthz, proxy /api to backend
.env.example                          MODIFY  add frontend + PORT vars
.gitignore                            MODIFY  un-ignore .streamlit/config.toml
pyproject.toml                        MODIFY  per-file ruff ignores for pre-existing debt
frontend/healthz.py                   MODIFY  read PORT, bind configurable host
frontend/app.py                       MODIFY  none required (verify only)
backend/app.py                        MODIFY  none required (verify only)
docs/deployment.md                    MODIFY  Railway + Streamlit Cloud + Docker runbooks
docs/superpowers/plans/               this plan
tests/test_docker_config.py           CREATE  assert image/CMD/stage invariants
tests/test_deploy_config.py           CREATE  assert env-var contract for both platforms
```

---

## Task 1: Unblock CI — install dev dependencies in CI

The single highest-value fix. Lint and test jobs both `pip install -r requirements.txt`, which has no pytest/ruff/black. Both jobs fail at the first tool invocation regardless of code quality.

**Files:**
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: `requirements.txt`, `requirements-dev.txt` (existing)
- Produces: every CI job installs `-r requirements.txt -r requirements-dev.txt`; later tasks rely on CI running ruff/black/pytest.

- [ ] **Step 1: Confirm the failure mode locally**

Run: `python -c "import pytest"` in an env built from `requirements.txt` only.
Expected: fails (proves CI's install step is insufficient).

- [ ] **Step 2: Fix both install steps in ci.yml**

In `.github/workflows/ci.yml`, the lint job has:

```yaml
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
```

Replace with:

```yaml
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt -r requirements-dev.txt
```

Apply the identical replacement to the **test** job's `- name: Install dependencies` step (the second occurrence of that block, which also adds `--cov` flags to pytest).

- [ ] **Step 3: Add dev-deps to the pip cache key**

Both jobs use:

```yaml
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
```

Replace `hashFiles('requirements.txt')` with `hashFiles('requirements.txt', 'requirements-dev.txt')` in both jobs so a dev-dep bump busts the cache.

- [ ] **Step 4: Verify the YAML parses and the pattern applied twice**

Run: `python -c "import yaml,io; d=yaml.safe_load(io.open('.github/workflows/ci.yml',encoding='utf-8')); print(len(d['jobs']))"`
Expected: `2`

Run: `Select-String -Path .github/workflows/ci.yml -Pattern "requirements-dev.txt" | Measure-Object | Select-Object -ExpandProperty Count`
Expected: `4` (2 install commands + 2 cache keys)

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: install dev dependencies so lint and test jobs can run"
```

---

## Task 2: Clear the Ruff backlog (82 errors)

CI's `ruff check` runs with `continue-on-error: false`, so all 82 errors block the pipeline. Breakdown: 17× SIM117, 12× B904, 11× W292, 9× RUF012, 6× F401, 5× ARG002, 4× E402, 3× SIM112, 3× I001, 2× ARG005, 2× F841, plus singles (B017, B023, B905, SIM105, SIM118, ARG001, RUF001, RUF006).

**Files:**
- Modify: files reported by ruff (mostly `backend/`, `tests/`)
- Modify: `pyproject.toml` (only for justified per-file ignores)

**Interfaces:**
- Consumes: `pyproject.toml` `[tool.ruff.lint]` config
- Produces: `ruff check backend/ frontend/ tests/` exits 0

- [ ] **Step 1: Capture the full baseline**

Run: `python -m ruff check backend/ frontend/ tests/ --statistics`
Expected: the counts listed in Finding 2. Save this output for comparison in Step 5.

- [ ] **Step 2: Apply the safe autofixes**

Run: `python -m ruff check backend/ frontend/ tests/ --fix`
Expected: 22 errors fixed (W292, F401, I001, F841, B905, SIM118).

- [ ] **Step 3: Fix the mechanical `with` merges (SIM117, 17 occurrences)**

Ruff flags `with a: ... with b: ...` that could be `with a, b:`. Apply the autofix for this rule explicitly, then hand-review each: nested `with` blocks where the inner block re-binds a name from the outer must **not** be merged.

Run: `python -m ruff check backend/ frontend/ tests/ --select SIM117 --fix`
Expected: SIM117 count drops to 0.

- [ ] **Step 4: Fix `raise ... from` (B904, 12 occurrences)**

Every `raise` inside an `except` block must chain the cause. For each site, the pattern is:

```python
    except SomeError:
        raise SomeOtherError("...") from e
```

If the handler binds no exception variable, add one: `except SomeError as e:`. Exception: `raise ... from None` is acceptable when the intent is deliberate suppression — in that case add `# noqa: B904` with a one-line reason.

Run: `python -m ruff check backend/ frontend/ tests/ --select B904`
Expected: `All checks passed!`

- [ ] **Step 5: Fix `RUF012` — mutable class defaults (9 occurrences)**

`RUF012` fires on class attributes like `metrics = {...}` or `allowed = []`. The correct fix depends on intent:

- Module-level singleton shared across requests → keep mutable, but annotate with `typing.ClassVar`:
  ```python
  from typing import ClassVar
  metrics: ClassVar[dict[str, int]] = {...}
  ```
- Per-instance state → move into `__init__`.

`backend/middleware/production.py:18` holds the in-memory `metrics` dict — that is a deliberate cross-request singleton, so use `ClassVar` there, not `__init__`.

Run: `python -m ruff check backend/ frontend/ tests/ --select RUF012`
Expected: `All checks passed!`

- [ ] **Step 6: Fix `ARG002`/`ARG005`/`ARG001` — unused arguments (8 occurrences)**

These are interface-mandated no-ops. Do **not** rename or delete parameters (LangGraph node signatures and tool signatures are contracts). Prefix with underscore:

```python
async def research_node(state: GraphState) -> dict[str, Any]:
```
→
```python
async def research_node(state: GraphState, _config: RunnableConfig | None = None) -> dict[str, Any]:
```

For `ARG005` (unused lambda argument), rename to `_state` / `_request` at the call site.

Run: `python -m ruff check backend/ frontend/ tests/ --select ARG`
Expected: `All checks passed!`

- [ ] **Step 7: Fix `E402` — imports after code (4 occurrences)**

`frontend/app.py` intentionally inserts the project root into `sys.path` before importing `frontend.components.*`. That is correct and must stay. Add a scoped ignore rather than restructuring:

In `pyproject.toml`, under `[tool.ruff.lint.per-file-ignores]`, add:
```toml
"frontend/app.py" = ["E402"]
```

Then fix the remaining 3 by moving imports above executable statements.

- [ ] **Step 8: Fix `SIM112` — capitalized env var names (3 occurrences)**

`os.getenv("OPENAI_API_KEY")` → `os.getenv("openai_api_key")`. Before changing, confirm the variable is also declared in `.env` / CI env. `config.py` reads via pydantic (case-insensitive), but direct `os.environ` reads in `backend/app.py` and `backend/config.py` use mixed case — normalize all direct reads to lowercase and verify each against `.env.example`.

Run: `Select-String -Path backend\*.py,backend\**\*.py -Pattern 'environ.get\("[A-Z]' `
Expected: no output

- [ ] **Step 9: Fix singles: B017, B023, B905, SIM105, RUF001, RUF006**

- **B017** (`tests/test_synthesis_agent.py:218`): `with pytest.raises(Exception):` → narrow it to the actual exception the model raises, e.g. `pytest.raises(ValidationError)` from `pydantic`.
- **B023** (function uses loop variable): bind the loop value to a local before the closure captures it, or pass it as a default arg.
- **B905**: `zip(a, b)` → `zip(a, b, strict=False)`.
- **SIM105**: replace `try/except: pass` with `contextlib.suppress(ExcType)`.
- **RUF001** (ambiguous unicode): the `—` em dash in a docstring/comment → use a plain hyphen, or `# noqa: RUF001` if the typography is deliberate in user-facing copy.
- **RUF006** (asyncio dangling task): `backend/app.py` calls `asyncio.create_task(_run_graph())` without holding a reference. Store it: `app.state._research_task = asyncio.create_task(_run_graph())` and cancel/await it in the shutdown half of the lifespan.

- [ ] **Step 10: Verify ruff is clean and tests still pass**

Run: `python -m ruff check backend/ frontend/ tests/`
Expected: `All checks passed!`

Run: `python -m pytest tests/ -q`
Expected: `212 passed` (or more — never fewer than 212)

- [ ] **Step 11: Commit**

```bash
git add backend/ frontend/ tests/ pyproject.toml
git commit -m "style: resolve ruff lint backlog blocking CI"
```

---

## Task 3: Apply Black formatting (48 files)

`black --check` fails on 48 files and blocks the lint job.

**Files:**
- Modify: 48 Python files under `backend/`, `frontend/`, `tests/`

**Interfaces:**
- Consumes: `pyproject.toml` `[tool.black]` (line-length 100, py312)
- Produces: `black --check backend/ frontend/ tests/` exits 0

- [ ] **Step 1: Reformat**

Run: `python -m black backend/ frontend/ tests/`
Expected: `48 files reformatted`.

- [ ] **Step 2: Re-run ruff (formatting can introduce new lint hits, e.g. line-splitting artifacts)**

Run: `python -m ruff check backend/ frontend/ tests/`
Expected: `All checks passed!` If new errors appear, fix them and repeat Step 1.

- [ ] **Step 3: Verify tests**

Run: `python -m pytest tests/ -q`
Expected: `212 passed` or more.

- [ ] **Step 4: Verify black check passes**

Run: `python -m black --check backend/ frontend/ tests/`
Expected: `All done! ✨ 🍰 ✨` / `78 files would be left unchanged.`

- [ ] **Step 5: Commit**

```bash
git add backend/ frontend/ tests/
git commit -m "style: apply black formatting"
```

---

## Task 4: Add tests that lock in the deployment contract

Right now nothing verifies that the Docker image actually runs Streamlit, that a single start command exists, or that the env-var contract both platforms depend on is complete. These tests turn the manual steps in Tasks 5–8 into regression-proofed facts.

**Files:**
- Create: `tests/test_docker_config.py`
- Create: `tests/test_deploy_config.py`

**Interfaces:**
- Consumes: `Dockerfile`, `docker-compose.yml`, `Procfile`, `nginx.conf`, `.env.example`
- Produces: test names `TestDockerfileRuntime`, `TestComposeWiring`, `TestDeployEnvContract` used by later verification steps

- [ ] **Step 1: Write the failing Dockerfile tests**

Create `tests/test_docker_config.py`:

```python
"""Tests that pin the Docker runtime contract for deployment."""

import os
import re


def _read(path: str) -> str:
    assert os.path.exists(path), f"{path} must exist"
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestDockerfileRuntime:
    """The image must actually start Streamlit in the frontend stage."""

    def test_frontend_stage_installs_streamlit(self):
        content = _read("Dockerfile")
        frontend_stage = content.split("AS frontend", 1)[1]
        assert "streamlit" in frontend_stage.lower(), (
            "frontend stage must install/ensure streamlit is available"
        )

    def test_frontend_stage_starts_streamlit(self):
        content = _read("Dockerfile")
        frontend_stage = content.split("AS frontend", 1)[1]
        assert re.search(r"CMD.*streamlit", frontend_stage), (
            "frontend stage CMD must launch streamlit"
        )

    def test_frontend_stage_has_healthcheck(self):
        content = _read("Dockerfile")
        frontend_stage = content.split("AS frontend", 1)[1]
        assert "HEALTHCHECK" in frontend_stage
        assert "9090" in frontend_stage

    def test_nginx_stage_exists(self):
        content = _read("Dockerfile")
        assert "AS nginx" in content
        assert "nginx" in content

    def test_expose_directives_present(self):
        content = _read("Dockerfile")
        assert re.search(r"^EXPOSE\s+8000", content, re.MULTILINE)
        assert re.search(r"^EXPOSE\s+8501", content, re.MULTILINE)

    def test_single_start_command(self):
        """Railway errors when both a Procfile and a Dockerfile CMD exist."""
        assert not os.path.exists("Procfile"), (
            "Procfile must be removed; Dockerfile CMD is the single start command"
        )


class TestComposeWiring:
    """compose must build the stages it claims to build."""

    def test_services_target_existing_stages(self):
        content = _read("docker-compose.yml")
        dockerfile = _read("Dockerfile")
        targets = re.findall(r"target:\s*(\w+)", content)
        assert targets, "compose must declare build targets"
        for target in targets:
            assert f"AS {target}" in dockerfile, f"missing Dockerfile stage: {target}"

    def test_nginx_service_uses_nginx_stage(self):
        content = _read("docker-compose.yml")
        nginx_block = content.split("nginx:")[-1]
        assert "target: nginx" in nginx_block
```

- [ ] **Step 2: Run to verify the tests fail**

Run: `python -m pytest tests/test_docker_config.py -v`
Expected: multiple FAILs — `test_frontend_stage_installs_streamlit`, `test_nginx_stage_exists`, `test_expose_directives_present`, `test_single_start_command`, `test_services_target_existing_stages` all fail against the current Dockerfile.

- [ ] **Step 3: Write the failing deploy-contract tests**

Create `tests/test_deploy_config.py`:

```python
"""Tests that pin the env-var contract for Railway + Streamlit Cloud."""

import os


def _read(path: str) -> str:
    assert os.path.exists(path), f"{path} must exist"
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestDeployEnvContract:
    """Every var the platforms need must be documented in .env.example."""

    REQUIRED_BACKEND_VARS = [
        "ENVIRONMENT",
        "OPENAI_API_KEY",
        "SECRET_KEY",
        "BACKEND_RELOAD",
        "PORT",
        "CORS_ORIGINS",
        "LOG_LEVEL",
        "LOG_FORMAT",
    ]

    REQUIRED_FRONTEND_VARS = [
        "EQUIPILOT_API_URL",
        "EQUIPILOT_HEALTH_URL",
        "HEALTH_CHECK_PORT",
    ]

    def test_env_example_documents_backend_vars(self):
        content = _read(".env.example")
        for var in self.REQUIRED_BACKEND_VARS:
            assert var in content, f".env.example missing {var}"

    def test_env_example_documents_frontend_vars(self):
        content = _read(".env.example")
        for var in self.REQUIRED_FRONTEND_VARS:
            assert var in content, f".env.example missing {var}"

    def test_port_documented(self):
        content = _read(".env.example")
        assert "PORT=" in content

    def test_nginx_conf_proxies_api_to_backend(self):
        content = _read("nginx.conf")
        assert "backend:8000" in content
        assert "/api/" in content

    def test_streamlit_config_is_not_gitignored(self):
        """config.toml is force-tracked; the ignore rule would silently drop edits."""
        result = os.popen('git check-ignore -v --no-index .streamlit/config.toml').read()
        assert result.strip() == "", (
            f".streamlit/config.toml must not be gitignored, got: {result}"
        )
```

- [ ] **Step 4: Run to verify these fail**

Run: `python -m pytest tests/test_deploy_config.py -v`
Expected: FAILs on the missing `PORT`, `EQUIPILOT_API_URL`, `EQUIPILOT_HEALTH_URL`, `HEALTH_CHECK_PORT` entries, the nginx `/api/` proxy, and the gitignore rule.

- [ ] **Step 5: Commit the failing tests**

```bash
git add tests/test_docker_config.py tests/test_deploy_config.py
git commit -m "test: pin Docker runtime and deploy env contract"
```

---

## Task 5: Fix the Dockerfile (real frontend + nginx stages)

Finding 5–7: the `frontend` stage is a no-op copy that would still run the backend CMD; there is no nginx stage; no `EXPOSE`; no `ENV` defaults.

**Files:**
- Modify: `Dockerfile`
- Delete: `Procfile`

**Interfaces:**
- Consumes: `requirements.txt`, `frontend/healthz.py`, `nginx.conf`
- Produces: stages `base`, `production`, `frontend`, `nginx`; `EXPOSE 8000` / `8501` / `9090`; `ENV PORT=8000`, `ENV HEALTH_CHECK_PORT=9090`

- [ ] **Step 1: Replace the Dockerfile**

Overwrite `Dockerfile` with:

```dockerfile
# syntax=docker/dockerfile:1

# ---------- base: shared runtime image ----------
FROM python:3.12-slim AS base
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# ---------- backend ----------
FROM base AS production
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend /app/backend
COPY frontend /app/frontend

ENV PORT=8000 \
    ENVIRONMENT=production \
    BACKEND_RELOAD=false \
    LOG_FORMAT=json

RUN useradd -m -u 10001 appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import os,urllib.request; url='http://localhost:'+os.getenv('PORT','8000')+'/health'; urllib.request.urlopen(url,timeout=3)"

CMD ["python", "-m", "backend.app"]

# ---------- frontend (Streamlit) ----------
FROM base AS frontend
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY frontend /app/frontend
COPY .streamlit /app/.streamlit

ENV FRONTEND_PORT=8501 \
    HEALTH_CHECK_PORT=9090

RUN useradd -m -u 10001 appuser \
    && mkdir -p /home/appuser/.streamlit \
    && chown -R appuser:appuser /home/appuser
USER appuser

EXPOSE 8501 9090

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen('http://localhost:'+os.getenv('HEALTH_CHECK_PORT','9090')+'/healthz',timeout=3)"

# Streamlit needs $PORT; run the healthz sidecar in the same container.
CMD ["sh", "-c", "python frontend/healthz.py & exec streamlit run frontend/app.py --server.port=${FRONTEND_PORT:-8501} --server.address=0.0.0.0 --server.headless=true"]

# ---------- nginx reverse proxy ----------
FROM nginx:1.27-alpine AS nginx
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://localhost/healthz || exit 1
```

Notes on the deliberate changes:
- Healthchecks use `urllib` instead of `requests` — `requests` is only present transitively via `yfinance`, and a healthcheck must not depend on a transitive dep.
- The frontend `CMD` backgrounds `frontend/healthz.py` then `exec`s Streamlit, so one container serves both 8501 and 9090 and compose's existing healthcheck target becomes valid.
- The nginx stage is a real `nginx:alpine` base with `nginx.conf` copied in.

- [ ] **Step 2: Delete Procfile**

Run: `git rm Procfile`
Expected: `rm 'Procfile'`

Rationale (closes `TODO.md` item 1): Railway picks up `Dockerfile` and uses its `CMD`/`start-period`. Having both a `Procfile` and a Dockerfile leaves the start command ambiguous.

- [ ] **Step 3: Run the Dockerfile tests**

Run: `python -m pytest tests/test_docker_config.py -v`
Expected: all pass.

- [ ] **Step 4: Run the full suite**

Run: `python -m pytest tests/ -q`
Expected: all pass, none fewer than 212 + the new tests.

- [ ] **Step 5: Build both images for real**

Run: `docker build --target production -t equipilot-backend:local .`
Expected: build succeeds.

Run: `docker build --target frontend -t equipilot-frontend:local .`
Expected: build succeeds.

- [ ] **Step 6: Smoke-test the frontend container's health endpoint**

Run (PowerShell, background start then probe):
```powershell
docker run -d --name eqp-fe -p 8501:8501 -p 9090:9090 equipilot-frontend:local
Start-Sleep -Seconds 12
(Invoke-WebRequest http://localhost:9090/healthz).Content
```
Expected: `{"status": "ok"}`

Run: `docker rm -f eqp-fe`
Expected: container removed.

- [ ] **Step 7: Commit**

```bash
git add Dockerfile Procfile
git commit -m "build: real streamlit frontend and nginx docker stages"
```

---

## Task 6: Wire docker-compose to the correct stages

Finding 7–8: `nginx` was built from `target: production`, and the frontend healthcheck pointed at a server that never ran.

**Files:**
- Modify: `docker-compose.yml`

**Interfaces:**
- Consumes: stages `production`, `frontend`, `nginx` from Task 5
- Produces: three services `backend` (8000), `frontend` (8501, 9090), `nginx` (80)

- [ ] **Step 1: Replace docker-compose.yml**

Overwrite with:

```yaml
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    image: equipilot-backend:local
    env_file:
      - .env
    environment:
      ENVIRONMENT: development
      BACKEND_RELOAD: "false"
      PORT: "8000"
    ports:
      - "8000:8000"
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: "512M"
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health',timeout=3)"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 15s
    restart: unless-stopped

  frontend:
    build:
      context: .
      dockerfile: Dockerfile
      target: frontend
    image: equipilot-frontend:local
    environment:
      FRONTEND_PORT: "8501"
      HEALTH_CHECK_PORT: "9090"
      EQUIPILOT_API_URL: "http://backend:8000"
      EQUIPILOT_HEALTH_URL: "http://backend:8000/health"
    ports:
      - "8501:8501"
      - "9090:9090"
    depends_on:
      backend:
        condition: service_healthy
    deploy:
      resources:
        limits:
          cpus: "0.5"
          memory: "256M"
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:9090/healthz',timeout=3)"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 15s
    restart: unless-stopped

  nginx:
    build:
      context: .
      dockerfile: Dockerfile
      target: nginx
    image: equipilot-nginx:local
    ports:
      - "80:80"
    depends_on:
      backend:
        condition: service_healthy
      frontend:
        condition: service_healthy
    deploy:
      resources:
        limits:
          cpus: "0.2"
          memory: "128M"
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost/healthz"]
      interval: 30s
      timeout: 5s
      retries: 3
    restart: unless-stopped
```

Notes: the `version:` key is removed (obsolete in Compose v2). `EQUIPILOT_API_URL` points at the in-network service name, not `localhost`.

- [ ] **Step 2: Validate the compose file**

Run: `docker compose config --quiet`
Expected: exit 0, no output.

- [ ] **Step 3: Bring the stack up**

Run: `docker compose up -d --build`
Expected: all three services reach `healthy`.

Run: `docker compose ps`
Expected: `backend`, `frontend`, `nginx` all `healthy`.

- [ ] **Step 4: Verify the proxy path end to end**

Run: `(Invoke-WebRequest http://localhost/healthz).Content`
Expected: `{"status": "ok"}`

Run: `(Invoke-WebRequest http://localhost/api/v1/... )` — substitute a real route; simplest is the backend root through the proxy once a `/api/` rule exists (Task 7).

- [ ] **Step 5: Commit**

```bash
git add docker-compose.yml
git commit -m "build: wire compose to real backend/frontend/nginx targets"
```

---

## Task 7: Fix nginx routing and the frontend healthz server

Finding 8: `frontend/healthz.py` hardcodes port 9090 and binds `0.0.0.0` with no override; `nginx.conf` has no `/api/` route to the backend and no `/healthz`.

**Files:**
- Modify: `nginx.conf`
- Modify: `frontend/healthz.py`
- Modify: `.env.example`

**Interfaces:**
- Consumes: service names `frontend:8501`, `backend:8000` from Task 6
- Produces: nginx routes `/` → frontend, `/api/` → backend, `/healthz` → local 200; healthz honours `HEALTH_CHECK_PORT` and `HEALTH_CHECK_HOST`

- [ ] **Step 1: Write the failing healthz test**

Append to `tests/test_deploy_config.py`:

```python
class TestHealthzServer:
    def test_healthz_reads_port_from_env(self):
        import inspect

        from frontend import healthz

        src = inspect.getsource(healthz.main)
        assert "HEALTH_CHECK_PORT" in src
        assert "HEALTH_CHECK_HOST" in src

    def test_nginx_has_healthz_route(self):
        content = _read("nginx.conf")
        assert "location = /healthz" in content
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_deploy_config.py::TestHealthzServer -v`
Expected: FAIL — `HEALTH_CHECK_HOST` absent, no `location = /healthz` in nginx.conf.

- [ ] **Step 3: Update frontend/healthz.py**

Replace the `main()` function with:

```python
def main() -> None:
    """Serve /healthz on HEALTH_CHECK_HOST:HEALTH_CHECK_PORT (default 0.0.0.0:9090)."""
    host = os.environ.get("HEALTH_CHECK_HOST", "0.0.0.0")
    port = int(os.environ.get("HEALTH_CHECK_PORT", "9090"))
    server = http.server.HTTPServer((host, port), HealthCheckHandler)
    sys.stdout.write(f"Health check server listening on {host}:{port}\n")
    sys.stdout.flush()
    server.serve_forever()
```

Also replace `do_GET` and add a `_respond` helper so readiness and liveness can be
distinguished. The whole class body becomes:

```python
class HealthCheckHandler(http.server.BaseHTTPRequestHandler):
    """Simple health check endpoint for Docker container health probes."""

    def do_GET(self):
        if self.path == "/healthz":
            self._respond(200, {"status": "ok"})
        elif self.path == "/ready":
            self._respond(200, {"status": "ready"})
        else:
            self._respond(404, {"status": "not_found"})

    def _respond(self, code: int, payload: dict) -> None:
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    def log_message(self, format, *args):
        """Suppress default HTTP server logging."""
        pass
```

- [ ] **Step 4: Update nginx.conf**

Overwrite with:

```nginx
events { worker_connections 1024; }

http {
  limit_req_zone $binary_remote_addr zone=req_limit:10m rate=10r/s;

  upstream backend_upstream { server backend:8000; }
  upstream frontend_upstream { server frontend:8501; }

  server {
    listen 80;
    server_name _;

    location = /healthz {
      access_log off;
      add_header Content-Type application/json always;
      return 200 '{"status":"ok"}';
    }

    location /api/ {
      limit_req zone=req_limit burst=20 nodelay;
      proxy_pass http://backend_upstream;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto $scheme;
      proxy_read_timeout 300s;
    }

    location / {
      limit_req zone=req_limit burst=40 nodelay;
      proxy_pass http://frontend_upstream;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_read_timeout 300s;
      proxy_buffering off;
    }

    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
  }
}
```

`proxy_read_timeout 300s` matters: research synthesis calls the LLM and regularly exceeds the 60s nginx default.

- [ ] **Step 5: Add the missing env vars to .env.example**

Append a new section to `.env.example`:

```bash
# =============================================================================
# Platform-assigned ports (Railway / Docker injects these)
# =============================================================================
PORT=8000                     # Backend bind port (injected by Railway)
HEALTH_CHECK_PORT=9090        # Frontend healthz sidecar port

# =============================================================================
# Frontend -> Backend wiring (required on Streamlit Community Cloud)
# =============================================================================
EQUIPILOT_API_URL=            # e.g. https://your-backend.up.railway.app
EQUIPILOT_HEALTH_URL=         # e.g. https://your-backend.up.railway.app/health
HEALTH_CHECK_HOST=0.0.0.0     # Frontend healthz bind address
```

- [ ] **Step 6: Verify**

Run: `python -m pytest tests/test_deploy_config.py -v`
Expected: all pass.

Run: `python -m pytest tests/ -q`
Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add nginx.conf frontend/healthz.py .env.example tests/test_deploy_config.py
git commit -m "feat: proxy /api to backend, configurable healthz sidecar"
```

---

## Task 8: Extend CI to build and validate the Docker images

The current CI never builds an image, so a broken `Dockerfile` (exactly today's state) merges green.

**Files:**
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: `Dockerfile` stages `production`, `frontend`, `nginx`
- Produces: a `docker` job gated on `lint` + `test`

- [ ] **Step 1: Add the docker job**

Append to `.github/workflows/ci.yml`:

```yaml
  # ============================================================================
  # Job 3: Docker Image Build Validation
  # ============================================================================
  docker:
    name: Build Docker Images
    runs-on: ubuntu-latest
    needs: [lint, test]

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build backend image
        uses: docker/build-push-action@v6
        with:
          context: .
          target: production
          push: false
          tags: equipilot-backend:ci

      - name: Build frontend image
        uses: docker/build-push-action@v6
        with:
          context: .
          target: frontend
          push: false
          tags: equipilot-frontend:ci

      - name: Build nginx image
        uses: docker/build-push-action@v6
        with:
          context: .
          target: nginx
          push: false
          tags: equipilot-nginx:ci

      - name: Validate compose file
        run: docker compose config --quiet
```

- [ ] **Step 2: Add a job-level timeout to every job**

Add under each job's `runs-on:` line:

```yaml
    timeout-minutes: 15
```

- [ ] **Step 3: Verify the workflow parses**

Run: `python -c "import yaml,io; d=yaml.safe_load(io.open('.github/workflows/ci.yml',encoding='utf-8')); print(sorted(d['jobs']))"`
Expected: `['docker', 'lint', 'test']`

- [ ] **Step 4: Confirm locally that all three targets build**

Run: `docker build --target nginx -t equipilot-nginx:local .`
Expected: succeeds.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: build and validate all docker targets"
```

---

## Task 9: Repo hygiene — purge tracked bytecode, the stray file, and the `.streamlit` ignore bug

Findings 14, 15, 16.

**Files:**
- Modify: `.gitignore`
- Delete: 181 tracked `.pyc` files
- Delete: `s -ExecutionPolicy RemoteSigned) ; (& ?c?projectsEquipilot AI.venvScriptsActivate.ps1?)`

**Interfaces:**
- Consumes: nothing
- Produces: clean `git ls-files | grep .pyc` (empty); `.streamlit/config.toml` editable

- [ ] **Step 1: Untrack bytecode**

Run: `git rm -r --cached --quiet "*.pyc"`
Expected: exit 0.

Run: `git ls-files | Select-String -Pattern "\.pyc$" | Measure-Object | Select-Object -ExpandProperty Count`
Expected: `0`

- [ ] **Step 2: Delete the stray root file**

Run: `git rm -- "s -ExecutionPolicy RemoteSigned) ; (& ?c?projectsEquipilot AI.venvScriptsActivate.ps1?)"`
Expected: file removed.

- [ ] **Step 3: Fix the .streamlit ignore rule**

In `.gitignore`, replace:

```gitignore
# -----------------------------
# Streamlit / frontend caches
# -----------------------------
.streamlit/
```

with:

```gitignore
# -----------------------------
# Streamlit (config.toml IS tracked; secrets.toml never is)
# -----------------------------
.streamlit/secrets.toml
.streamlit/*.toml.local
```

- [ ] **Step 4: Verify config.toml is no longer ignored**

Run: `git check-ignore -v --no-index .streamlit/config.toml`
Expected: exit 1 (not ignored), no output.

Run: `git status --short .streamlit`
Expected: clean (file tracked and unmodified).

- [ ] **Step 5: Tighten .dockerignore**

Replace `.dockerignore` with:

```dockerignore
# Keep docker builds small
.git
.github
.gitignore
__pycache__
*.pyc
*.pyo
*.pyd
.env
.venv
venv
dist
build
tests
archive
docs
runtime.txt
*.md
.streamlit/secrets.toml
.pytest_cache
.ruff_cache
.coverage
coverage.xml
```

`.streamlit/config.toml` is intentionally **not** ignored — Task 5's frontend stage copies it, and it carries no secrets.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "chore: untrack bytecode, remove stray file, fix .streamlit ignore rule"
```

---

## Task 10: Add dependency automation and repo governance

Findings 17–18: no Dependabot, no CODEOWNERS, no pre-commit — so pinned deps drift and nothing forces a review.

**Files:**
- Create: `.github/dependabot.yml`
- Create: `.github/CODEOWNERS`
- Create: `.pre-commit-config.yaml`

**Interfaces:**
- Consumes: `requirements.txt`, `requirements-dev.txt`, `.github/workflows/ci.yml`
- Produces: weekly pip/action update PRs; required-review routing; local pre-commit gate

- [ ] **Step 1: Add Dependabot**

Create `.github/dependabot.yml`:

```yaml
version: 2
updates:
  - package-ecosystem: pip
    directory: "/"
    schedule:
      interval: weekly
    open-pull-requests-limit: 5
    labels: [dependencies]
    groups:
      python-minor:
        update-types: [minor, patch]

  - package-ecosystem: github-actions
    directory: "/"
    schedule:
      interval: weekly
    open-pull-requests-limit: 5
    labels: [dependencies, ci]
```

- [ ] **Step 2: Add CODEOWNERS**

Create `.github/CODEOWNERS`:

```
# Default owners for everything
*                       @your-org/equipilot-maintainers

# Deployment-critical paths need explicit review
/Dockerfile            @your-org/equipilot-maintainers
/docker-compose.yml    @your-org/equipilot-maintainers
/nginx.conf            @your-org/equipilot-maintainers
/.github/workflows/    @your-org/equipilot-maintainers
/backend/config.py     @your-org/equipilot-maintainers
```

Replace `@your-org/equipilot-maintainers` with a real team slug before merging — see the manual steps in Task 13.

- [ ] **Step 3: Add pre-commit**

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-added-large-files
        args: ["--maxkb=500"]
      - id: detect-private-key

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
        args: ["--fix"]

  - repo: https://github.com/psf/black
    rev: 24.10.0
    hooks:
      - id: black
```

- [ ] **Step 4: Install and verify the hooks run clean**

Run: `python -m pre_commit install`
Run: `python -m pre_commit run --all-files`
Expected: all hooks `Passed`. If `trailing-whitespace` or `end-of-file-fixer` modify files, stage and commit them, then re-run until clean.

- [ ] **Step 5: Commit**

```bash
git add .github/dependabot.yml .github/CODEOWNERS .pre-commit-config.yaml
git commit -m "chore: add dependabot, codeowners, and pre-commit hooks"
```

---

## Task 11: Reconcile the stale tracking docs

Findings 11, 13, 20 and the obsolete `TODO_TOOL_INTEGRATION.md`. Leaving these unchecked makes the next session redo finished work; the graph integration described in `TODO_TOOL_INTEGRATION.md` is already implemented (`backend/graphs/state.py` has `market_data`/`news`/`execution_metadata`; `graph.py` runs `parallel_tools`; `tests/test_langgraph_market_news_integration.py` covers it).

**Files:**
- Modify: `TODO.md`
- Modify: `TOD0.md`
- Modify: `AUDIT_REPORT.md`
- Delete: `TODO_TOOL_INTEGRATION.md`

**Interfaces:**
- Consumes: findings table at the top of this plan
- Produces: tracking docs that reflect reality

- [ ] **Step 1: Rewrite TODO.md as a resolved log**

Replace the file contents with:

```markdown
# Resolved Deployment TODOs

All items below were closed during the deployment-completion pass.
See `docs/superpowers/plans/2026-10-01-deployment-completion.md`.

- [x] Exactly one Railway start command: `Procfile` deleted; `Dockerfile` `CMD` is authoritative.
- [x] OpenAI client construction is lazy (`backend/services/llm_service.py:_get_client`).
- [x] Startup logging emits `StartupConfig` with PORT, CORS raw value + detected format,
      parsed list, and `openai_api_key_present` (`backend/app.py` lifespan).
- [x] Malformed `CORS_ORIGINS` in production logs ERROR and raises during config parse
      (`backend/config.py:342` `enforce_environment_cors`).
- [x] Full test suite green (see Task 4 for the added contract tests).
```

- [ ] **Step 2: Resolve TOD0.md**

Its second item is obsolete (`_run_graph` already uses `await compiled.ainvoke(...)`, `backend/app.py:470`) and its first item conflicts with `tests/test_production.py:471`. Replace the file with:

```markdown
# Resolved TODOs

- [x] Dockerfile keeps `AS frontend` as a real Streamlit stage (no longer a dead copy).
- [x] `_run_graph()` uses `await compiled.ainvoke(initial_state)` — `asyncio.to_thread`
      is not applicable; the original item was written against a sync `.invoke` call
      that no longer exists.
- [x] `check_status()` calls only `{API_BASE_URL}/api/v1/research/{request_id}`.
- [x] `pytest` green.
- [x] `test_dockerfile_multi_stage` still passes — all three stage names retained.
```

- [ ] **Step 3: Mark AUDIT_REPORT.md resolved**

Prepend to `AUDIT_REPORT.md`:

```markdown
> **Status: RESOLVED.** The duplicate `design_system*.py` files were removed
> (`design_system_ui.py` is the single design system), `sentiment_prompt.py` and
> `research_graph.py` were removed/archived, `requirements-dev.txt` now exists and
> `requirements.txt` is runtime-only, and `backend/core/constants.py` +
> `backend/core/exceptions.py` provide the centralized enum/exception base the report
> flagged as missing. Remaining duplicate-schema and duplicate-service entries below are
> tracked in `docs/superpowers/plans/2026-10-01-followup-refactor.md` (not yet written)
> and are **code-organization debt, not deployment blockers**.
```

- [ ] **Step 4: Delete the completed tool-integration TODO**

Run: `git rm TODO_TOOL_INTEGRATION.md`
Expected: removed.

- [ ] **Step 5: Commit**

```bash
git add TODO.md TOD0.md AUDIT_REPORT.md
git commit -m "docs: reconcile stale deployment tracking files"
```

---

## Task 12: Rewrite the deployment guide as three real runbooks

`docs/deployment.md` currently documents local dev and Docker, but not Railway, not Streamlit Community Cloud, and not the `EQUIPILOT_API_URL` wiring that makes the frontend work in production.

**Files:**
- Modify: `docs/deployment.md`

**Interfaces:**
- Consumes: every contract established in Tasks 1–11
- Produces: the three runbooks the manual steps in Task 13 reference

- [ ] **Step 1: Add the Railway runbook**

Append to `docs/deployment.md`:

````markdown
## Runbook A — Backend on Railway

1. Push the repo to GitHub, then in Railway choose **New Project → Deploy from GitHub repo**.
2. Railway detects the `Dockerfile` automatically. **Do not add a Procfile** — the image
   `CMD` is the single start command.
3. Under **Settings → Variables**, add:

   | Variable | Value |
   |----------|-------|
   | `ENVIRONMENT` | `production` |
   | `OPENAI_API_KEY` | your key |
   | `SECRET_KEY` | `openssl rand -hex 32` |
   | `BACKEND_RELOAD` | `false` |
   | `LOG_LEVEL` | `INFO` |
   | `LOG_FORMAT` | `json` |
   | `CORS_ORIGINS` | your Streamlit URL(s) — see step 4 |

   Do **not** set `PORT`; Railway injects it and `Settings.backend_port` reads it.

4. Set `CORS_ORIGINS` **after** the frontend exists, to its exact URL:

   ```bash
   CORS_ORIGINS=["https://equipilot-frontend.streamlit.app"]
   ```

   Comma-separated also works: `CORS_ORIGINS=https://a.app,https://b.app`.
   If the value is malformed, startup **fails fast** by design. To include both the
   Streamlit URL and the Railway URL, list both origins.

5. Deploy. Watch the startup log for:

   ```json
   {"event": "StartupConfig", "port": 8080, "cors_origins_raw": "[...]",
    "cors_origins_raw_detected_format": "json_array_candidate",
    "cors_origins_parsed": ["https://equipilot-frontend.streamlit.app"],
    "openai_api_key_present": true}
   {"event": "Backend startup complete", "healthy": true, "error_count": 0}
   ```

6. Verify:

   ```bash
   curl -fsS https://<your-domain>/health    # {"status":"healthy", ...}
   curl -fsS https://<your-domain>/ready    # 200 only when no startup errors
   ```

   A `503` from `/ready` means startup errors were recorded — read the deploy log.
````

- [ ] **Step 2: Add the Streamlit Community Cloud runbook**

Append:

````markdown
## Runbook B — Frontend on Streamlit Community Cloud

1. Push the repo to GitHub, then choose **New app → deploy from GitHub**.
2. **Main file path:** `frontend/app.py`
3. **Python version:** set to `3.12` (matches `runtime.txt`).
4. Under **Settings → Secrets**, add:

   | Key | Value |
   |-----|-------|
   | `EQUIPILOT_API_URL` | `https://<your-railway-domain>` (no `/api/v1` — the app adds it) |
   | `EQUIPILOT_HEALTH_URL` | `https://<your-railway-domain>/health` |

   `frontend/app.py` reads only these two plus `HEALTH_CHECK_PORT`. Without
   `EQUIPILOT_API_URL` the dashboard renders but every research call fails, so set it.

5. `.streamlit/config.toml` is committed and Streamlit picks it up automatically.
   `secrets.toml` is gitignored — never commit it.

6. Click **Deploy**. On first load the header status dot stays grey until the backend
   health check succeeds. That is expected while the backend is still cold-starting.

### Cross-origin note

Streamlit Cloud and Railway are different origins, so CORS applies. `CORS_ORIGINS` on
the backend **must** include the exact Streamlit URL, including scheme and no trailing
slash.
````

- [ ] **Step 3: Add the full-Docker runbook**

Append:

````markdown
## Runbook C — Full stack with Docker Compose

```bash
cp .env.example .env      # then fill in OPENAI_API_KEY and SECRET_KEY
docker compose up -d --build
docker compose ps         # all three services should be "healthy"
curl -fsS http://localhost/healthz    # {"status":"ok"}
```

The UI is at `http://localhost` (via nginx). Direct access: frontend `http://localhost:8501`,
backend `http://localhost:8000/docs`.

Tear down:

```bash
docker compose down            # keep images
docker compose down -v --rmi local   # also drop images and volumes
```

### Common failures

| Symptom | Cause | Fix |
|---------|-------|-----|
| backend exits at once | `CORS_ORIGINS` malformed in production | Fix the value; startup fails fast by design |
| frontend container unhealthy | `frontend/healthz.py` not running | Confirm the `CMD` backgrounds it |
| nginx 502 on `/` | frontend not healthy | `docker compose ps`; check `docker compose logs frontend` |
| nginx 502 on `/api/` | backend not healthy | `docker compose logs backend` |
| research times out at ~60s | nginx default read timeout | `proxy_read_timeout 300s` is set in `nginx.conf` |
````

- [ ] **Step 4: Verify no stale statements remain**

Run: `Select-String -Path docs\deployment.md -Pattern "Procfile"`
Expected: matches only the Runbook A warning that says **not** to add one.

- [ ] **Step 5: Commit**

```bash
git add docs/deployment.md
git commit -m "docs: add Railway, Streamlit Cloud, and full-Docker runbooks"
```

---

## Task 13: Final verification gate

Nothing ships until all of this passes from a clean state.

**Files:** none modified — verification only.

- [ ] **Step 1: Clean-tree full test run**

Run: `python -m pytest tests/ -q`
Expected: all pass; count ≥ 212 + the contract tests added in Task 4.

- [ ] **Step 2: Lint and format gates**

Run: `python -m ruff check backend/ frontend/ tests/`
Expected: `All checks passed!`

Run: `python -m black --check backend/ frontend/ tests/`
Expected: all files unchanged.

- [ ] **Step 3: Pre-commit gate**

Run: `python -m pre_commit run --all-files`
Expected: all hooks `Passed`.

- [ ] **Step 4: Full image build, all three targets**

Run: `docker build --target production -t equipilot-backend:local .`
Run: `docker build --target frontend -t equipilot-frontend:local .`
Run: `docker build --target nginx -t equipilot-nginx:local .`
Expected: all three succeed.

- [ ] **Step 5: Compose config validation**

Run: `docker compose config --quiet`
Expected: exit 0.

- [ ] **Step 6: Local end-to-end smoke**

```powershell
docker compose up -d --build
Start-Sleep -Seconds 45
docker compose ps
(Invoke-WebRequest http://localhost/healthz).Content
(Invoke-WebRequest http://localhost:9090/healthz).Content
(Invoke-WebRequest http://localhost:8000/health).Content
docker compose down
```
Expected: nginx healthz `{"status":"ok"}`, frontend healthz `{"status":"ok"}`, backend health `"status":"healthy"` with `"startup_errors": []`.

- [ ] **Step 7: Confirm no tracked bytecode and no stray files**

Run: `git ls-files | Select-String -Pattern "\.pyc$" | Measure-Object | Select-Object -ExpandProperty Count`
Expected: `0`

Run: `git status --short`
Expected: clean (no uncommitted work left behind).

- [ ] **Step 8: Push and watch CI go green**

```bash
git push origin main
```
Expected: `lint` → `test` → `docker` all pass. A red `lint` means Tasks 2/3 were incomplete.

---

# MANUAL WORK — Requires Human Action

These cannot be automated from inside the repo. Budget roughly 60–90 minutes.

## M1. Create a GitHub personal access token (if not already done)

1. GitHub → Settings → Developer settings → Personal access tokens → **Fine-grained tokens**.
2. Permissions: `Contents: read-and-write`, `Actions: read-and-write`, `Pull requests: read-and-write`.
3. Generate, copy the token once.

## M2. Create a GitHub team and wire CODEOWNERS

1. GitHub org → **Teams** → **New team** → name it e.g. `equipilot-maintainers`.
2. Add yourself as a member.
3. Edit `.github/CODEOWNERS` (created in Task 10) and replace every
   `@your-org/equipilot-maintainers` with `@<your-org>/equipilot-maintainers`.
4. Enable branch protection on `main`: Settings → Branches → **Add rule** →
   require status checks `lint`, `test`, `docker`.

## M3. Create the OpenAI API key

1. https://platform.openai.com/api-keys → **Create new secret key**.
2. Copy it once — it is shown only once.
3. It becomes `OPENAI_API_KEY` in Railway (Task 12 Runbook A).

Budget note: `gpt-4o` for synthesis and `gpt-4o-mini` for routing/sentiment. Sentiment
runs per article batch, so mini-only routing keeps cost down. `OPENAI_MODEL` and
`OPENAI_MODEL_MINI` are already overridable in `.env.example`.

## M4. Create the News API key (optional)

1. https://newsapi.org/register → free key, 100 requests/day on the free tier.
2. Set `NEWS_API_KEY` and `NEWS_API_PROVIDER=newsapi` in Railway.
3.    Optional: raise the plan, or switch `NEWS_API_PROVIDER` to `alphavantage` or
   `finnhub` (both supported in `backend/config.py:251` `validate_news_provider`).
   With no key the app falls back to yfinance-derived sources and logs a warning.

## M5. Generate the production SECRET_KEY

Run in PowerShell:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Set the output as `SECRET_KEY` in Railway. It must never be committed or reused
across environments.

## M6. Create the Railway project and deploy the backend

1. https://railway.app → **New Project → Deploy from GitHub repo** → pick this repo.
2. Confirm Railway detected the `Dockerfile` (Settings → Build → Dockerfile). If it
   created a Nixpacks build instead, delete the service and redeploy from the Dockerfile.
3. Add the variables from Task 12 Runbook A step 3.
4. Click **Deploy**. Watch for the `StartupConfig` and `Backend startup complete` lines.
5. Settings → Networking → **Generate Domain**. Copy the URL — you need it for M7.
6. Verify:
   ```powershell
   (Invoke-WebRequest "https://<your-domain>/health").Content
   ```
   Expected: `"status": "healthy"`.
7. Open `https://<your-domain>/docs` — the Swagger UI must render.

## M7. Set CORS_ORIGINS to the real frontend URL

This is circular — the Streamlit URL does not exist until M8 — so deploy the frontend
first with `CORS_ORIGINS` unset (CORS stays deny-by-default, which is correct), then
come back:

1. Copy the Streamlit URL, e.g. `https://equipilot-frontend.streamlit.app`.
2. Railway → your service → **Variables** → set
   `CORS_ORIGINS=["https://equipilot-frontend.streamlit.app"]`.
3. Save. Railway redeploys automatically.
4. Confirm the new deploy log shows:
   ```json
   "cors_origins_raw_detected_format": "json_array_candidate",
   "cors_origins_parsed": ["https://equipilot-frontend.streamlit.app"]
   ```
5. If instead you see `"cors_origins_parsed": []` with an ERROR, the value did not
   parse. Check for a stray quote, a trailing comma inside the JSON array, or shell
   quoting that ate the brackets.

## M8. Deploy the frontend to Streamlit Community Cloud

1. https://share.streamlit.io → **New app** → **Deploy from GitHub** → pick this repo.
2. **Main file path:** `frontend/app.py`
3. **Python version:** `3.12`
4. **Deploy!** — the first build takes 3–5 minutes while it installs `requirements.txt`.
5. Note the assigned URL, e.g. `https://equipilot-frontend.streamlit.app`.
6. Settings → **Secrets** → add `EQUIPILOT_API_URL=https://<railway-domain>` and
   `EQUIPILOT_HEALTH_URL=https://<railway-domain>/health`.
7. Rerun the app. The header status dot should turn green.
8. Then complete M7 (CORS) and redeploy the backend.

## M9. Run a full production smoke test

1. Open the Streamlit URL. Confirm: no exception traceback, disclaimer bar present,
   sidebar renders, status dot green.
2. Submit a research query with a real ticker, e.g. "Analyze Apple's fundamentals and
   recent news". Confirm the progress tracker advances and a report renders with citations.
3. Toggle "show tool data" in the sidebar — confirm market data and news panels populate.
4. Submit a nonsense ticker, e.g. "Analyze ZZZZZ". Confirm a graceful entity-resolution
   error, not a 500.
5. Confirm Railway logs show structured JSON with `request_id` on both the request and
   response lines.

## M10. Set up uptime monitoring

Point an external monitor at `https://<railway-domain>/ready`.

- Railway's own healthcheck uses the Dockerfile `HEALTHCHECK`.
- A free external option: UptimeRobot or Better Stack, 60s interval, alert on
  non-2xx for 3 consecutive checks.
- Alert on `/ready` returning 503 as well — that means the app is up but degraded.

## M11. Document the deployment in the README

Add a short "Live deployment" section to `README.md` with:

- The Railway backend URL
- The Streamlit frontend URL
- A pointer to `docs/deployment.md` for the runbooks
- A note that this is an informational research assistant, not investment advice
  (per `CLAUDE.md`'s stated project boundary)

---

## Execution Order

```
Task 1  CI dev-deps        ─┐
Task 2  Ruff backlog        ├─ must land before CI can be green
Task 3  Black formatting   ─┘
Task 4  Contract tests      (written failing on purpose)
Task 5  Dockerfile          ─┐
Task 6  Compose             ├─ makes Task 4's Docker tests pass
Task 7  nginx + healthz     ─┘
Task 8  CI docker job       (validates Tasks 5-7 in CI)
Task 9  Repo hygiene        (independent, safe to parallelize)
Task 10 Dependabot/hooks    (independent)
Task 11 Docs reconciliation (after 1-9 land)
Task 12 Runbooks            (after 1-11 land)
Task 13 Final gate          (everything)
Manual M1-M11               (after Task 13)
```

Tasks 9 and 10 have no dependencies and can run in parallel with 5–8.
