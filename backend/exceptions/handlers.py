# EquiPilot AI - Centralized Exception Handlers
# Production-grade error handling with structured logging

from typing import Union

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# HTTP status codes for domain exceptions
HTTP_ENTITY_NOT_FOUND = 404
HTTP_AMBIGUOUS_ENTITY = 409
HTTP_SENTIMENT_TIMEOUT = 504
HTTP_SYNTHESIS_TIMEOUT = 504
HTTP_VALIDATION_ERROR = 422
HTTP_RATE_LIMITED = 429


def get_request_id(request: Request) -> str:
    """Safely extract request ID from request state."""
    return getattr(request.state, "request_id", "unknown")


def error_response(
    status_code: int,
    detail: str,
    request_id: str,
    error_type: str = "internal_error",
) -> JSONResponse:
    """Create a standardized error response.

    Args:
        status_code: HTTP status code
        detail: Human-readable error description
        request_id: Unique request identifier
        error_type: Machine-readable error type identifier

    Returns:
        JSONResponse with standard error envelope
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "detail": detail,
            "request_id": request_id,
            "error_type": error_type,
        },
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions with structured logging."""
    request_id = get_request_id(request)
    logger.error(
        "Unhandled exception",
        request_id=request_id,
        path=request.url.path,
        method=request.method,
        error=str(exc),
        error_type=type(exc).__name__,
        exc_info=True,
    )

    error_detail = str(exc) if settings.is_development else "Internal server error"

    return error_response(
        status_code=500,
        detail=error_detail,
        request_id=request_id,
        error_type="internal_error",
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTPException with structured logging."""
    request_id = get_request_id(request)

    if exc.status_code >= 500:
        logger.error(
            "HTTP server error",
            request_id=request_id,
            path=request.url.path,
            status_code=exc.status_code,
            detail=str(exc.detail),
        )
    else:
        logger.info(
            "HTTP client error",
            request_id=request_id,
            path=request.url.path,
            status_code=exc.status_code,
            detail=str(exc.detail),
        )

    return error_response(
        status_code=exc.status_code,
        detail=str(exc.detail),
        request_id=request_id,
        error_type="http_error",
    )


async def starlette_http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle Starlette HTTPExceptions (e.g., 405 Method Not Allowed)."""
    request_id = get_request_id(request)
    logger.warning(
        "Starlette HTTP exception",
        request_id=request_id,
        path=request.url.path,
        status_code=exc.status_code,
        detail=str(exc.detail),
    )

    return error_response(
        status_code=exc.status_code,
        detail=str(exc.detail),
        request_id=request_id,
        error_type="http_error",
    )


async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle request validation errors (Pydantic, etc.)."""
    request_id = get_request_id(request)
    logger.warning(
        "Validation error",
        request_id=request_id,
        path=request.url.path,
        error=str(exc),
    )

    return error_response(
        status_code=422,
        detail=str(exc) if settings.is_development else "Request validation failed",
        request_id=request_id,
        error_type="validation_error",
    )


async def domain_exception_handler(
    request: Request, exc: Exception, status_code: int, error_type: str
) -> JSONResponse:
    """Generic handler for domain-specific exceptions."""
    request_id = get_request_id(request)
    logger.warning(
        f"Domain exception: {error_type}",
        request_id=request_id,
        path=request.url.path,
        error=str(exc),
        status_code=status_code,
    )

    return error_response(
        status_code=status_code,
        detail=str(exc),
        request_id=request_id,
        error_type=error_type,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI application.

    This provides consistent error responses across the entire API.

    Args:
        app: The FastAPI application instance
    """
    from backend.exceptions import (
        EntityNotFoundError,
        AmbiguousEntityError,
        EntityValidationError,
        SentimentTimeoutError,
        SentimentValidationError,
        SynthesisTimeoutError,
        SynthesisValidationError,
    )
    from fastapi.exceptions import RequestValidationError

    # Standard exception handlers
    app.add_exception_handler(Exception, global_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    # Domain-specific exception handlers
    app.add_exception_handler(
        EntityNotFoundError,
        lambda req, exc: domain_exception_handler(
            req, exc, HTTP_ENTITY_NOT_FOUND, "entity_not_found"
        ),
    )
    app.add_exception_handler(
        AmbiguousEntityError,
        lambda req, exc: domain_exception_handler(
            req, exc, HTTP_AMBIGUOUS_ENTITY, "ambiguous_entity"
        ),
    )
    app.add_exception_handler(
        EntityValidationError,
        lambda req, exc: domain_exception_handler(
            req, exc, HTTP_VALIDATION_ERROR, "entity_validation_error"
        ),
    )
    app.add_exception_handler(
        SentimentTimeoutError,
        lambda req, exc: domain_exception_handler(
            req, exc, HTTP_SENTIMENT_TIMEOUT, "sentiment_timeout"
        ),
    )
    app.add_exception_handler(
        SentimentValidationError,
        lambda req, exc: domain_exception_handler(
            req, exc, HTTP_VALIDATION_ERROR, "sentiment_validation_error"
        ),
    )
    app.add_exception_handler(
        SynthesisTimeoutError,
        lambda req, exc: domain_exception_handler(
            req, exc, HTTP_SYNTHESIS_TIMEOUT, "synthesis_timeout"
        ),
    )
    app.add_exception_handler(
        SynthesisValidationError,
        lambda req, exc: domain_exception_handler(
            req, exc, HTTP_VALIDATION_ERROR, "synthesis_validation_error"
        ),
    )

    logger.info("Exception handlers registered", handler_count=9)