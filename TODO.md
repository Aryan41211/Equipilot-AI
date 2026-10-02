# Resolved Deployment TODOs

All items below were closed during the deployment-completion pass.
See `docs/superpowers/plans/2026-10-01-deployment-completion.md`.

- [x] Exactly one Railway start command: `Procfile` deleted; the `Dockerfile` `CMD`
      (`python -m backend.app`) is authoritative.
- [x] OpenAI client construction is lazy (`backend/services/llm_service.py:_get_client`).
- [x] Startup logging emits `StartupConfig` with the bound `port`, the `host`, the
      `CORS_ORIGINS` raw value + detected format, the parsed list, and
      `openai_api_key_present` (`backend/app.py` lifespan).
- [x] Malformed `CORS_ORIGINS` in production raises during config parse
      (`backend/config.py` `parse_cors_origins`), and a production value that parses to an
      empty allow-list logs ERROR and raises (`enforce_environment_cors`).
- [x] Full test suite green — 236 passed. `tests/test_deploy_config.py` and
      `tests/test_docker_config.py` pin the deployment contract so these items cannot
      silently regress.
