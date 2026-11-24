# OPTIMIZATION_STRATEGY.md — EquiPilot AI

**Project:** EquiPilot AI — Agentic Equity Research Platform
**Strategy date:** 2026-11-24

## Priority 1: Agent Graph Integration (Phase E1)

**Current state:** 5 agent classes exist but compiled graph has only 4 nodes. SynthesisAgent not wired.
**Goal:** Integrate SynthesisAgent into the compiled LangGraph workflow.
**Constraint:** Do not claim 5-agent workflow until SynthesisAgent is in the active graph.

### Planned actions:
1. Add SynthesisAgent as a graph node
2. Wire router → parallel_tools → synthesis → research
3. Ensure state merging and error handling for parallel execution
4. Test end-to-end graph execution

### Success criteria:
- 5 agents connected in compiled graph
- Complete graph execution
- Synthesis actually functional

## Priority 2: Synthesis & Citations (Phase E5-E7)

**Current state:** SynthesisAgent exists but not wired. Active report is placeholder. Citations=None.
**Goal:** Implement real synthesis with source-grounded citations.
**Constraint:** Cannot claim citations without testing against real sources.

### Planned actions:
1. Wire SynthesisAgent into graph
2. Test citation generation against source references
3. Implement citation verification tests
4. Measure citation precision and coverage

### Success criteria:
- Citations returned in API responses
- Citations resolve to actual sources
- Citation-to-claim alignment verified

## Priority 3: Market Data Reliability (Phase E3)

**Current state:** yfinance integration exists in code. Not tested with live API.
**Goal:** Validate market data reliability and provenance.
**Constraint:** No OPENAI_API_KEY/NEWS_API_KEY configured (no cost incurred).

### Planned actions:
1. Test yfinance integration with real ticker
2. Validate symbol resolution, historical data, missing data handling
3. Attach data source, retrieval timestamp, period, currency
4. Test invalid ticker, market holidays, stale data handling

### Success criteria:
- Market data provenance established
- Stale/unavailable data not presented as current
- External API failures handled gracefully

## Priority 4: Sentiment Evaluation (Phase E6)

**Current state:** Sentiment service exists (LLM-based). Not evaluated.
**Goal:** Build manually reviewed evaluation dataset.
**Constraint:** No claimed accuracy without labeled evaluation.

### Planned actions:
1. Create manually reviewed sentiment evaluation dataset (50-100 samples)
2. Measure precision, recall, F1, confusion matrix
3. Compare against baseline

### Success criteria:
- Sentiment accuracy measured with labels
- No ungrounded accuracy claims

## Priority 5: API Performance & Cost (Phase E8)

**Current state:** API p50 ~1.5ms. Graph execution ~704ms.
**Goal:** Establish cost and latency baselines.
**Constraint:** No OPENAI_API_KEY (no LLM calls made).

### Planned actions:
1. Measure end-to-end latency with real LLM (when key available)
2. Measure cost per research run
3. Optimize unnecessary LLM calls

### Success criteria:
- Cost and latency baselines established
- Unnecessary agent calls identified

## Priority 6: Security & Resilience (Phase E8-E9)

**Current state:** Rate limiting, security headers exist in code.
**Goal:** Validate security boundaries.
**Constraint:** Safe, controlled tests only.

### Planned actions:
1. Test prompt injection resistance
2. Test external tool failures
3. Test rate limiting under load
4. Test graceful degradation

### Success criteria:
- External content treated as untrusted
- Graceful degradation verified
- No incomplete research disguised as verified

## Acceptance Criteria

| Criterion | Status |
|---|---|
| All 5 agents connected | NOT STARTED |
| Complete graph execution | NOT STARTED |
| Synthesis functional | NOT STARTED |
| Citations validated | NOT STARTED |
| Market data provenance | NOT STARTED |
| Error handling tested | PARTIAL (code review) |
| Agent evaluation reproducible | NOT STARTED |
| Critical tests passing | DONE (257 passed) |
