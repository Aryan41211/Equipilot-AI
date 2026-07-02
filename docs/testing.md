# EquiPilot AI — Testing Guide

## Overview

EquiPilot AI uses pytest for all testing. The test suite covers unit tests, integration tests, end-to-end tests, and production readiness tests.

---

## Test Structure

```
tests/
├── test_production.py                          # Production readiness (54 tests)
├── test_dynamic_routing.py                     # Dynamic routing tests
├── test_e2e_integration.py                     # End-to-end integration tests
├── test_entity_resolution_service.py           # Entity resolution service tests
├── test_entity_resolution_tool.py              # Entity resolution tool tests
├── test_frontend_components.py                 # Frontend component tests
├── test_langgraph_market_news_integration.py   # LangGraph integration tests
├── test_market_data_service.py                 # Market data service tests
├── test_market_data_tool.py                    # Market data tool tests
├── test_sentiment_service.py                   # Sentiment service tests
├── test_sentiment_tool.py                      # Sentiment tool tests
└── test_synthesis_agent.py                     # Synthesis agent tests
```

---

## Running Tests

### Run All Tests

```bash
# From project root
pytest
```

### Run with Coverage

```bash
pytest --cov=backend --cov-report=term-missing
```

### Run Specific Test File

```bash
pytest tests/test_production.py -v
```

### Run by Test Name (Keyword)

```bash
pytest -k "health" tests/
pytest -k "metrics" tests/
pytest -k "config" tests/
```

### Run by Test Class

```bash
pytest tests/test_production.py::TestHealthEndpoints -v
pytest tests/test_production.py::TestSecurityHeaders -v
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Warnings

```bash
pytest -v -W all
```

---

## Test Categories

### 1. Production Readiness Tests (`test_production.py`)

54 tests covering all production features:

| Test Class | Tests | Description |
|------------|-------|-------------|
| `TestHealthEndpoints` | 8 | Health, ready, version, metrics endpoints |
| `TestSecurityHeaders` | 2 | Security headers on success and error responses |
| `TestRequestIdMiddleware` | 3 | Request ID generation and propagation |
| `TestExceptionHandlers` | 5 | Exception handler registration and error format |
| `TestConfigurationValidation` | 7 | Config validation, environment, workers |
| `TestMetricsCollection` | 4 | Request tracking, response times, status codes |
| `TestConfigFields` | 3 | Default values, CORS, allowed hosts |
| `TestAppConfiguration` | 5 | App title, version, docs endpoints |
| `TestExceptionHandlerConstants` | 1 | HTTP status code constants |
| `TestLoggingConfiguration` | 2 | Logger creation, setup |
| `TestExceptionPackage` | 2 | Exception hierarchy and imports |

### 2. Unit Tests

Test individual components in isolation:

- **Service tests**: Market data service, sentiment service, entity resolution service
- **Tool tests**: Market data tool, news tool, sentiment tool
- **Agent tests**: Synthesis agent

### 3. Integration Tests

Test component interactions:

- **LangGraph integration**: Market data + news workflow
- **Dynamic routing**: Query routing and agent selection
- **End-to-end**: Full request lifecycle

### 4. Frontend Tests

Test Streamlit UI components:

- **Component tests**: Query form, report display, progress tracker

---

## Writing Tests

### Test Fixtures

The test suite uses pytest fixtures for shared setup:

```python
import pytest
from backend.app import create_app


@pytest.fixture
def app():
    """Create test app instance."""
    return create_app()


@pytest.fixture
def client(app):
    """Create test client."""
    from fastapi.testclient import TestClient
    return TestClient(app)
```

### Test Structure

Tests follow the Arrange-Act-Assert pattern:

```python
class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_endpoint_returns_healthy(self, client):
        """Health endpoint should return healthy status."""
        # Arrange
        # (fixture provides client)

        # Act
        response = client.get("/health")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("healthy", "degraded")
        assert data["version"] == APP_VERSION
```

### Testing Configuration

```python
def test_config_validates_log_level(self):
    """Configuration should validate log level values."""
    from backend.config import Settings
    from pydantic import ValidationError

    # Valid value
    settings = Settings(log_level="INFO")
    assert settings.log_level == "INFO"

    # Invalid value should raise
    with pytest.raises(ValidationError):
        Settings(log_level="INVALID")
```

### Testing Exception Handlers

```python
def test_error_response_format(self):
    """error_response should produce consistent format."""
    response = error_response(
        status_code=400,
        detail="Bad request",
        request_id="test-id",
        error_type="validation_error",
    )
    data = json.loads(response.body)
    assert data["detail"] == "Bad request"
    assert data["request_id"] == "test-id"
    assert data["error_type"] == "validation_error"
```

---

## Test Configuration

### pytest Configuration

The project uses a `pyproject.toml` or `pytest.ini` for pytest configuration:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
```

### Coverage Configuration

```ini
[tool.coverage.run]
source = ["./backend"]
omit = ["*/tests/*", "*/__pycache__/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if __name__ == .__main__.:",
]
```

---

## Continuous Integration

### GitHub Actions Example

```yaml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.12"

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run tests
      run: |
        pytest --cov=backend --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

---

## Test Best Practices

### Guidelines

1. **Test one thing per test** — Each test should verify a single behavior
2. **Use descriptive names** — `test_health_endpoint_returns_healthy` not `test_health`
3. **Follow AAA pattern** — Arrange, Act, Assert
4. **Use fixtures for setup** — Avoid duplicating setup code
5. **Test edge cases** — Empty inputs, invalid data, error conditions
6. **Test error paths** — Verify error responses have correct format
7. **Keep tests fast** — Avoid external API calls in unit tests
8. **Use mocks for external services** — Mock yfinance, OpenAI, News API

### What to Test

| Component | What to Test |
|-----------|-------------|
| **Endpoints** | Status codes, response format, error handling |
| **Middleware** | Headers, request IDs, metrics, rate limiting |
| **Configuration** | Validation, defaults, environment modes |
| **Services** | Data transformation, error handling, caching |
| **Agents** | State transitions, tool calls, error recovery |
| **Schemas** | Validation, serialization, field constraints |

---

## Related Documentation

- [Architecture](architecture.md) — System architecture overview
- [API Reference](api.md) — Complete API documentation
- [Deployment Guide](deployment.md) — Production deployment instructions
- [Troubleshooting](troubleshooting.md) — Common issues and solutions