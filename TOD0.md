# Resolved TODOs

- [x] Dockerfile keeps `AS frontend` as a real Streamlit stage (no longer a dead copy).
- [x] `_run_graph()` uses `await compiled.ainvoke(initial_state)` — `asyncio.to_thread`
      is not applicable; the original item was written against a sync `.invoke` call
      that no longer exists.
- [x] `check_status()` calls only `{API_BASE_URL}/api/v1/research/{request_id}`.
- [x] `pytest` green — 236 passed.
- [x] `test_dockerfile_multi_stage` still passes — all three stage names it asserts are
      retained (`base`, `production`, `frontend`). The `nginx` stage was added on top and
      is built and validated by `tests/test_docker_config.py` and the CI `docker` job.
