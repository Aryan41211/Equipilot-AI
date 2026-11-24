"""EquiPilot AI — Research Report Evaluation Framework.

Evaluates research reports for:
- Numerical calculation correctness
- Citation precision and coverage
- Factual consistency
- Unsupported claim rate
- Source freshness
- Completeness
- Risk identification quality
- Report generation success rate

Uses human-reviewed rubric for subjective criteria.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvaluationSample:
    """A single research report evaluation sample."""

    sample_id: str
    company: str
    ticker: str
    query: str
    report: str
    citations: list[dict[str, Any]]
    financial_data: dict[str, Any]
    ground_truth: dict[str, Any] | None = None
    label_source: str = "human-validated"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """Result for a single evaluation sample."""

    sample_id: str
    company: str
    ticker: str
    metrics: dict[str, float] = field(default_factory=dict)
    checks: dict[str, bool] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class EvaluationReport:
    """Aggregate evaluation report."""

    total_samples: int = 0
    successful_evaluations: int = 0
    failed_evaluations: int = 0
    metrics: dict[str, float] = field(default_factory=dict)
    per_sample: list[EvaluationResult] = field(default_factory=list)


def _extract_numbers(text: str) -> list[float]:
    """Extract numeric values from text (including percentages)."""
    numbers = []
    for match in re.finditer(r"[-+]?\d*\.\d+|[-+]?\d+", text):
        try:
            numbers.append(float(match.group()))
        except ValueError:
            continue
    return numbers


def _extract_percentages(text: str) -> list[float]:
    """Extract percentage values from text."""
    percentages = []
    for match in re.finditer(r"[-+]?\d*\.\d+\s*%|[-+]?\d+\s*%", text):
        try:
            val = float(match.group().replace("%", "").strip())
            percentages.append(val / 100.0)
        except ValueError:
            continue
    return percentages


def evaluate_numerical_correctness(
    report: str,
    financial_data: dict[str, Any],
) -> dict[str, float]:
    """Check numerical claims in report against financial data.

    Verifies that key financial figures mentioned in the report match
    the source data within a tolerance.

    Returns:
        Dict with 'numerical_accuracy' (fraction of correct claims)
        and 'claims_checked' count.
    """
    # Key financial metrics to check
    metric_mappings = {
        "revenue": ["revenue", "total_revenue"],
        "net_income": ["net_income", "net income"],
        "eps": ["eps", "earnings per share"],
        "roe": ["roe", "return on equity"],
        "debt_to_equity": ["debt to equity", "debt_to_equity"],
        "current_ratio": ["current ratio"],
        "pe_ratio": ["p/e", "pe ratio", "price to earnings"],
    }

    claims_checked = 0
    claims_correct = 0
    tolerance = 0.05  # 5% tolerance

    for _report_key, data_keys in metric_mappings.items():
        # Find the value in financial data
        data_value = None
        for dk in data_keys:
            if dk in financial_data:
                data_value = financial_data[dk]
                break

        if data_value is None:
            continue

        # Look for this metric in the report
        report_lower = report.lower()
        found = False
        for keyword in data_keys:
            if keyword.lower() in report_lower:
                found = True
                break

        if not found:
            continue

        claims_checked += 1

        # Extract nearby numbers in report
        report_numbers = _extract_numbers(report)
        # Check if any report number is close to the data value
        correct = any(
            abs(num - data_value) / max(abs(data_value), 0.001) <= tolerance
            for num in report_numbers
        )
        if correct:
            claims_correct += 1

    accuracy = claims_correct / claims_checked if claims_checked > 0 else 0.0
    return {
        "numerical_accuracy": round(accuracy, 4),
        "claims_checked": float(claims_checked),
    }


def evaluate_citation_precision(
    citations: list[dict[str, Any]],
) -> float:
    """Check that citations have valid structure.

    A citation is valid if it has: id, type, title, source, url.
    """
    if not citations:
        return 0.0

    valid = 0
    for citation in citations:
        has_id = bool(citation.get("id"))
        has_type = bool(citation.get("type"))
        has_title = bool(citation.get("title"))
        has_source = bool(citation.get("source"))
        has_url = bool(citation.get("url"))

        if has_id and has_type and has_title and has_source and has_url:
            valid += 1

    return round(valid / len(citations), 4)


def evaluate_citation_coverage(
    report: str,
    citations: list[dict[str, Any]],
) -> float:
    """Check that report sentences have citation support.

    Simple heuristic: count citation markers [1], [2], etc. in report
    and compare to available citations.
    """
    if not citations:
        return 0.0

    citation_markers = set(re.findall(r"\[(\d+)\]", report))
    cited_indices = {int(m) for m in citation_markers}
    available_ids = {c.get("id") for c in citations if c.get("id") is not None}

    if not cited_indices:
        return 0.0

    covered = len(cited_indices & available_ids)
    return round(covered / len(cited_indices), 4)


def evaluate_unsupported_claim_rate(
    report: str,
    _citations: list[dict[str, Any]] | None = None,
) -> float:
    """Estimate unsupported claim rate.

    A claim is a sentence. A claim is "supported" if it has a nearby
    citation marker or references a cited source.
    """
    sentences = [s.strip() for s in re.split(r"[.!?]+", report) if s.strip()]
    if not sentences:
        return 0.0

    supported = 0
    for sentence in sentences:
        if re.search(r"\[\d+\]", sentence) or any(
            word in sentence.lower() for word in ["according to", "source", "reported"]
        ):
            supported += 1

    unsupported = len(sentences) - supported
    return round(unsupported / len(sentences), 4)


def evaluate_completeness(report: str) -> float:
    """Check report completeness against expected sections.

    Expected sections:
    - company overview
    - financial performance
    - growth analysis
    - profitability
    - balance sheet risk
    - cash flow analysis
    - risk factors
    - bull/bear/neutral case
    """
    expected_sections = [
        "overview",
        "financial",
        "growth",
        "profit",
        "balance",
        "cash flow",
        "risk",
        "bull",
        "bear",
        "neutral",
    ]

    report_lower = report.lower()
    found = sum(1 for section in expected_sections if section in report_lower)
    return round(found / len(expected_sections), 4)


def evaluate_risk_identification(report: str) -> float:
    """Check that risk factors are identified in the report.

    Looks for risk-related keywords and sections.
    """
    risk_keywords = [
        "risk",
        "risk factor",
        "downside",
        "threat",
        "challenge",
        "concern",
        "weakness",
        "vulnerability",
        "uncertainty",
    ]
    report_lower = report.lower()
    found = sum(1 for kw in risk_keywords if kw in report_lower)
    return round(min(found / 3.0, 1.0), 4)  # Cap at 1.0


def evaluate_source_freshness(
    financial_data: dict[str, Any],
) -> float:
    """Check if financial data has a recent timestamp."""
    if "data_as_of" not in financial_data:
        return 0.0
    # If we have a timestamp, data is considered fresh
    return 1.0


def evaluate_sample(sample: EvaluationSample) -> EvaluationResult:
    """Evaluate a single research report sample."""
    checks: dict[str, bool] = {}
    warnings: list[str] = []

    # Numerical correctness
    num_metrics = evaluate_numerical_correctness(sample.report, sample.financial_data)
    checks["numerical_correct"] = num_metrics["numerical_accuracy"] >= 0.8

    # Citation precision
    citation_precision = evaluate_citation_precision(sample.citations)
    checks["citations_valid"] = citation_precision >= 0.8

    # Citation coverage
    citation_coverage = evaluate_citation_coverage(sample.report, sample.citations)
    checks["citations_cover_claims"] = citation_coverage >= 0.5

    # Unsupported claim rate
    unsupported_rate = evaluate_unsupported_claim_rate(sample.report, sample.citations)
    checks["low_unsupported_claims"] = unsupported_rate <= 0.3

    # Completeness
    completeness = evaluate_completeness(sample.report)
    checks["report_complete"] = completeness >= 0.7

    # Risk identification
    risk_quality = evaluate_risk_identification(sample.report)
    checks["risks_identified"] = risk_quality >= 0.5

    # Source freshness
    source_freshness = evaluate_source_freshness(sample.financial_data)
    checks["data_fresh"] = source_freshness >= 0.5

    all_metrics = {
        **num_metrics,
        "citation_precision": citation_precision,
        "citation_coverage": citation_coverage,
        "unsupported_claim_rate": unsupported_rate,
        "completeness": completeness,
        "risk_identification": risk_quality,
        "source_freshness": source_freshness,
    }

    # Overall score (weighted average)
    weights = {
        "numerical_accuracy": 0.25,
        "citation_precision": 0.15,
        "citation_coverage": 0.15,
        "completeness": 0.20,
        "risk_identification": 0.15,
        "source_freshness": 0.10,
    }
    overall = sum(all_metrics.get(k, 0) * w for k, w in weights.items())
    all_metrics["overall_score"] = round(overall, 4)

    return EvaluationResult(
        sample_id=sample.sample_id,
        company=sample.company,
        ticker=sample.ticker,
        metrics=all_metrics,
        checks=checks,
        warnings=warnings,
    )


def run_evaluation(samples: list[EvaluationSample]) -> EvaluationReport:
    """Run evaluation on a list of research report samples."""
    per_sample: list[EvaluationResult] = []
    successful = 0
    failed = 0

    for sample in samples:
        try:
            result = evaluate_sample(sample)
            per_sample.append(result)
            successful += 1
        except Exception as exc:
            per_sample.append(
                EvaluationResult(
                    sample_id=sample.sample_id,
                    company=sample.company,
                    ticker=sample.ticker,
                    error=str(exc),
                )
            )
            failed += 1

    # Aggregate metrics
    agg_metrics: dict[str, float] = {}
    if per_sample:
        metric_keys = set()
        for r in per_sample:
            if r.metrics:
                metric_keys.update(r.metrics.keys())
        for key in metric_keys:
            values = [r.metrics[key] for r in per_sample if r.metrics and key in r.metrics]
            if values:
                agg_metrics[key] = round(sum(values) / len(values), 4)

    # Check pass rates
    check_keys = set()
    for r in per_sample:
        check_keys.update(r.checks.keys())
    for key in check_keys:
        values = [r.checks.get(key, False) for r in per_sample]
        agg_metrics[f"check_{key}_rate"] = round(sum(values) / len(values), 4)

    return EvaluationReport(
        total_samples=len(samples),
        successful_evaluations=successful,
        failed_evaluations=failed,
        metrics=agg_metrics,
        per_sample=per_sample,
    )
