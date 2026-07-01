# EquiPilot AI - Docker Configuration
# Production-grade containerization with multi-stage builds

# =============================================================================
# Stage 1: Base - Install system and Python dependencies
# =============================================================================
FROM python:3.12-slim AS base

# Set Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Stage 2: Production - Minimal runtime image
# =============================================================================
FROM python:3.12-slim AS production

# Set Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_VERSION=0.1.0

# Create non-root user
RUN groupadd -r appgroup && \
    useradd -r -g appgroup -m -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appgroup /app

WORKDIR /app

# Copy installed packages from base stage
COPY --from=base /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=base /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appgroup backend/ ./backend/

# Switch to non-root user
USER appuser

# Health check with retry logic and proper endpoint
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; import json; resp = urllib.request.urlopen('http://localhost:8000/health'); data = json.loads(resp.read()); assert data.get('status') in ('healthy', 'degraded'), f'Health check failed: {data}'" || exit 1

EXPOSE 8000

# Default command - backend only with production settings
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--loop", "uvloop", "--http", "httptools"]

# =============================================================================
# Stage 3: Frontend - Streamlit frontend
# =============================================================================
FROM production AS frontend

# Copy frontend code
COPY --chown=appuser:appgroup frontend/ ./frontend/

EXPOSE 8501

# Health check for frontend
HEALTHCHECK --interval=15s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; resp = urllib.request.urlopen('http://localhost:8501/healthz'); assert resp.status == 200, f'Frontend health check failed: {resp.status}'" || exit 1

CMD ["streamlit", "run", "frontend/app.py", "--server.port", "8501", "--server.address", "0.0.0.0", "--server.headless", "true"]

# =============================================================================
# Stage 4: Development - Hot-reload for both backend and frontend
# =============================================================================
FROM base AS development

# Install development dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application code
COPY --chown=appuser:appgroup backend/ ./backend/
COPY --chown=appuser:appgroup frontend/ ./frontend/

# Create non-root user for development
RUN groupadd -r appgroup && \
    useradd -r -g appgroup -m -u 1000 appuser && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000 8501

CMD ["sh", "-c", "uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload & streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true"]