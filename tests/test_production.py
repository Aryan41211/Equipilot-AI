# EquiPilot AI - Production Tests
# Tests for health endpoints, middleware, exception handlers, and production features

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.app import APP_VERSION, create_app
from backend.exceptions.handlers import (
    HTTP_AMBIGUOUS_ENTITY,
    HTTP_ENTITY_NOT_FOUND,
    HTTP_SENTIMENT_TIMEOUT,
    HTTP_SYNTHESIS_TIMEOUT,
    HTTP_VALIDATION_ERROR,
    error_response,
)
from backend.middleware.production import metrics


@pytest.fixture
def app():
    """Create test app instance."""
    return create_app()


@pytest.fixture
def client(app):
    """Create test client."""
    from fastapi.testclient import TestClient
    return TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_endpoint_returns_healthy(self, client):
        """Health endpoint should return healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ("healthy", "degraded")
        assert data["version"] == APP_VERSION
        assert "services" in data

    def test_health_endpoint_includes_service_status(self, client):
        """Health endpoint should include service configuration status."""
        response = client.get("/health")
        data = response.json()
        assert "openai" in data["services"]
        assert "news_api" in data["services"]

    def test_health_endpoint_returns_degraded_with_errors(self, app, client):
        """Health endpoint should return degraded when startup errors exist."""
        app.state.startup_errors = ["Test error"]
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "degraded"
        assert "errors" in data
        assert "Test error" in data["errors"]

    def test_ready_endpoint_returns_ready(self, client):
        """Readiness endpoint should return ready status when no startup errors."""
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["version"] == APP_VERSION

    def test_ready_endpoint_returns_not_ready_on_error(self, app, client):
        """Readiness endpoint should return 503 when startup errors exist."""
        app.state.startup_errors = ["Test error"]
        response = client.get("/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not_ready"
        assert "errors" in data

    def test_version_endpoint(self, client):
        """Version endpoint should return correct application info."""
        response = client.get("/version")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "EquiPilot AI"
        assert data["version"] == APP_VERSION
        assert "api_version" in data

    def test_metrics_endpoint(self, client):
        """Metrics endpoint should return metrics data."""
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "requests_total" in data
        assert "requests_by_status" in data
        assert "average_response_time_ms" in data
        assert "active_requests" in data

    def test_metrics_tracks_health_requests(self, client):
        """Metrics should track health endpoint requests."""
        initial_count = metrics["requests_total"].get("/health", 0)
        client.get("/health")
        assert metrics["requests_total"]["/health"] >= initial_count + 1


class TestSecurityHeaders:
    """Test security headers middleware."""

    def test_security_headers_present(self, client):
        """All responses should include security headers."""
        response = client.get("/health")

        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert "Strict-Transport-Security" in response.headers
        assert "Content-Security-Policy" in response.headers
        assert "Referrer-Policy" in response.headers
        assert "Permissions-Policy" in response.headers

    def test_security_headers_on_error_responses(self, client):
        """Security headers should be present even on error responses."""
        response = client.get("/nonexistent-path")
        assert response.status_code in (404,)
        assert response.headers.get("X-Content-Type-Options") == "nosniff"


class TestRequestIdMiddleware:
    """Test request ID middleware."""

    def test_request_id_header_present(self, client):
        """All responses should include X-Request-ID header."""
        response = client.get("/health")

        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) == 36  # UUID format

    def test_unique_request_ids(self, client):
        """Each request should get a unique request ID."""
        response1 = client.get("/health")
        response2 = client.get("/health")

        assert response1.headers["X-Request-ID"] != response2.headers["X-Request-ID"]

    def test_request_id_in_error_response(self, client):
        """Error responses should include request ID."""
        response = client.get("/ready")
        assert "X-Request-ID" in response.headers


class TestExceptionHandlers:
    """Test exception handling middleware."""

    def test_global_exception_handler_includes_request_id(self, client):
        """Global exception handler should include request ID in response."""
        response = client.get("/health")
        assert "X-Request-ID" in response.headers

    def test_not_found_returns_json(self, client):
        """404 responses should return JSON with request_id."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "request_id" in data

    def test_method_not_allowed_returns_json(self, client):
        """405 responses should return JSON with request_id."""
        response = client.put("/health")  # PUT not allowed on GET endpoint
        assert response.status_code in (405,)
        data = response.json()
        assert "detail" in data
        assert "request_id" in data

    def test_error_response_format(self):
        """error_response should produce consistent format."""

        response = error_response(
            status_code=400,
            detail="Bad request",
            request_id="test-id",
            error_type="validation_error",
        )
        data = response.body
        import json
        parsed = json.loads(data)
        assert parsed["detail"] == "Bad request"
        assert parsed["request_id"] == "test-id"
        assert parsed["error_type"] == "validation_error"

    def test_domain_exception_handlers_registered(self, app):
        """Domain exception handlers should be registered."""
        from backend.exceptions import (
            AmbiguousEntityError,
            EntityNotFoundError,
            EntityValidationError,
            SentimentTimeoutError,
            SentimentValidationError,
            SynthesisTimeoutError,
            SynthesisValidationError,
        )

        # Check that handlers are registered for domain exceptions
        handled_exceptions = list(app.exception_handlers.keys())
        for exc_class in [
            EntityNotFoundError,
            AmbiguousEntityError,
            EntityValidationError,
            SentimentTimeoutError,
            SentimentValidationError,
            SynthesisTimeoutError,
            SynthesisValidationError,
        ]:
            assert exc_class in handled_exceptions


