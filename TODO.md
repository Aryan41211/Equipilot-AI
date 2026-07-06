# Phase 3 TODO — Enterprise Performance Optimization

- [ ] Profile pipeline stages (Frontend + Backend timing spans)
  - [ ] Frontend timing instrumentation + “Timing Report” expander (collapsed by default; only after completion)
  - [ ] Backend execution metadata: ensure node/tool traces include durations and add overall stage timings if missing

- [ ] Parallel execution in backend
  - [ ] Implement `parallel_tools_node` in `backend/graphs/nodes.py`
  - [ ] Update `backend/graphs/graph.py` routing to: `router -> parallel_tools -> research -> END`
  - [ ] Ensure market+news run concurrently; sentiment runs after news
  - [ ] Ensure partial failures don’t break entire workflow; isolate exceptions per task

- [ ] Intelligent caching (TTL + deterministic-only + thread-safe)
  - [ ] Add TTL cache + hit/miss metrics to `backend/services/news_service.py`
  - [ ] Add TTL cache + hit/miss metrics to `backend/services/sentiment_service.py`
  - [ ] Make TTL configurable from `backend/config.py` (or add local defaults if already there)

- [ ] Streamlit rerun/poll optimization
  - [ ] Reduce expensive UI work during polling (progress/trace rendering frequency)
  - [ ] Keep duplicate polling/reruns prevented

- [ ] Validation + benchmarking
  - [ ] Run baseline benchmarks (before)
  - [ ] Run optimized benchmarks (after)
  - [ ] Compare output identity/quality (report text shape remains identical)
  - [ ] Validate no duplicate API calls and no duplicate polling loops

- [ ] Final deliverables
  - [ ] Update `PERF_BENCHMARK.md` with before/after table
  - [ ] Provide performance bottlenecks found, optimizations implemented, files modified, remaining limitations
  - [ ] Provide git commit message
