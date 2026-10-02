"""Startup fail-fast tests for required production configuration.

These tests drive the real FastAPI lifespan, because "startup aborts" is the
behaviour under test. Each case purges the relevant environment variables and
constructs ``Settings`` with ``_env_file=None`` so results never depend on the
developer's real process environment or a stray local ``.env``. Assertions are on
exception type and variable *names* only -- secret values are never read or
printed.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.config import Settings
from backend.core.exceptions import ConfigurationError

_PURGED_ENV_VARS = (
    "ENVIRONMENT",
    "SECRET_KEY",
    "OPENAI_API_KEY",
    "NEWS_API_KEY",
    "BACKEND_RELOAD",
    "CORS_ORIGINS",
)


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch):
    """Drop inherited env vars so every case sees a hermetic configuration."""
    for name in _PURGED_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def _make_settings(**overrides) -> Settings:
    """Build Settings with an explicit, hermetic baseline."""
    kwargs = {
        "environment": "production",
        "secret_key": "",
        "openai_api_key": "",
        "news_api_key": "",
        "backend_reload": False,
        "cors_origins": [],
        "_env_file": None,
    }
    kwargs.update(overrides)
    return Settings(**kwargs)


def _app_with(monkeypatch, active_settings):
    """Point the running app at `active_settings` and return a fresh instance."""
    import backend.app as app_module

    monkeypatch.setattr(app_module, "settings", active_settings)
    return create_app()


class TestProductionFailsFast:
    """Production must refuse to boot without its required configuration."""

    def test_production_startup_aborts_without_secret_key(self, monkeypatch):
        """The defect: production booted happily with no secret key."""
        app = _app_with(monkeypatch, _make_settings(secret_key=""))

        with pytest.raises(ConfigurationError) as excinfo, TestClient(app):
            pass

        assert "SECRET_KEY" in str(excinfo.value)

    def test_production_startup_abort_reports_names_not_values(self, monkeypatch):
        """The failure message must never echo a secret value."""
        app = _app_with(
            monkeypatch,
            _make_settings(secret_key="", openai_api_key="sentinel-openai-value"),
        )

        with pytest.raises(ConfigurationError) as excinfo, TestClient(app):
            pass

        message = str(excinfo.value)
        assert "SECRET_KEY" in message
        assert "sentinel-openai-value" not in message


class TestNonProductionToleratesMissingConfig:
    """Development and staging must stay bootable -- local dev depends on it."""

    def test_development_startup_unaffected_by_missing_required_var(self, monkeypatch):
        app = _app_with(monkeypatch, _make_settings(environment="development"))

        with TestClient(app) as client:
            assert client.get("/health").status_code == 200

    def test_staging_startup_unaffected_by_missing_required_var(self, monkeypatch):
        app = _app_with(monkeypatch, _make_settings(environment="staging"))

        with TestClient(app) as client:
            assert client.get("/health").status_code == 200


class TestOptionalKeysAreNotRequired:
    """The documented no-key deployment path must keep working."""

    def test_production_startup_succeeds_without_optional_keys(self, monkeypatch):
        app = _app_with(
            monkeypatch,
            _make_settings(secret_key="configured-secret", openai_api_key="", news_api_key=""),
        )

        with TestClient(app) as client:
            assert client.get("/health").status_code == 200

    def test_correctly_configured_production_starts_cleanly(self, monkeypatch):
        app = _app_with(
            monkeypatch,
            _make_settings(
                secret_key="configured-secret",
                openai_api_key="configured-openai",
                news_api_key="configured-news",
            ),
        )

        with TestClient(app) as client:
            assert client.get("/health").status_code == 200
