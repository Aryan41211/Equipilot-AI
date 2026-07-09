# EquiPilot AI - FastAPI Application Entry Point
# Main backend application with routing, middleware, and lifecycle management

import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import settings
from backend.core.constants import APP_NAME, APP_VERSION, AppStatus, ExecutionStatus
from backend.exceptions.handlers import register_exception_handlers
from backend.graphs.graph import create_first_graph, create_initial_state
from backend.middleware.production import (
    add_production_middleware,
    metrics,
)
from backend.schemas.research import ResearchRequest, ResearchResponse, ResearchStatus
from backend.utils.logger import get_logger, setup_logging

# Configure structured logging
setup_logging()

logger = get_logger(__name__)

logger.info("DIAG: backend.app imported (setup_logging done)")

# Global graph instance (initialized on startup)
research_graph = None

# In-memory execution store for Phase 2 runtime repair (per-process)
# Maps request_id -> GraphState (and derived response payload)
_research_store: dict[str, dict[str, Any]] = {}

# Server-side idempotency map (per-process, in-memory TTL)
# Key: fingerprint derived from incoming request (query + tickers)
# Value: dict with timestamps and associated request_id/state
_idempotency_store: dict[str, dict[str, Any]] = {}


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

    # Required deterministic startup log line (deployment audit).
    import os

    raw_cors = os.environ.get("CORS_ORIGINS")
    if raw_cors is None:
        raw_cors = os.environ.get("cors_origins")

    raw_cors_str = (raw_cors or "").strip() if raw_cors is not None else None
    if raw_cors_str is None or raw_cors_str == "":
        cors_detected_format = "empty_or_missing"
    elif raw_cors_str.startswith("["):
        cors_detected_format = "json_array_candidate"
    elif "," in raw_cors_str:
        cors_detected_format = "comma_separated"
    else:
        cors_detected_format = "single_value"

    logger.info(
        "StartupConfig",
        port=settings.backend_port,
        host=settings.backend_host,
        cors_origins_raw=raw_cors_str,
        cors_origins_raw_detected_format=cors_detected_format,
        cors_origins_parsed=settings.cors_origins,
        openai_api_key_present=bool(settings.openai_api_key),
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
        """Submit a new research request and start the LangGraph workflow."""
        logger.info("Research request received", query=request.query, tickers=request.tickers)

        # ----------------------------
        # Server-side idempotency check (in-memory TTL)
        # ----------------------------
        import hashlib
        import os as _os
        import time as _time

        enable_idempotency = _os.environ.get("ENABLE_IDEMPOTENCY_CHECK", "true").strip().lower() in (
            "1",
            "true",
            "yes",
            "y",
            "on",
        )
        idempotency_ttl_seconds = int(_os.environ.get("IDEMPOTENCY_TTL_SECONDS", "60"))

        fingerprint: str | None = None
        if enable_idempotency:
            # Derive from query + tickers (as requested)
            tickers = request.tickers or []
            raw = f"{(request.query or '').strip()}|{','.join(tickers)}"
            fingerprint = hashlib.sha256(raw.encode("utf-8")).hexdigest()

            now = _time.time()
            entry = _idempotency_store.get(fingerprint) if fingerprint else None
            if entry:
                created_at_ts = float(entry.get("created_at_ts", 0) or 0)
                age_s = now - created_at_ts
                job_rid = entry.get("request_id")
                job_completed = bool(entry.get("completed", False))

                if age_s <= idempotency_ttl_seconds and job_rid and job_completed:
                    # Completed already: return the existing result payload from store
                    state = _research_store.get(job_rid, {}).get("state")
                    if state is not None:
                        graph_status = state.get("status")
                        # Map GraphState.status -> ResearchStatus
                        if graph_status == "success":
                            r_status = ResearchStatus.COMPLETED
                        elif graph_status == "failed":
                            r_status = ResearchStatus.FAILED
                        else:
                            r_status = ResearchStatus.IN_PROGRESS

                        report = state.get("report") or None
                        t = state.get("ticker")
                        tickers_out = [t] if t else []

                        # execution_metadata/traces for frontend
                        execution_metadata = state.get("execution_metadata", {}) or {}
                        traces = execution_metadata.get("traces", []) or []
                        current_step = "router"
                        if traces:
                            last = traces[-1]
                            current_step = last.get("node_name") or last.get("step") or "router"
                        execution_metadata = {
                            **execution_metadata,
                            "current_step": current_step,
                            "traces": traces,
                        }

                        message = (
                            "Research completed."
                            if r_status == ResearchStatus.COMPLETED
                            else (
                                "Research in progress."
                                if r_status == ResearchStatus.IN_PROGRESS
                                else "Research failed."
                            )
                        )

                        return ResearchResponse(
                            request_id=job_rid,
                            status=r_status,
                            query=request.query,
                            tickers=tickers_out,
                            report=report,
                            sections=None,
                            citations=None,
                            current_step=current_step,
                            execution_metadata=execution_metadata,
                            message=message,
                        )

                # If still within TTL, treat as in-flight: return the existing request_id,
                # and a PENDING response shell (no new task launched).
                if age_s <= idempotency_ttl_seconds and job_rid:
                    now_state = _research_store.get(job_rid, {}).get("state", {}) or {}
                    execution_metadata = now_state.get("execution_metadata", {}) or {}
                    traces = execution_metadata.get("traces", []) or []
                    current_step = "router"
                    if traces:
                        last = traces[-1]
                        current_step = last.get("node_name") or last.get("step") or "router"
                    execution_metadata = {
                        **execution_metadata,
                        "current_step": current_step,
                        "traces": traces,
                    }

                    return ResearchResponse(
                        request_id=job_rid,
                        status=ResearchStatus.PENDING,
                        query=request.query,
                        tickers=request.tickers or [],
                        current_step=current_step,
                        execution_metadata={
                            "current_step": current_step,
                            "traces": traces,
                        },
                        message="Research request already submitted; returning existing job.",
                    )

        # Build request_id + initial state for the graph
        rid = str(uuid.uuid4())
        initial_state = create_initial_state(request.query)

        # Populate ticker hint into graph state if provided
        if request.tickers and len(request.tickers) > 0:
            # GraphState expects `ticker`, but router extracts ticker from query.
            # Provide the first ticker as a hint.
            initial_state = {**initial_state, "ticker": request.tickers[0]}

        # Store initial record
        _research_store[rid] = {
            "state": initial_state,
            "created_at": datetime.utcnow().isoformat(),
            "completed": False,
        }

        # Store idempotency mapping entry (if enabled)
        if enable_idempotency and fingerprint:
            _idempotency_store[fingerprint] = {
                "request_id": rid,
                "created_at_ts": _time.time(),
                "completed": False,
            }

        async def _run_graph() -> None:
            try:
                current_state = _research_store.get(rid, {}).get("state", initial_state)
                _research_store[rid]["state"] = {
                    **current_state,
                    "status": "in_progress",
                }

                # Execute the compiled graph synchronously; we store the latest state
                # after each node execution is not streamed here, so we run fully.
                compiled = research_graph
                if compiled is None:
                    raise RuntimeError("Research graph not initialized")

                # Use async invocation so LangGraph can correctly execute async nodes/runnables
                final_state = await compiled.ainvoke(initial_state)

                # Ensure timing metadata exists and emit a single structured completion log
                execution_metadata = final_state.get("execution_metadata", {}) or {}
                traces = execution_metadata.get("traces", []) or []
                total_ms = execution_metadata.get("execution_time_ms")
                if total_ms is None and traces:
                    total_ms = sum((t.get("duration_ms", 0) or 0) for t in traces if isinstance(t, dict))

                per_node = [
                    {
                        "node": t.get("node_name") or t.get("step"),
                        "duration_ms": t.get("duration_ms"),
                        "ok": t.get("success"),
                    }
                    for t in traces
                    if isinstance(t, dict)
                ]

                logger.info(
                    "Research request completed",
                    request_id=rid,
                    status=final_state.get("status"),
                    total_duration_ms=total_ms,
                    per_node_durations=per_node,
                )

                # Update store with final state
                _research_store[rid]["state"] = final_state
                _research_store[rid]["completed"] = True

                # Mark idempotency mapping as completed (if enabled)
                if enable_idempotency and fingerprint:
                    existing = _idempotency_store.get(fingerprint)
                    if existing is not None:
                        existing["completed"] = True
            except Exception as e:
                # Store failure in state
                state = _research_store.get(rid, {}).get("state", initial_state)
                state = {**state, "status": "failed", "errors": [str(e)]}
                _research_store[rid]["state"] = state
                _research_store[rid]["completed"] = True

                # Mark idempotency mapping as completed (even on failure)
                if enable_idempotency and fingerprint:
                    existing = _idempotency_store.get(fingerprint)
                    if existing is not None:
                        existing["completed"] = True

                logger.exception("Graph execution failed", request_id=rid, error=str(e))

        # Launch background task (FastAPI will keep it running in the same process)
        import asyncio

        asyncio.create_task(_run_graph())

        return ResearchResponse(
            request_id=rid,
            status=ResearchStatus.PENDING,
            query=request.query,
            tickers=request.tickers or [],
            current_step="router",
            execution_metadata={
                "current_step": "router",
                "traces": [],
            },
            message="Research request accepted.",
        )

    @app.get(
        f"{settings.api_prefix}/research/{{request_id}}",
        response_model=ResearchResponse,
        tags=["Research"],
        summary="Get research results",
        description="Retrieve the results of a previously submitted research request.",
    )
    async def get_research(request_id: str) -> ResearchResponse:
        """Get research results by request ID (in-memory)."""
        logger.info("Research results requested", request_id=request_id)

        record = _research_store.get(request_id)
        if not record:
            return ResearchResponse(
                request_id=request_id,
                status=ResearchStatus.NOT_FOUND,
                query="",
                tickers=[],
                message="Research request not found.",
                current_step=None,
                execution_metadata=None,
            )

        state: Any = record.get("state") or {}
        completed = bool(record.get("completed"))

        # Map GraphState.status -> ResearchStatus
        graph_status = state.get("status")
        if completed and graph_status == "success":
            r_status = ResearchStatus.COMPLETED
        elif completed and graph_status == "failed":
            r_status = ResearchStatus.FAILED
        else:
            r_status = ResearchStatus.IN_PROGRESS if graph_status in ("in_progress", "pending", None) else ResearchStatus.IN_PROGRESS

        current_step = "router"
        execution_metadata: dict[str, Any] = {}
        traces = []
        execution_metadata = state.get("execution_metadata", {}) or {}
        traces = execution_metadata.get("traces", []) or []
        if traces:
            # last trace is the latest completed node
            last = traces[-1]
            current_step = last.get("node_name") or last.get("step") or "router"
        execution_metadata = {
            **execution_metadata,
            "current_step": current_step,
            "traces": traces,
        }

        # Build frontend-compatible fields
        report = state.get("report") or None
        tickers = []
        # GraphState has `ticker` singular; frontend expects list
        t = state.get("ticker")
        if t:
            tickers = [t]

        message = "Research completed." if r_status == ResearchStatus.COMPLETED else (
            "Research in progress." if r_status == ResearchStatus.IN_PROGRESS else "Research failed."
        )

        return ResearchResponse(
            request_id=request_id,
            status=r_status,
            query=state.get("user_query", ""),
            tickers=tickers,
            report=report,
            sections=None,
            citations=None,
            current_step=current_step,
            execution_metadata=execution_metadata,
            message=message,
        )

    @app.get(
        f"{settings.api_prefix}/research/{{request_id}}/status",
        response_model=ResearchStatus,
        tags=["Research"],
        summary="Get research status",
        description="Check the current status of a research request.",
    )
    async def get_research_status(request_id: str) -> ResearchStatus:
        """Get research status by request ID (in-memory)."""
        record = _research_store.get(request_id)
        if not record:
            return ResearchStatus.NOT_FOUND

        state: Any = record.get("state") or {}
        completed = bool(record.get("completed"))

        graph_status = state.get("status")
        if completed and graph_status == "success":
            return ResearchStatus.COMPLETED
        if completed and graph_status == "failed":
            return ResearchStatus.FAILED

        # Map in-progress graph states
        if graph_status in ("in_progress", "pending", None, "success", "failed"):
            # If graph_status is success/failed but not completed, treat as in-progress.
            return ResearchStatus.IN_PROGRESS

        # Fallback: treat unknown as in-progress to keep UI polling stable.
        return ResearchStatus.IN_PROGRESS

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