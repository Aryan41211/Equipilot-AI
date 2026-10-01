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

ENV HEALTH_CHECK_PORT=9090

RUN useradd -m -u 10001 appuser \
    && mkdir -p /home/appuser/.streamlit \
    && chown -R appuser:appuser /home/appuser
USER appuser

EXPOSE 8501 9090

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen('http://localhost:'+os.getenv('HEALTH_CHECK_PORT','9090')+'/healthz',timeout=3)"

# Streamlit needs $PORT; run the healthz sidecar in the same container.
CMD ["sh", "-c", "python frontend/healthz.py & exec streamlit run frontend/app.py --server.port=${PORT:-8501} --server.address=0.0.0.0 --server.headless=true"]

# ---------- nginx reverse proxy ----------
FROM nginx:1.27-alpine AS nginx
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://127.0.0.1/healthz || exit 1