class TestConfigurationValidation:
    """Test configuration validation."""

    def test_config_validates_log_level(self):
        """Configuration should validate log level values."""
        from pydantic import ValidationError

        from backend.config import Settings

        # Valid log level
        settings = Settings(log_level="INFO")
        assert settings.log_level == "INFO"

        # Invalid log level should raise
        with pytest.raises(ValidationError):
            Settings(log_level="INVALID")

    def test_config_validates_log_format(self):
        """Configuration should validate log format values."""
        from pydantic import ValidationError

        from backend.config import Settings

        settings = Settings(log_format="json")
        assert settings.log_format == "json"

        with pytest.raises(ValidationError):
            Settings(log_format="xml")

    def test_config_validates_news_provider(self):
        """Configuration should validate news API provider values."""
        from pydantic import ValidationError

        from backend.config import Settings

        settings = Settings(news_api_provider="newsapi")
        assert settings.news_api_provider == "newsapi"

        with pytest.raises(ValidationError):
            Settings(news_api_provider="invalid")

    def test_config_validates_environment(self):
        """Configuration should validate environment values."""
        from pydantic import ValidationError

        from backend.config import Settings

        settings = Settings(environment="production")
        assert settings.environment == "production"

        with pytest.raises(ValidationError):
            Settings(environment="invalid")

    def test_config_validates_workers(self):
        """Configuration should validate worker count."""
        from pydantic import ValidationError

        from backend.config import Settings

        settings = Settings(backend_workers=4)
        assert settings.backend_workers == 4

        with pytest.raises(ValidationError):
            Settings(backend_workers=0)

        with pytest.raises(ValidationError):
            Settings(backend_workers=10)

    def test_validate_required_settings_returns_warnings(self):
        """validate_required_settings should return warnings for missing keys."""
        from backend.config import Settings

        settings = Settings(openai_api_key="", news_api_key="")
        warnings = settings.validate_required_settings()

        assert len(warnings) >= 2
        assert any("OPENAI_API_KEY" in w for w in warnings)
        assert any("NEWS_API_KEY" in w for w in warnings)

    def test_validate_environment_variables_production(self):
        """validate_environment_variables should return errors for production."""
        from backend.config import Settings

        settings = Settings(
            environment="production",
            openai_api_key="",
            secret_key="",
            backend_reload=True,
        )
        errors = settings.validate_environment_variables()

        assert len(errors) >= 3
        assert any("OPENAI_API_KEY" in e for e in errors)
        assert any("SECRET_KEY" in e for e in errors)
        assert any("BACKEND_RELOAD" in e for e in errors)

    def test_is_production_property(self):
        """is_production should return correct value."""
        from backend.config import Settings

        dev_settings = Settings(environment="development", backend_reload=True)
        assert dev_settings.is_development is True
        assert dev_settings.is_production is False

        prod_settings = Settings(environment="production", backend_reload=False)
        assert prod_settings.is_production is True
        assert prod_settings.is_development is False

        # is_development also considers backend_reload
        reload_settings = Settings(environment="staging", backend_reload=True)
        assert reload_settings.is_development is True


class TestMetricsCollection:
    """Test metrics middleware."""

    def test_metrics_tracks_requests(self, client):
        """Metrics middleware should track request counts."""
        initial_count = metrics["requests_total"].get("/health", 0)

        client.get("/health")

        assert metrics["requests_total"]["/health"] >= initial_count + 1

    def test_metrics_tracks_response_time(self, client):
        """Metrics middleware should track response times."""
        # Clear previous metrics
        metrics["request_duration"].clear()

        client.get("/health")

        assert len(metrics["request_duration"]) >= 1

    def test_metrics_tracks_active_requests(self, client):
        """Metrics middleware should track active requests."""
        initial_active = metrics["active_requests"]
        client.get("/health")
        assert metrics["active_requests"] == initial_active  # Should return to initial

    def test_metrics_tracks_status_codes(self, client):
        """Metrics middleware should track status codes."""
        initial_count = metrics["requests_by_status"].get(200, 0)
        client.get("/health")
        assert metrics["requests_by_status"][200] >= initial_count + 1


class TestConfigFields:
    """Test configuration fields and defaults."""

    def test_default_values(self):
        """Settings should have correct default values."""
        from backend.config import Settings

        settings = Settings()

        assert settings.backend_host == "0.0.0.0"
        assert settings.backend_port == 8000
        assert settings.backend_reload is True
        assert settings.backend_workers == 2
        assert settings.api_prefix == "/api/v1"
        assert settings.request_rate_limit == 100
        assert settings.max_concurrent_requests == 10
        assert settings.environment == "development"
        assert settings.app_name == "EquiPilot AI"
        assert settings.app_version == "0.1.0"

    def test_cors_origins_parsing(self):
        """CORS origins should be parsed correctly from string."""
        from backend.config import Settings

        settings = Settings(cors_origins=["http://localhost:3000"])
        assert "http://localhost:3000" in settings.cors_origins

    def test_allowed_hosts_default(self):
        """Allowed hosts should default to wildcard."""
        from backend.config import Settings

        settings = Settings()
        assert "*" in settings.allowed_hosts


