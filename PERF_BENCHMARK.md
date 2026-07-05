# EquiPilot AI - Performance Benchmarks (Phase 3)


## How to run
- Start backend (uvicorn) and frontend (streamlit).
- Execute N runs (suggested N=3) for the same query/ticker.
- Capture:
  - Frontend observed total time (from `poll_started_at` -> completion)
  - Backend per-node durations from `execution_metadata.traces`
  - Number of HTTP polls during polling
  - Number of POST submissions (should be 1)

## Placeholder template (fill after profiling)
| Run | Query | Request ID | Frontend total (s) | Backend total (ms) | router (ms) | market_data_tool (ms) | news_tool (ms) | sentiment_tool (ms) | research (ms) | HTTP polls |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 |  |  |  |  |  |  |  |  |  |  |
| 2 |  |  |  |  |  |  |  |  |  |  |
| 3 |  |  |  |  |  |  |  |  |  |  |

## Before vs After
- Keep identical inputs and environment variables.
- Record differences and confirm:
  - no duplicate requests
  - no duplicate reruns
  - no change in report output quality
