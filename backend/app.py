# EquiPilot AI - FastAPI Application Entry Point
# Main backend application with routing, middleware, and lifecycle management

import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import settings
from backend.core.constants import APP_NAME, APP_VERSION, AppStatus, ExecutionStatus
from backend.exceptions.handlers import register_exception_handlers
from backend.graphs.graph import create_first_graph
from backend.middleware.production import (
    add_production_middleware,
    metrics,
)
from backend.schemas.research import ResearchRequest, ResearchResponse, ResearchStatus
from backend.utils.logger import get_logger, setup_logging

# Configure structured logging
setup_logging()

logger = get_logger(__name__)

# Global graph instance (initialized on startup)
research_graph = None


async def validate_environment() -> list:
    """Validate environment configuration on startup.

    Returns:
        List of error messages. Empty list means all validations passed.
    """
    errors = []

    # Validate settings configuration
    try:
        warnings = settings.validate_required_settings()
        for warning in warnings:
            logger.warning("Configuration warning", detail=warning)
    except Exception as e:
        errors.append(f"Configuration validation: {e!s}")
        logger.error("Configuration validation failed", error=str(e))

    # Validate critical environment variables
    if not settings.openai_api_key:
        errors.append("OPENAI_API_KEY is not set - LLM features unavailable")

    if not settings.news_api_key:
        logger.info("NEWS_API_KEY not set - news features will use fallback sources")

    # Validate port availability (basic check)
    if settings.backend_port < 1024 and not settings.is_development:
        errors.append(
            f"Backend port {settings.backend_port} requires root privileges in production"
        )

    return errors


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup/shutdown."""
    global research_graph  # Declare once at the top for all assignments

    logger.info(
        "Starting EquiPilot AI backend",
        version=APP_VERSION,
        log_level=settings.log_level,
        log_format=settings.log_format,
    )

    startup_errors = []

    # Validate environment
    try:
        startup_errors.extend(await validate_environment())
    except Exception as e:
        startup_errors.append(f"Environment validation: {e!s}")

    # Initialize LangGraph research workflow
    try:
        research_graph = create_first_graph()
        logger.info("Research graph initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize research graph", error=str(e))
        startup_errors.append(f"Graph initialization: {e!s}")

    if startup_errors:
        logger.error("Startup completed with errors", errors=startup_errors)
        app.state.startup_errors = startup_errors
    else:
        app.state.startup_errors = []

    logger.info(
        "Backend startup complete",
        healthy=not bool(startup_errors),
        error_count=len(startup_errors),
    )

    yield

    # Graceful shutdown
    logger.info("Initiating graceful shutdown")
    research_graph = None
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        Configured FastAPI application instance
    """

    app = FastAPI(
        title=APP_NAME,
        description="Agentic Equity Research Assistant API",
        version=APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register all production middleware (rate limiting, security headers, metrics)
    add_production_middleware(app)

    # Register all exception handlers (global, HTTP, domain-specific)
    register_exception_handlers(app)

    # Request ID middleware
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        request_id = getattr(request.state, "request_id", "unknown")
        logger.info(
            "Incoming request",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            client=request.client.host if request.client else None,
        )
        try:
            response = await call_next(request)
            logger.info(
                "Request completed",
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
            )
            return response
        except Exception as e:
            logger.error(
                "Request failed",
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                error=str(e),
            )
            raise

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint for load balancers and monitoring.

        Returns application health status including service availability
        and any startup errors.
        """
        startup_errors = getattr(app.state, "startup_errors", [])
        return {
            "status": AppStatus.HEALTHY if not startup_errors else AppStatus.DEGRADED,
            "version": APP_VERSION,
            "services": {
                "openai": settings.has_openai,
                "news_api": settings.has_news_api,
            },
            "errors": startup_errors,
        }

    # Readiness endpoint
    @app.get("/ready", tags=["Health"])
    async def readiness_check():
        """Readiness endpoint for orchestration systems (Kubernetes, Docker).

        Returns 200 when the application is ready to serve traffic,
        503 when startup errors exist.
        """
        startup_errors = getattr(app.state, "startup_errors", [])
        if startup_errors:
            return JSONResponse(
                status_code=503,
                content={
                    "status": AppStatus.NOT_READY,
                    "errors": startup_errors,
                },
            )
        return {
            "status": AppStatus.READY,
            "version": APP_VERSION,
        }

    # Version endpoint
    @app.get("/version", tags=["Health"])
    async def version():
        """Version endpoint for deployment verification."""
        return {
            "name": APP_NAME,
            "version": APP_VERSION,
            "api_version": settings.api_prefix,
        }

    # Metrics endpoint
    @app.get("/metrics", tags=["Health"])
    async def get_metrics():
        """Metrics endpoint for monitoring systems.

        Returns request counts, response times, and active request count.
        """
        avg_duration = 0
        if metrics["request_duration"]:
            avg_duration = (
                sum(metrics["request_duration"])
                / len(metrics["request_duration"])
                * 1000
            )

        return {
            "requests_total": dict(metrics["requests_total"]),
            "requests_by_status": dict(metrics["requests_by_status"]),
            "average_response_time_ms": round(avg_duration, 2),
            "active_requests": metrics["active_requests"],
        }

    # API Routes
    @app.post(
        f"{settings.api_prefix}/research",
        response_model=ResearchResponse,
        tags=["Research"],
        summary="Submit a research query",
        description="Submit an equity research query to be processed by the agentic workflow.",
    )
    async def submit_research(request: ResearchRequest) -> ResearchResponse:
        """Submit a new research request."""
        logger.info("Research request received", query=request.query, tickers=request.tickers)

        # TODO: Implement actual research workflow execution
        # For now, return a placeholder response
        return ResearchResponse(
            request_id=str(uuid.uuid4()),
            status=ResearchStatus.PENDING,
            query=request.query,
            tickers=request.tickers or [],
            message="Research request accepted. Implementation pending.",
        )

    @app.get(
        f"{settings.api_prefix}/research/{{request_id}}",
        response_model=ResearchResponse,
        tags=["Research"],
        summary="Get research results",
        description="Retrieve the results of a previously submitted research request.",
    )
    async def get_research(request_id: str) -> ResearchResponse:
        """Get research results by request ID."""
        logger.info("Research results requested", request_id=request_id)

        # TODO: Implement actual result retrieval
        return ResearchResponse(
            request_id=request_id,
            status=ResearchStatus.NOT_FOUND,
            query="",
            tickers=[],
            message="Research request not found. Implementation pending.",
        )

    @app.get(
        f"{settings.api_prefix}/research/{{request_id}}/status",
        response_model=ResearchStatus,
        tags=["Research"],
        summary="Get research status",
        description="Check the current status of a research request.",
    )
    async def get_research_status(request_id: str) -> ResearchStatus:
        """Get research status by request ID."""
        # TODO: Implement actual status checking
        return ResearchStatus.NOT_FOUND

    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.app:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.backend_reload,
        log_level=settings.log_level.lower(),
    )