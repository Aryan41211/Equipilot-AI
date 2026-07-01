# EquiPilot AI - Production Middleware
# Rate limiting, security headers, and metrics collection

import time
from collections import defaultdict
from collections.abc import Callable

from fastapi import FastAPI, Request, Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Metrics storage (in-memory for simplicity, use Redis in production)
metrics = {
    "requests_total": defaultdict(int),
    "requests_by_status": defaultdict(int),
    "request_duration": [],
    "active_requests": 0,
}


def get_rate_limiter() -> Limiter:
    """Create and configure rate limiter."""
    return Limiter(key_func=get_remote_address)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response


class MetricsMiddleware(BaseHTTPMiddleware):
    """Collect request metrics for monitoring."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        metrics["active_requests"] += 1
        start_time = time.time()

        response = await call_next(request)

        duration = time.time() - start_time
        path = request.url.path
        method = request.method

        metrics["requests_total"][path] += 1
        metrics["requests_by_status"][response.status_code] += 1
        metrics["request_duration"].append(duration)

        # Keep only last 1000 request durations
        if len(metrics["request_duration"]) > 1000:
            metrics["request_duration"] = metrics["request_duration"][-1000:]

        metrics["active_requests"] -= 1

        logger.info(
            "Request metrics",
            method=method,
            path=path,
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2),
        )

        return response


def add_production_middleware(app: FastAPI) -> None:
    """Add all production middleware to the app.

    Registers rate limiting, security headers, and metrics collection
    middleware on the FastAPI application.

    Args:
        app: The FastAPI application instance
    """
    from slowapi import _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded

    # Rate limiter
    rate_limiter = get_rate_limiter()
    app.state.limiter = rate_limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # Metrics collection
    app.add_middleware(MetricsMiddleware)

    logger.info(
        "Production middleware registered",
        rate_limiting_enabled=True,
        security_headers_enabled=True,
        metrics_enabled=True,
    )
