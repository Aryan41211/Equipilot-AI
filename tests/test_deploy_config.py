"""Tests that pin the env-var contract for Railway + Streamlit Cloud."""

import os
from typing import ClassVar


def _read(path: str) -> str:
    assert os.path.exists(path), f"{path} must exist"
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestDeployEnvContract:
    """Every var the platforms need must be documented in .env.example."""

    REQUIRED_BACKEND_VARS: ClassVar[list[str]] = [
        "ENVIRONMENT",
        "OPENAI_API_KEY",
        "SECRET_KEY",
        "BACKEND_RELOAD",
        "PORT",
        "CORS_ORIGINS",
        "LOG_LEVEL",
        "LOG_FORMAT",
    ]

    REQUIRED_FRONTEND_VARS: ClassVar[list[str]] = [
        "EQUIPILOT_API_URL",
        "EQUIPILOT_HEALTH_URL",
        "HEALTH_CHECK_PORT",
    ]

    def test_env_example_documents_backend_vars(self):
        content = _read(".env.example")
        for var in self.REQUIRED_BACKEND_VARS:
            assert var in content, f".env.example missing {var}"

    def test_env_example_documents_frontend_vars(self):
        content = _read(".env.example")
        for var in self.REQUIRED_FRONTEND_VARS:
            assert var in content, f".env.example missing {var}"

    def test_port_documented(self):
        content = _read(".env.example")
        assert "PORT=" in content

    def test_nginx_conf_proxies_api_to_backend(self):
        content = _read("nginx.conf")
        assert "backend:8000" in content
        assert "/api/" in content

    def test_streamlit_config_is_not_gitignored(self):
        """config.toml is force-tracked; the ignore rule would silently drop edits."""
        result = os.popen("git check-ignore -v --no-index .streamlit/config.toml").read()
        assert result.strip() == "", f".streamlit/config.toml must not be gitignored, got: {result}"
