# EquiPilot AI — Phase 2 Reproduction Guide

**Project:** EquiPilot AI — Agentic Equity Research System
**Git SHA:** `0fccaca`
**Branch:** `main`
**Date:** 2026-11-24
**Environment:** 16 CPU cores, 15.65 GB RAM, CPU-only

---

## 1. Environment Setup

```bash
cd C:\projects\Equipilot AI

# Verify Python version
python --version  # 3.12

# Install dependencies
pip install -r requirements.txt

# Key dependencies:
# - FastAPI, LangGraph, LangChain
# - yfinance (market data)
# - pydantic (schemas)
# - pytest (testing)
```

---

## 2. Run Tests

```bash
cd C:\projects\Equipilot AI

# Run all tests
python -m pytest tests -q -p no:cacheprovider

# Expected: 257 passed, 3 failed (pre-existing environment-related)
# Failures: test_env_example_documents_*, test_submit_research_connection_error

# Run financial analysis tests only
python -m pytest tests/test_financial_analysis.py -q -p no:cacheprovider
# Expected: 39 passed

# Run report evaluator tests only
python -m pytest tests/test_report_evaluator.py -q -p no:cacheprovider
# Expected: 16 passed
```

---

## 3. Graph Execution Test

```bash
cd C:\projects\Equipilot AI\backend

python -c "
import asyncio
from backend.graphs.graph import create_first_graph, create_initial_state

async def test():
    graph = create_first_graph()
    state = create_initial_state('Analyze AAPL stock fundamentals')
    result = await graph.ainvoke(state)
    print('Status:', result.get('status'))
    print('Ticker:', result.get('ticker'))
    print('Report preview:', result.get('report', '')[:200])
    print('Citations:', len(result.get('citations', [])))
    print('Execution duration ms:', result.get('execution_duration_ms'))

asyncio.run(test())
"

# Expected output:
# Status: success
# Ticker: AAPL
# Report preview: Placeholder research report for AAPL...
# Citations: 0 (no LLM key)
# Execution duration ms: ~700ms
```

---

## 4. Financial Analysis Test

```bash
cd C:\projects\Equipilot AI\backend

python -c "
from backend.services.financial_analysis import compute_all_financials, validate_financial_metrics

# Compute all financials with sample data
result = compute_all_financials(
    revenue=1000,
    previous_revenue=800,
    gross_profit=400,
    net_income=150,
    roe_result=0.3,
)
print('Revenue growth:', result.get('revenue_growth'))  # 0.25
print('Gross margin:', result.get('gross_margin'))       # 0.4
print('Net margin:', result.get('net_margin'))           # 0.15

# Validate metrics
validation = validate_financial_metrics({
    'gross_margin': 0.4,
    'debt_to_equity': 0.5,
    'pe_ratio': 20.0,
})
print('All valid:', all(v['valid'] for v in validation.values()))
"
```

---

## 5. Key Files

| File | Purpose |
|------|---------|
| `backend/graphs/graph.py` | Compiled LangGraph (5 nodes) |
| `backend/graphs/nodes.py` | Node implementations |
| `backend/graphs/state.py` | GraphState schema |
| `backend/agents/synthesis_agent.py` | SynthesisAgent (LLM report generation) |
| `backend/services/financial_analysis.py` | 13 financial calculation functions |
| `backend/services/report_evaluator.py` | Report evaluation framework |
| `tests/test_financial_analysis.py` | 39 financial tests |
| `tests/test_report_evaluator.py` | 16 report evaluation tests |
| `EQUIPILOT_PHASE2_AUDIT.md` | Full audit report |
| `EQUIPILOT_AGENT_BENCHMARK.csv` | Agent performance metrics |
| `EQUIPILOT_RESEARCH_EVALUATION.json` | Evaluation framework spec |
| `EQUIPILOT_CITATION_AUDIT.md` | Citation integrity rules |
| `EQUIPILOT_FINANCIAL_VALIDATION.md` | Financial calculations doc |

---

## 6. Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| No OPENAI_API_KEY | LLM synthesis falls back to placeholder | Configure API key to enable full synthesis |
| No evaluation dataset | Report quality not quantitatively measured | Create 100+ company case dataset |
| No human review | Subjective criteria unvalidated | Recruit domain experts for review |
| No financial backtest | No investment accuracy claims | Not applicable (prohibited) |
| yfinance rate-limited | Live market data testing limited | Use cached/synthetic data for tests |

---

## 7. Git Status

- All changes committed to `main` (SHA: `0fccaca`)
- No branches created or switched
- No commits pushed (pending approval)
- Pre-commit hooks: ruff, black, trailing whitespace — all pass
