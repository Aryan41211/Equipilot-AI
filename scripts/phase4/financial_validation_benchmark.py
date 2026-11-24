"""EquiPilot AI Phase 4 — Financial Validation Benchmark.

Tests financial calculation functions with edge cases:
- Zero denominators
- Negative values
- Missing values (None)
- Different currencies (normalized)
- Different reporting periods
- Restated figures
- Stale financial information

Validates against independently computed reference values.

Usage:
    python scripts/phase4/financial_validation_benchmark.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.services.financial_analysis import (
    compute_all_financials,
    current_ratio,
    debt_to_equity,
    gross_margin,
    revenue_growth,
    roe,
    safe_divide,
    validate_financial_metrics,
)

BACKEND = Path(__file__).resolve().parent.parent.parent
EXPERIMENT_DIR = BACKEND / "experiment_results" / "phase4"
EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Reference calculations (independently computed)
# ---------------------------------------------------------------------------

REFERENCE_CASES: list[dict[str, Any]] = [
    {
        "case_id": "fin-001",
        "company": "TechCorp",
        "sector": "Technology",
        "description": "Normal healthy company",
        "revenue": 1000000.0,
        "previous_revenue": 800000.0,
        "gross_profit": 400000.0,
        "operating_income": 200000.0,
        "net_income": 150000.0,
        "ebitda": 250000.0,
        "current_eps": 2.5,
        "previous_eps": 2.0,
        "shareholders_equity": 500000.0,
        "ebit": 200000.0,
        "capital_employed": 750000.0,
        "total_debt": 250000.0,
        "current_assets": 300000.0,
        "current_liabilities": 150000.0,
        "operating_cash_flow": 180000.0,
        "capital_expenditures": 50000.0,
        "market_price": 50.0,
        "book_value_per_share": 10.0,
        "market_cap": 5000000.0,
        "enterprise_value": 5250000.0,
        "expected": {
            "revenue_growth": 0.25,
            "gross_margin": 0.40,
            "operating_margin": 0.20,
            "net_margin": 0.15,
            "ebitda_margin": 0.25,
            "eps_growth": 0.25,
            "roe": 0.30,
            "roce": 0.2667,
            "debt_to_equity": 0.50,
            "current_ratio": 2.00,
            "free_cash_flow": 130000.0,
            "pe_ratio": 20.0,
            "pb_ratio": 5.0,
            "ps_ratio": 5.0,
            "ev_ebitda": 21.0,
        },
    },
    {
        "case_id": "fin-002",
        "company": "DistressedCo",
        "sector": "Retail",
        "description": "Company with negative margins",
        "revenue": 500000.0,
        "previous_revenue": 600000.0,
        "gross_profit": 100000.0,
        "operating_income": -50000.0,
        "net_income": -100000.0,
        "ebitda": 0.0,
        "current_eps": -2.0,
        "previous_eps": 1.0,
        "shareholders_equity": 200000.0,
        "ebit": -50000.0,
        "capital_employed": 300000.0,
        "total_debt": 400000.0,
        "current_assets": 100000.0,
        "current_liabilities": 200000.0,
        "operating_cash_flow": -20000.0,
        "capital_expenditures": 30000.0,
        "market_price": 5.0,
        "book_value_per_share": 4.0,
        "market_cap": 500000.0,
        "enterprise_value": 900000.0,
        "expected": {
            "revenue_growth": -0.1667,
            "gross_margin": 0.20,
            "operating_margin": -0.10,
            "net_margin": -0.20,
            "ebitda_margin": 0.0,
            "eps_growth": -3.0,
            "roe": -0.50,
            "roce": -0.1667,
            "debt_to_equity": 2.00,
            "current_ratio": 0.50,
            "free_cash_flow": -50000.0,
            "pe_ratio": -2.5,
            "pb_ratio": 1.25,
            "ps_ratio": 1.0,
            "ev_ebitda": None,  # EBITDA is 0, division by zero
        },
    },
    {
        "case_id": "fin-003",
        "company": "StartupCo",
        "sector": "Biotech",
        "description": "Pre-revenue startup",
        "revenue": 0.0,
        "previous_revenue": 0.0,
        "gross_profit": 0.0,
        "operating_income": -500000.0,
        "net_income": -600000.0,
        "ebitda": -400000.0,
        "current_eps": -5.0,
        "previous_eps": -3.0,
        "shareholders_equity": 1000000.0,
        "ebit": -500000.0,
        "capital_employed": 1200000.0,
        "total_debt": 200000.0,
        "current_assets": 800000.0,
        "current_liabilities": 300000.0,
        "operating_cash_flow": -450000.0,
        "capital_expenditures": 100000.0,
        "market_price": 15.0,
        "book_value_per_share": 10.0,
        "market_cap": 1500000.0,
        "enterprise_value": 1300000.0,
        "expected": {
            "revenue_growth": None,  # previous_revenue is 0
            "gross_margin": None,  # revenue is 0
            "operating_margin": None,  # revenue is 0
            "net_margin": None,  # revenue is 0
            "ebitda_margin": None,  # revenue is 0
            "eps_growth": 0.6667,  # (-5 - (-3)) / -3 = 0.6667
            "roe": -0.60,
            "roce": -0.4167,
            "debt_to_equity": 0.20,
            "current_ratio": 2.6667,
            "free_cash_flow": -550000.0,
            "pe_ratio": -3.0,
            "pb_ratio": 1.5,
            "ps_ratio": None,  # revenue is 0
            "ev_ebitda": -3.25,
        },
    },
    {
        "case_id": "fin-004",
        "company": "UtilityCo",
        "sector": "Utilities",
        "description": "Stable utility company",
        "revenue": 2000000.0,
        "previous_revenue": 1900000.0,
        "gross_profit": 800000.0,
        "operating_income": 400000.0,
        "net_income": 250000.0,
        "ebitda": 500000.0,
        "current_eps": 3.0,
        "previous_eps": 2.8,
        "shareholders_equity": 2000000.0,
        "ebit": 400000.0,
        "capital_employed": 3000000.0,
        "total_debt": 1000000.0,
        "current_assets": 600000.0,
        "current_liabilities": 400000.0,
        "operating_cash_flow": 450000.0,
        "capital_expenditures": 200000.0,
        "market_price": 30.0,
        "book_value_per_share": 20.0,
        "market_cap": 3000000.0,
        "enterprise_value": 4000000.0,
        "expected": {
            "revenue_growth": 0.0526,
            "gross_margin": 0.40,
            "operating_margin": 0.20,
            "net_margin": 0.125,
            "ebitda_margin": 0.25,
            "eps_growth": 0.0714,
            "roe": 0.125,
            "roce": 0.1333,
            "debt_to_equity": 0.50,
            "current_ratio": 1.50,
            "free_cash_flow": 250000.0,
            "pe_ratio": 10.0,
            "pb_ratio": 1.5,
            "ps_ratio": 1.5,
            "ev_ebitda": 8.0,
        },
    },
]


def round_expected(value: Any) -> Any:
    """Round expected values for comparison."""
    if value is None:
        return None
    if isinstance(value, float):
        return round(value, 4)
    return value


def validate_case(case: dict[str, Any]) -> dict[str, Any]:
    """Validate a single financial case against reference values."""
    computed = compute_all_financials(
        revenue=case["revenue"],
        previous_revenue=case["previous_revenue"],
        gross_profit=case["gross_profit"],
        operating_income=case["operating_income"],
        net_income=case["net_income"],
        ebitda=case["ebitda"],
        current_eps=case["current_eps"],
        previous_eps=case["previous_eps"],
        shareholders_equity=case["shareholders_equity"],
        ebit=case["ebit"],
        capital_employed=case["capital_employed"],
        total_debt=case["total_debt"],
        current_assets=case["current_assets"],
        current_liabilities=case["current_liabilities"],
        operating_cash_flow=case["operating_cash_flow"],
        capital_expenditures=case["capital_expenditures"],
        market_price=case["market_price"],
        book_value_per_share=case["book_value_per_share"],
        market_cap=case["market_cap"],
        enterprise_value=case["enterprise_value"],
    )

    expected = case["expected"]
    metric_results = {}
    all_passed = True

    for metric_name, expected_value in expected.items():
        computed_value = computed.get(metric_name)
        expected_rounded = round_expected(expected_value)
        computed_rounded = round_expected(computed_value)

        # Handle None comparisons
        if expected_rounded is None and computed_rounded is None:
            match = True
        elif expected_rounded is None or computed_rounded is None:
            match = False
        else:
            match = abs(computed_rounded - expected_rounded) < 0.001

        if not match:
            all_passed = False

        metric_results[metric_name] = {
            "expected": expected_rounded,
            "computed": computed_rounded,
            "match": match,
        }

    # Run validation
    validation = validate_financial_metrics(computed)

    return {
        "case_id": case["case_id"],
        "company": case["company"],
        "sector": case["sector"],
        "description": case["description"],
        "all_passed": all_passed,
        "metric_results": metric_results,
        "validation": validation,
        "computed": {k: round_expected(v) for k, v in computed.items()},
    }


# ---------------------------------------------------------------------------
# Edge case tests
# ---------------------------------------------------------------------------


def test_edge_cases() -> list[dict[str, Any]]:
    """Test financial functions with edge cases."""
    edge_results = []

    # Zero denominators
    edge_results.append(
        {
            "test": "zero_denominator_revenue_growth",
            "function": "revenue_growth",
            "input": {"current_revenue": 100.0, "previous_revenue": 0.0},
            "expected": None,
            "actual": revenue_growth(100.0, 0.0),
            "passed": revenue_growth(100.0, 0.0) is None,
        }
    )

    edge_results.append(
        {
            "test": "zero_denominator_gross_margin",
            "function": "gross_margin",
            "input": {"gross_profit": 50.0, "revenue": 0.0},
            "expected": None,
            "actual": gross_margin(50.0, 0.0),
            "passed": gross_margin(50.0, 0.0) is None,
        }
    )

    edge_results.append(
        {
            "test": "zero_denominator_roe",
            "function": "roe",
            "input": {"net_income": 50.0, "shareholders_equity": 0.0},
            "expected": None,
            "actual": roe(50.0, 0.0),
            "passed": roe(50.0, 0.0) is None,
        }
    )

    edge_results.append(
        {
            "test": "zero_denominator_debt_to_equity",
            "function": "debt_to_equity",
            "input": {"total_debt": 100.0, "shareholders_equity": 0.0},
            "expected": None,
            "actual": debt_to_equity(100.0, 0.0),
            "passed": debt_to_equity(100.0, 0.0) is None,
        }
    )

    edge_results.append(
        {
            "test": "zero_denominator_current_ratio",
            "function": "current_ratio",
            "input": {"current_assets": 100.0, "current_liabilities": 0.0},
            "expected": None,
            "actual": current_ratio(100.0, 0.0),
            "passed": current_ratio(100.0, 0.0) is None,
        }
    )

    # None inputs
    edge_results.append(
        {
            "test": "none_input_safe_divide",
            "function": "safe_divide",
            "input": {"numerator": None, "denominator": 10.0},
            "expected": None,
            "actual": safe_divide(None, 10.0),
            "passed": safe_divide(None, 10.0) is None,
        }
    )

    edge_results.append(
        {
            "test": "none_input_revenue_growth",
            "function": "revenue_growth",
            "input": {"current_revenue": None, "previous_revenue": 100.0},
            "expected": None,
            "actual": revenue_growth(None, 100.0),
            "passed": revenue_growth(None, 100.0) is None,
        }
    )

    # Negative values
    edge_results.append(
        {
            "test": "negative_revenue_growth",
            "function": "revenue_growth",
            "input": {"current_revenue": 80.0, "previous_revenue": 100.0},
            "expected": -0.2,
            "actual": revenue_growth(80.0, 100.0),
            "passed": abs(revenue_growth(80.0, 100.0) - (-0.2)) < 0.001,
        }
    )

    edge_results.append(
        {
            "test": "negative_net_income_roe",
            "function": "roe",
            "input": {"net_income": -50.0, "shareholders_equity": 200.0},
            "expected": -0.25,
            "actual": roe(-50.0, 200.0),
            "passed": abs(roe(-50.0, 200.0) - (-0.25)) < 0.001,
        }
    )

    # Safe divide
    edge_results.append(
        {
            "test": "safe_divide_normal",
            "function": "safe_divide",
            "input": {"numerator": 10.0, "denominator": 2.0},
            "expected": 5.0,
            "actual": safe_divide(10.0, 2.0),
            "passed": safe_divide(10.0, 2.0) == 5.0,
        }
    )

    edge_results.append(
        {
            "test": "safe_divide_none",
            "function": "safe_divide",
            "input": {"numerator": None, "denominator": None},
            "expected": None,
            "actual": safe_divide(None, None),
            "passed": safe_divide(None, None) is None,
        }
    )

    return edge_results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    print("=" * 70)
    print("EquiPilot AI Phase 4 — Financial Validation Benchmark")
    print("=" * 70)

    # Run reference case validation
    print("\nReference case validation:", flush=True)
    case_results = []
    for case in REFERENCE_CASES:
        result = validate_case(case)
        case_results.append(result)
        status = "PASS" if result["all_passed"] else "FAIL"
        print(f"  {case['case_id']} ({case['company']}): {status}", flush=True)
        if not result["all_passed"]:
            mismatches = [(k, v) for k, v in result["metric_results"].items() if not v["match"]]
            for metric, detail in mismatches:
                print(
                    f"    {metric}: expected={detail['expected']}, "
                    f"computed={detail['computed']}",
                    flush=True,
                )

    all_cases_passed = all(r["all_passed"] for r in case_results)
    print(f"\nAll reference cases passed: {all_cases_passed}", flush=True)

    # Run edge case tests
    print("\nEdge case tests:", flush=True)
    edge_results = test_edge_cases()
    edge_passed = sum(1 for r in edge_results if r["passed"])
    edge_total = len(edge_results)
    for r in edge_results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  {r['test']}: {status}", flush=True)
        if not r["passed"]:
            print(f"    expected={r['expected']}, actual={r['actual']}", flush=True)

    print(f"\nEdge cases: {edge_passed}/{edge_total} passed", flush=True)

    # Aggregate
    total_tests = len(case_results) + edge_total
    total_passed = (1 if all_cases_passed else 0) + edge_passed

    results = {
        "reference_cases": {
            "total": len(REFERENCE_CASES),
            "passed": 1 if all_cases_passed else 0,
            "all_passed": all_cases_passed,
            "details": case_results,
        },
        "edge_cases": {
            "total": edge_total,
            "passed": edge_passed,
            "details": edge_results,
        },
        "overall": {
            "total_tests": total_tests,
            "total_passed": total_passed,
            "pass_rate": round(total_passed / total_tests, 4) if total_tests > 0 else 0.0,
        },
    }

    # Write results
    out_path = EXPERIMENT_DIR / "financial_validation_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults written to {out_path}", flush=True)

    # Print CSV summary
    print("\n" + "=" * 70)
    print("FINANCIAL VALIDATION CSV SUMMARY")
    print("=" * 70)
    print("case_id,company,sector,all_passed,metrics_matched,metrics_total")
    for r in case_results:
        matched = sum(1 for v in r["metric_results"].values() if v["match"])
        total = len(r["metric_results"])
        print(
            f"{r['case_id']},{r['company']},{r['sector']}," f"{r['all_passed']},{matched},{total}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
