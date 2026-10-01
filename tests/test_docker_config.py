"""Tests that pin the Docker runtime contract for deployment."""

import os
import re


def _read(path: str) -> str:
    assert os.path.exists(path), f"{path} must exist"
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestDockerfileRuntime:
    """The image must actually start Streamlit in the frontend stage."""

    def test_frontend_stage_installs_streamlit(self):
        content = _read("Dockerfile")
        frontend_stage = content.split("AS frontend", 1)[1]
        assert (
            "streamlit" in frontend_stage.lower()
        ), "frontend stage must install/ensure streamlit is available"

    def test_frontend_stage_starts_streamlit(self):
        content = _read("Dockerfile")
        frontend_stage = content.split("AS frontend", 1)[1]
        assert re.search(
            r"CMD.*streamlit", frontend_stage
        ), "frontend stage CMD must launch streamlit"

    def test_frontend_stage_has_healthcheck(self):
        content = _read("Dockerfile")
        frontend_stage = content.split("AS frontend", 1)[1]
        assert "HEALTHCHECK" in frontend_stage
        assert "9090" in frontend_stage

    def test_nginx_stage_exists(self):
        content = _read("Dockerfile")
        assert "AS nginx" in content
        assert "nginx" in content

    def test_expose_directives_present(self):
        content = _read("Dockerfile")
        assert re.search(r"^EXPOSE\s+8000", content, re.MULTILINE)
        assert re.search(r"^EXPOSE\s+8501", content, re.MULTILINE)

    def test_single_start_command(self):
        """Railway errors when both a Procfile and a Dockerfile CMD exist."""
        assert not os.path.exists(
            "Procfile"
        ), "Procfile must be removed; Dockerfile CMD is the single start command"


class TestComposeWiring:
    """compose must build the stages it claims to build."""

    def test_services_target_existing_stages(self):
        content = _read("docker-compose.yml")
        dockerfile = _read("Dockerfile")
        targets = re.findall(r"target:\s*(\w+)", content)
        assert targets, "compose must declare build targets"
        for target in targets:
            assert f"AS {target}" in dockerfile, f"missing Dockerfile stage: {target}"

    def test_nginx_service_uses_nginx_stage(self):
        content = _read("docker-compose.yml")
        # Split on the service key, not the bare string: "image: equipilot-nginx:local"
        # also contains "nginx:" and appears after this service's build target.
        nginx_block = content.split("\n  nginx:", 1)[1]
        assert "target: nginx" in nginx_block
