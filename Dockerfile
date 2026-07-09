# syntax=docker/dockerfile:1

FROM python:3.12-slim AS base
WORKDIR /app

FROM base AS production
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend /app/backend
COPY frontend /app/frontend

# Final runtime stage
FROM production AS frontend
WORKDIR /app
COPY frontend /app/frontend

# Create non-root user
RUN useradd -m -u 10001 appuser
USER appuser

# Healthcheck instruction required by tests
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import requests,os; url=os.getenv('EQUIPILOT_HEALTH_URL','http://localhost:8000/health'); requests.get(url,timeout=3).raise_for_status()"

CMD ["python", "-m", "backend.app"]
