"""Tests for EquiPilot AI report evaluation framework."""

from __future__ import annotations

from backend.services.report_evaluator import (
    EvaluationSample,
    evaluate_citation_coverage,
    evaluate_citation_precision,
    evaluate_completeness,
    evaluate_numerical_correctness,
    evaluate_risk_identification,
    evaluate_unsupported_claim_rate,
    run_evaluation,
)


class TestNumericalCorrectness:
    def test_matching_values(self):
        report = "Revenue was $100 million and net income was $15 million."
        financial_data = {"revenue": 100.0, "net_income": 15.0}
        result = evaluate_numerical_correctness(report, financial_data)
        assert result["numerical_accuracy"] >= 0.5
        assert result["claims_checked"] >= 1

    def test_no_matching_data(self):
        report = "The company performed well."
        financial_data = {}
        result = evaluate_numerical_correctness(report, financial_data)
        assert result["claims_checked"] == 0
        assert result["numerical_accuracy"] == 0.0


class TestCitationPrecision:
    def test_valid_citations(self):
        citations = [
            {
                "id": 1,
                "type": "market_data",
                "title": "AAPL Price",
                "source": "yfinance",
                "url": "https://example.com/1",
            },
            {
                "id": 2,
                "type": "news",
                "title": "Apple News",
                "source": "NewsAPI",
                "url": "https://example.com/2",
            },
        ]
        result = evaluate_citation_precision(citations)
        assert result == 1.0

    def test_invalid_citations(self):
        citations = [
            {"id": 1, "type": "market_data"},  # missing title, source, url
        ]
        result = evaluate_citation_precision(citations)
        assert result == 0.0

    def test_empty_citations(self):
        assert evaluate_citation_precision([]) == 0.0


class TestCitationCoverage:
    def test_full_coverage(self):
        report = "Revenue grew [1] and margins improved [2]."
        citations = [
            {
                "id": 1,
                "type": "market_data",
                "title": "Rev",
                "source": "yf",
                "url": "https://e.com/1",
            },
            {"id": 2, "type": "news", "title": "News", "source": "NA", "url": "https://e.com/2"},
        ]
        result = evaluate_citation_coverage(report, citations)
        assert result == 1.0

    def test_partial_coverage(self):
        report = "Revenue grew [1] but [3] is missing."
        citations = [
            {
                "id": 1,
                "type": "market_data",
                "title": "Rev",
                "source": "yf",
                "url": "https://e.com/1",
            },
            {"id": 2, "type": "news", "title": "News", "source": "NA", "url": "https://e.com/2"},
        ]
        result = evaluate_citation_coverage(report, citations)
        assert result == 0.5  # 1 out of 2 cited indices available

    def test_no_citations(self):
        assert evaluate_citation_coverage("text", []) == 0.0


class TestUnsupportedClaimRate:
    def test_all_supported(self):
        report = "Revenue grew [1]. Margins improved [2]."
        citations = [
            {"id": 1, "type": "md", "title": "T", "source": "S", "url": "U"},
            {"id": 2, "type": "md", "title": "T", "source": "S", "url": "U"},
        ]
        result = evaluate_unsupported_claim_rate(report, citations)
        assert result == 0.0

    def test_no_citations(self):
        result = evaluate_unsupported_claim_rate("Revenue grew. Margins improved.", [])
        assert result == 1.0


class TestCompleteness:
    def test_complete_report(self):
        report = """
        Company Overview: Apple Inc.
        Financial Performance: Revenue $100B.
        Growth Analysis: Revenue growing 10%.
        Profitability: Net margin 25%.
        Balance Sheet Risk: Debt-to-equity 0.5.
        Cash Flow Analysis: Operating cash flow $50B.
        Risk Factors: Market competition.
        Bull Case: Strong brand.
        Bear Case: High valuation.
        Neutral Case: Stable outlook.
        """
        result = evaluate_completeness(report)
        assert result >= 0.8

    def test_incomplete_report(self):
        result = evaluate_completeness("Just some text.")
        assert result < 0.5


class TestRiskIdentification:
    def test_risks_identified(self):
        report = "Key risks include market competition and regulatory uncertainty."
        result = evaluate_risk_identification(report)
        assert result >= 0.5

    def test_no_risks(self):
        result = evaluate_risk_identification("Everything is great.")
        assert result < 0.5


class TestRunEvaluation:
    def test_basic_evaluation(self):
        samples = [
            EvaluationSample(
                sample_id="eval-001",
                company="Apple Inc.",
                ticker="AAPL",
                query="Analyze AAPL",
                report="Revenue grew [1]. Margins improved [2]. Company Overview: Apple. Financial Performance: strong. Risk Factors: competition.",
                citations=[
                    {
                        "id": 1,
                        "type": "market_data",
                        "title": "AAPL",
                        "source": "yfinance",
                        "url": "https://e.com/1",
                    },
                    {
                        "id": 2,
                        "type": "news",
                        "title": "News",
                        "source": "NewsAPI",
                        "url": "https://e.com/2",
                    },
                ],
                financial_data={"revenue": 100.0, "net_income": 15.0},
            )
        ]
        report = run_evaluation(samples)
        assert report.total_samples == 1
        assert report.successful_evaluations == 1
        assert report.failed_evaluations == 0
        assert "overall_score" in report.metrics

    def test_empty_samples(self):
        report = run_evaluation([])
        assert report.total_samples == 0
        assert report.successful_evaluations == 0
