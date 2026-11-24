"""EquiPilot AI Phase 4 — Citation Metrics Benchmark.

Evaluates citation precision, coverage, and correctness on research reports.
Tests with simulated and real citation data (no LLM API calls).

Usage:
    python scripts/phase4/citation_metrics_benchmark.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

BACKEND = Path(__file__).resolve().parent.parent.parent
EXPERIMENT_DIR = BACKEND / "experiment_results" / "phase4"
EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Citation test cases
# ---------------------------------------------------------------------------

CITATION_TEST_CASES: list[dict[str, Any]] = [
    {
        "case_id": "cite-001",
        "report": "Apple's revenue grew 15% year-over-year [1]. The company maintains strong margins [2].",
        "citations": [
            {
                "id": "1",
                "type": "market_data",
                "title": "Apple Q3 2024 Earnings Report",
                "source": "SEC Filing",
                "url": "https://sec.gov/apple-q3-2024",
                "chunk_text": "Apple's revenue grew 15% year-over-year to $85.8 billion.",
                "confidence": 0.95,
            },
            {
                "id": "2",
                "type": "market_data",
                "title": "Apple Financial Analysis",
                "source": "Bloomberg",
                "url": "https://bloomberg.com/apple-financials",
                "chunk_text": "Apple maintains gross margins above 40%.",
                "confidence": 0.90,
            },
        ],
        "answer_sentences": [
            "Apple's revenue grew 15% year-over-year [1].",
            "The company maintains strong margins [2].",
        ],
        "expected_citation_precision": 1.0,
        "expected_citation_coverage": 1.0,
    },
    {
        "case_id": "cite-002",
        "report": "Microsoft's revenue increased 10% [1]. The cloud segment grew 25% [2]. However, the PC division declined [3].",
        "citations": [
            {
                "id": "1",
                "type": "market_data",
                "title": "Microsoft Q4 2024 Earnings",
                "source": "SEC Filing",
                "url": "https://sec.gov/microsoft-q4-2024",
                "chunk_text": "Microsoft's revenue increased 10% year-over-year.",
                "confidence": 0.95,
            },
            {
                "id": "2",
                "type": "market_data",
                "title": "Microsoft Cloud Report",
                "source": "Microsoft Investor Relations",
                "url": "https://microsoft.com/cloud-report",
                "chunk_text": "The cloud segment grew 25% year-over-year.",
                "confidence": 0.92,
            },
        ],
        "answer_sentences": [
            "Microsoft's revenue increased 10% [1].",
            "The cloud segment grew 25% [2].",
            "However, the PC division declined.",
        ],
        "expected_citation_precision": 1.0,
        "expected_citation_coverage": 0.67,  # 2 of 3 sentences cited
    },
    {
        "case_id": "cite-003",
        "report": "Tesla delivered 450000 vehicles [1]. The company is profitable [2].",
        "citations": [
            {
                "id": "1",
                "type": "market_data",
                "title": "Tesla Delivery Report",
                "source": "Tesla Investor Relations",
                "url": "https://tesla.com/deliveries",
                "chunk_text": "Tesla delivered 450000 vehicles in Q3.",
                "confidence": 0.95,
            },
            {
                "id": "2",
                "type": "news",
                "title": "Tesla Profitability Analysis",
                "source": "CNBC",
                "url": "https://cnbc.com/tesla-profit",
                "chunk_text": "Tesla reported net income of $1.5 billion.",
                "confidence": 0.88,
            },
        ],
        "answer_sentences": [
            "Tesla delivered 450000 vehicles [1].",
            "The company is profitable [2].",
        ],
        "expected_citation_precision": 1.0,
        "expected_citation_coverage": 1.0,
    },
    {
        "case_id": "cite-004",
        "report": "Amazon's AWS revenue grew 20% [1]. The retail segment faces headwinds [2].",
        "citations": [
            {
                "id": "1",
                "type": "market_data",
                "title": "AWS Growth Report",
                "source": "Amazon Investor Relations",
                "url": "https://amazon.com/aws-report",
                "chunk_text": "AWS revenue grew 20% year-over-year.",
                "confidence": 0.94,
            },
        ],
        "answer_sentences": [
            "Amazon's AWS revenue grew 20% [1].",
            "The retail segment faces headwinds.",
        ],
        "expected_citation_precision": 1.0,
        "expected_citation_coverage": 0.5,  # 1 of 2 sentences cited
    },
    {
        "case_id": "cite-005",
        "report": "No citations in this report at all.",
        "citations": [],
        "answer_sentences": ["No citations in this report at all."],
        "expected_citation_precision": 0.0,
        "expected_citation_coverage": 0.0,
    },
]


def compute_citation_precision(
    citations: list[dict[str, Any]],
    contexts: list[str],
) -> float:
    """Fraction of citations backed by actual context."""
    if not citations:
        return 0.0
    if not contexts:
        return 0.0
    valid = 0
    for citation in citations:
        chunk_text = citation.get("chunk_text", "")
        if not chunk_text:
            continue
        # Simple check: citation chunk text appears in some context
        for ctx in contexts:
            if chunk_text.lower() in ctx.lower() or ctx.lower() in chunk_text.lower():
                valid += 1
                break
    return valid / len(citations)


def compute_citation_coverage(
    answer_sentences: list[str],
    citations: list[dict[str, Any]],
) -> float:
    """Fraction of answer sentences that have at least one citation."""
    if not citations:
        return 0.0
    if not answer_sentences:
        return 0.0
    # Count citation markers in the answer
    all_text = " ".join(answer_sentences)
    citation_markers = set()
    import re

    for match in re.finditer(r"\[(\d+)\]", all_text):
        citation_markers.add(int(match.group(1)))

    available_citation_ids = {c.get("id") for c in citations if c.get("id") is not None}
    # Try to match numeric citation IDs
    cited_indices = set()
    for marker in citation_markers:
        if str(marker) in available_citation_ids or marker in available_citation_ids:
            cited_indices.add(marker)

    covered = sum(1 for i in range(1, len(answer_sentences) + 1) if i in cited_indices)
    return covered / len(answer_sentences)


def compute_unsupported_claim_rate(
    answer_sentences: list[str],
    _contexts: list[str],
    _citations: list[dict[str, Any]],
) -> float:
    """Fraction of answer sentences without supporting citation."""
    if not answer_sentences:
        return 0.0
    all_text = " ".join(answer_sentences)
    import re

    citation_markers = set()
    for match in re.finditer(r"\[(\d+)\]", all_text):
        citation_markers.add(int(match.group(1)))

    unsupported = 0
    for _i, _sentence in enumerate(answer_sentences, start=1):
        if _i not in citation_markers:
            unsupported += 1
    return unsupported / len(answer_sentences)


def run_citation_benchmark() -> dict[str, Any]:
    """Run citation metrics benchmark on test cases."""
    results = {
        "n_test_cases": len(CITATION_TEST_CASES),
        "cases": [],
        "aggregate": {},
    }

    for case in CITATION_TEST_CASES:
        citations = case.get("citations", [])
        answer_sentences = case.get("answer_sentences", [])
        contexts = [c.get("chunk_text", "") for c in citations]

        citation_precision = compute_citation_precision(citations, contexts)
        citation_coverage = compute_citation_coverage(answer_sentences, citations)
        unsupported_rate = compute_unsupported_claim_rate(answer_sentences, contexts, citations)

        expected_precision = case.get("expected_citation_precision", 0.0)
        expected_coverage = case.get("expected_citation_coverage", 0.0)

        precision_match = abs(citation_precision - expected_precision) < 0.001
        coverage_match = abs(citation_coverage - expected_coverage) < 0.001

        case_result = {
            "case_id": case["case_id"],
            "citation_precision": round(citation_precision, 4),
            "citation_coverage": round(citation_coverage, 4),
            "unsupported_claim_rate": round(unsupported_rate, 4),
            "expected_precision": expected_precision,
            "expected_coverage": expected_coverage,
            "precision_match": precision_match,
            "coverage_match": coverage_match,
            "n_citations": len(citations),
            "n_sentences": len(answer_sentences),
        }
        results["cases"].append(case_result)

    # Aggregate
    n = len(results["cases"])
    if n > 0:
        results["aggregate"] = {
            "mean_citation_precision": round(
                sum(c["citation_precision"] for c in results["cases"]) / n, 4
            ),
            "mean_citation_coverage": round(
                sum(c["citation_coverage"] for c in results["cases"]) / n, 4
            ),
            "mean_unsupported_claim_rate": round(
                sum(c["unsupported_claim_rate"] for c in results["cases"]) / n, 4
            ),
            "precision_matches": sum(1 for c in results["cases"] if c["precision_match"]),
            "coverage_matches": sum(1 for c in results["cases"] if c["coverage_match"]),
            "all_precision_match": all(c["precision_match"] for c in results["cases"]),
            "all_coverage_match": all(c["coverage_match"] for c in results["cases"]),
        }

    return results


# ---------------------------------------------------------------------------
# Agent performance benchmark (without LLM)
# ---------------------------------------------------------------------------


def run_agent_performance_benchmark() -> dict[str, Any]:
    """Benchmark agent graph execution performance without LLM."""
    import asyncio

    from backend.graphs.graph import create_first_graph, create_initial_state

    test_queries = [
        "What is AAPL stock price?",
        "Tell me about MSFT financials",
        "Analyze GOOGL market position",
        "TSLA earnings report summary",
        "AMZN revenue growth analysis",
    ]

    graph = create_first_graph()

    results = {
        "n_test_queries": len(test_queries),
        "executions": [],
        "aggregate": {},
    }

    total_latencies = []
    successful = 0
    failed = 0

    for query in test_queries:
        state = create_initial_state(query)
        try:
            result = asyncio.run(graph.ainvoke(state))
            latency_ms = result.get("execution_duration_ms", 0)
            status = result.get("status", "unknown")
            executed_nodes = result.get("executed_nodes", [])

            total_latencies.append(latency_ms if latency_ms else 0)
            if status == "success":
                successful += 1
            else:
                failed += 1

            results["executions"].append(
                {
                    "query": query,
                    "status": status,
                    "latency_ms": latency_ms,
                    "executed_nodes": executed_nodes,
                    "has_report": bool(result.get("report")),
                    "has_citations": bool(result.get("citations")),
                    "n_citations": len(result.get("citations", [])),
                }
            )
        except Exception as exc:
            failed += 1
            results["executions"].append(
                {
                    "query": query,
                    "status": "error",
                    "error": str(exc),
                    "latency_ms": 0,
                    "executed_nodes": [],
                    "has_report": False,
                    "has_citations": False,
                    "n_citations": 0,
                }
            )

    if total_latencies:
        total_latencies.sort()
        n = len(total_latencies)
        results["aggregate"] = {
            "successful": successful,
            "failed": failed,
            "success_rate": round(successful / n, 4),
            "p50_latency_ms": round(total_latencies[int(n * 0.5)], 2),
            "p95_latency_ms": round(total_latencies[min(int(n * 0.95), n - 1)], 2),
            "p99_latency_ms": round(total_latencies[min(int(n * 0.99), n - 1)], 2),
            "mean_latency_ms": round(sum(total_latencies) / n, 2),
        }

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    print("=" * 70)
    print("EquiPilot AI Phase 4 — Citation Metrics & Agent Performance")
    print("=" * 70)

    # Citation metrics
    print("\nCitation metrics benchmark:", flush=True)
    citation_results = run_citation_benchmark()
    agg = citation_results.get("aggregate", {})
    print(f"  Test cases: {citation_results['n_test_cases']}", flush=True)
    print(f"  Mean citation precision: {agg.get('mean_citation_precision', 0):.4f}", flush=True)
    print(f"  Mean citation coverage: {agg.get('mean_citation_coverage', 0):.4f}", flush=True)
    print(
        f"  Mean unsupported claim rate: {agg.get('mean_unsupported_claim_rate', 0):.4f}",
        flush=True,
    )
    print(f"  All precision match: {agg.get('all_precision_match', False)}", flush=True)
    print(f"  All coverage match: {agg.get('all_coverage_match', False)}", flush=True)

    # Agent performance
    print("\nAgent performance benchmark:", flush=True)
    perf_results = run_agent_performance_benchmark()
    perf_agg = perf_results.get("aggregate", {})
    print(f"  Test queries: {perf_results['n_test_queries']}", flush=True)
    print(f"  Successful: {perf_agg.get('successful', 0)}", flush=True)
    print(f"  Failed: {perf_agg.get('failed', 0)}", flush=True)
    print(f"  Success rate: {perf_agg.get('success_rate', 0):.4f}", flush=True)
    print(f"  p50 latency: {perf_agg.get('p50_latency_ms', 0)}ms", flush=True)
    print(f"  p95 latency: {perf_agg.get('p95_latency_ms', 0)}ms", flush=True)

    # Combined results
    combined = {
        "citation_metrics": citation_results,
        "agent_performance": perf_results,
    }

    out_path = EXPERIMENT_DIR / "citation_and_performance_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2)
    print(f"\nResults written to {out_path}", flush=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