class TestAppConfiguration:
    """Test FastAPI app configuration."""

    def test_app_has_correct_title(self, app):
        """App should have correct title."""
        assert app.title == "EquiPilot AI"

    def test_app_has_correct_version(self, app):
        """App should have correct version."""
        assert app.version == APP_VERSION

    def test_app_docs_endpoint_exists(self, client):
        """App should have docs endpoint."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_app_openapi_endpoint_exists(self, client):
        """App should have OpenAPI endpoint."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

    def test_app_redoc_endpoint_exists(self, client):
        """App should have Redoc endpoint."""
        response = client.get("/redoc")
        assert response.status_code == 200


class TestExceptionHandlerConstants:
    """Test exception handler constants."""

    def test_http_status_constants(self):
        """HTTP status constants should have correct values."""
        assert HTTP_ENTITY_NOT_FOUND == 404
        assert HTTP_AMBIGUOUS_ENTITY == 409
        assert HTTP_SENTIMENT_TIMEOUT == 504
        assert HTTP_SYNTHESIS_TIMEOUT == 504
        assert HTTP_VALIDATION_ERROR == 422


class TestDockerConfiguration:
    """Test Docker configuration files."""

    def test_dockerfile_exists(self):
        """Dockerfile should exist."""
        assert os.path.exists("Dockerfile")

    def test_dockerignore_exists(self):
        """.dockerignore should exist."""
        assert os.path.exists(".dockerignore")

    def test_docker_compose_exists(self):
        """docker-compose.yml should exist."""
        assert os.path.exists("docker-compose.yml")

    def test_nginx_config_exists(self):
        """nginx.conf should exist."""
        assert os.path.exists("nginx.conf")

    def test_dockerfile_has_healthcheck(self):
        """Dockerfile should have HEALTHCHECK instruction."""
        with open("Dockerfile") as f:
            content = f.read()
        assert "HEALTHCHECK" in content

    def test_dockerfile_has_non_root_user(self):
        """Dockerfile should create and use non-root user."""
        with open("Dockerfile") as f:
            content = f.read()
        assert "appuser" in content
        assert "USER appuser" in content

    def test_dockerfile_multi_stage(self):
        """Dockerfile should have multi-stage builds."""
        with open("Dockerfile") as f:
            content = f.read()
        assert "AS base" in content
        assert "AS production" in content
        assert "AS frontend" in content

    def test_docker_compose_has_resource_limits(self):
        """docker-compose should have resource limits."""
        with open("docker-compose.yml") as f:
            content = f.read()
        assert "deploy" in content
        assert "resources" in content
        assert "limits" in content

    def test_docker_compose_has_healthchecks(self):
        """docker-compose should have healthchecks for all services."""
        with open("docker-compose.yml") as f:
            content = f.read()
        assert "healthcheck" in content

    def test_nginx_has_rate_limiting(self):
        """nginx.conf should have rate limiting zones."""
        with open("nginx.conf") as f:
            content = f.read()
        assert "limit_req_zone" in content
        assert "limit_req" in content

    def test_nginx_has_security_headers(self):
        """nginx.conf should have security headers."""
        with open("nginx.conf") as f:
            content = f.read()
        assert "X-Frame-Options" in content
        assert "X-Content-Type-Options" in content
        assert "Strict-Transport-Security" in content


class TestLoggingConfiguration:
    """Test logging configuration."""

    def test_logger_creates_structured_logger(self):
        """get_logger should return a structlog logger."""
        from backend.utils.logger import get_logger

        logger = get_logger("test")
        assert logger is not None

    def test_setup_logging_does_not_raise(self):
        """setup_logging should not raise exceptions."""
        from backend.utils.logger import setup_logging

        # Should not raise
        setup_logging()


class TestExceptionPackage:
    """Test exceptions package."""

    def test_exception_package_imports(self):
        """Exception package should export all exception classes."""
        from backend.exceptions import (
            EntityNotFoundError,
            EntityResolutionError,
            SentimentError,
            SentimentTimeoutError,
            SynthesisError,
            SynthesisTimeoutError,
        )

        # Verify they are actual exception classes
        assert issubclass(EntityNotFoundError, EntityResolutionError)
        assert issubclass(SentimentTimeoutError, SentimentError)
        assert issubclass(SynthesisTimeoutError, SynthesisError)

    def test_exception_hierarchy(self):
        """Exception hierarchy should be correct."""
        from backend.exceptions import (
            EntityNotFoundError,
            EntityResolutionError,
        )

        exc = EntityNotFoundError("test")
        assert isinstance(exc, EntityResolutionError)
        assert isinstance(exc, Exception)
