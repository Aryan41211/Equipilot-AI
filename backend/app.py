# EquiPilot AI - FastAPI Application Entry Point
# Main backend application with routing, middleware, and lifecycle management

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from backend.config import settings, get_settings
from backend.schemas.research import ResearchRequest, ResearchResponse, ResearchStatus
from backend.graphs.research_graph import create_research_graph

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if settings.log_format == "json" else structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Global graph instance (initialized on startup)
research_graph = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup/shutdown."""
    global research_graph

    logger.info("Starting EquiPilot AI backend", version="0.1.0")

    # Initialize LangGraph research workflow
    try:
        research_graph = create_research_graph()
        logger.info("Research graph initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize research graph", error=str(e))
        raise

    # Validate critical configuration
    if not settings.has_openai:
        logger.warning("OpenAI API key not configured - LLM features will not work")

    if not settings.has_news_api:
        logger.warning("News API key not configured - news features will not work")

    logger.info("Backend startup complete")

    yield

    # Shutdown
    logger.info("Shutting down EquiPilot AI backend")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""

    app = FastAPI(
        title="EquiPilot AI",
        description="Agentic Equity Research Assistant API",
        version="0.1.0",
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

    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.info(
            "Incoming request",
            method=request.method,
            url=str(request.url),
            client=request.client.host if request.client else None,
        )
        response = await call_next(request)
        logger.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
        )
        return response

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(
            "Unhandled exception",
            path=request.url.path,
            error=str(exc),
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "error": str(exc)},
        )

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint for load balancers and monitoring."""
        return {
            "status": "healthy",
            "version": "0.1.0",
            "services": {
                "openai": settings.has_openai,
                "news_api": settings.has_news_api,
            },
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
            request_id="placeholder-id",
            status=ResearchStatus.PENDING,
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