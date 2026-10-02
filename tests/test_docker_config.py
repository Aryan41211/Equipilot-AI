"""Tests that pin the Docker runtime contract for deployment."""

import os
import re


def _read(path: str) -> str:
    assert os.path.exists(path), f"{path} must exist"
    with open(path, encoding="utf-8") as f:
        return f.read()


def _named_stages(content: str) -> list[str]:
    """Ordered stage aliases from a Dockerfile, ignoring comments and blank lines."""
    stages = []
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^FROM\s+\S+(?:\s+AS\s+(\S+))?\s*$", line, re.IGNORECASE)
        if match and match.group(1):
            stages.append(match.group(1).lower())
    return stages


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

    def test_frontend_stage_cmd_honors_platform_port(self):
        """Railway injects PORT; the frontend must bind it, not a bespoke var."""
        content = _read("Dockerfile")
        frontend_stage = content.split("AS frontend", 1)[1]
        cmd = re.search(r"^CMD .*$", frontend_stage, re.MULTILINE)
        assert cmd, "frontend stage must define a CMD"
        assert "--server.port=${PORT:-8501}" in cmd.group(
            0
        ), "frontend CMD must expand $PORT so the platform's injected port is honoured"
        assert (
            "FRONTEND_PORT" not in frontend_stage
        ), "FRONTEND_PORT is dead: the CMD reads $PORT, so the leftover var invites a regression"

    def test_production_stage_is_last(self):
        """The final stage must be `production`.

        WHY: `docker build .` with no `--target` builds the LAST stage. Railway
        does not support `--target` for multi-stage Dockerfiles, so it deploys
        whichever stage happens to be last. With `nginx` last, a Railway deploy
        of this Dockerfile serves nginx and the backend CMD never runs -- the
        deploy looks healthy and is entirely wrong. Stage order is therefore a
        deployment contract, not a cosmetic choice.
        """
        stages = _named_stages(_read("Dockerfile"))
        assert stages, "Dockerfile must declare named stages"
        assert stages[-1] == "production", (
            f"production must be the last stage so a bare `docker build .` yields the "
            f"backend image; got order {stages}"
        )

    def test_all_named_stages_retained(self):
        """Reordering must not drop a stage that compose or CI builds by name."""
        stages = _named_stages(_read("Dockerfile"))
        for required in ("base", "production", "frontend", "nginx"):
            assert required in stages, f"Dockerfile is missing the {required} stage: {stages}"
        assert len(stages) == len(set(stages)), f"duplicate stage aliases: {stages}"


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

    def test_backend_env_file_is_optional(self):
        """.env is gitignored, so a bare `env_file: [.env]` hard-fails a clean clone."""
        content = _read("docker-compose.yml")
        backend_block = content.split("\n  backend:", 1)[1].split("\n  frontend:", 1)[0]
        assert "env_file:" in backend_block, "docker-compose.yml must declare env_file"
        # env_file children are indented 6 spaces; a 4-space line is the next sibling key.
        entries = []
        for line in backend_block.split("env_file:", 1)[1].split("\n")[1:]:
            if line.strip() and not line.startswith("      "):
                break
            entries.append(line)
        block = "\n".join(entries)
        assert "path: .env" in block, f"env_file must use the long form, got: {block.strip()!r}"
        assert (
            "required: false" in block
        ), f"env_file must mark .env optional, got: {block.strip()!r}"
        assert not re.search(
            r"^\s*-\s*\.env\s*$", block, re.MULTILINE
        ), "a bare '- .env' entry makes compose fail when .env is absent"
