"""Tests for EquiPilot AI financial analysis calculations."""

from __future__ import annotations

from backend.services.financial_analysis import (
    compute_all_financials,
    current_ratio,
    debt_to_equity,
    ebitda_margin,
    eps_growth,
    ev_ebitda,
    free_cash_flow,
    gross_margin,
    net_margin,
    operating_margin,
    pb_ratio,
    pe_ratio,
    ps_ratio,
    revenue_growth,
    roce,
    roe,
    safe_divide,
    validate_financial_metrics,
)
from backend.services.report_evaluator import (
    evaluate_citation_coverage,
    evaluate_citation_precision,
    evaluate_completeness,
    evaluate_numerical_correctness,
    evaluate_unsupported_claim_rate,
)


class TestSafeDivide:
    def test_normal_division(self):
        assert safe_divide(10, 2) == 5.0

    def test_zero_denominator(self):
        assert safe_divide(10, 0) is None

    def test_none_numerator(self):
        assert safe_divide(None, 5) is None

    def test_none_denominator(self):
        assert safe_divide(10, None) is None

    def test_both_none(self):
        assert safe_divide(None, None) is None


class TestRevenueGrowth:
    def test_positive_growth(self):
        result = revenue_growth(115, 100)
        assert result == 0.15

    def test_negative_growth(self):
        result = revenue_growth(85, 100)
        assert result == -0.15

    def test_zero_previous(self):
        assert revenue_growth(100, 0) is None

    def test_none_previous(self):
        assert revenue_growth(100, None) is None


class TestGrossMargin:
    def test_standard(self):
        assert gross_margin(40, 100) == 0.4

    def test_zero_revenue(self):
        assert gross_margin(40, 0) is None

    def test_none_values(self):
        assert gross_margin(None, 100) is None
        assert gross_margin(40, None) is None


class TestOperatingMargin:
    def test_standard(self):
        assert operating_margin(20, 100) == 0.2

    def test_zero_revenue(self):
        assert operating_margin(20, 0) is None


class TestNetMargin:
    def test_standard(self):
        assert net_margin(15, 100) == 0.15


class TestEbitdaMargin:
    def test_standard(self):
        assert ebitda_margin(30, 100) == 0.3


class TestEpsGrowth:
    def test_positive_growth(self):
        assert eps_growth(3.5, 3.0) == (3.5 - 3.0) / 3.0

    def test_zero_previous(self):
        assert eps_growth(3.5, 0) is None


class TestRoe:
    def test_standard(self):
        assert roe(20, 100) == 0.2

    def test_zero_equity(self):
        assert roe(20, 0) is None


class TestRoce:
    def test_standard(self):
        assert roce(30, 150) == 0.2


class TestDebtToEquity:
    def test_standard(self):
        assert debt_to_equity(60, 100) == 0.6

    def test_zero_equity(self):
        assert debt_to_equity(60, 0) is None


class TestCurrentRatio:
    def test_standard(self):
        assert current_ratio(200, 100) == 2.0


class TestFreeCashFlow:
    def test_standard(self):
        assert free_cash_flow(100, 30) == 70

    def test_negative_fcf(self):
        assert free_cash_flow(20, 50) == -30


class TestPeRatio:
    def test_standard(self):
        assert pe_ratio(100, 5) == 20.0

    def test_zero_eps(self):
        assert pe_ratio(100, 0) is None


class TestPbRatio:
    def test_standard(self):
        assert pb_ratio(100, 20) == 5.0


class TestPsRatio:
    def test_standard(self):
        assert ps_ratio(500, 100) == 5.0


class TestEvEbitda:
    def test_standard(self):
        assert ev_ebitda(500, 50) == 10.0


class TestComputeAllFinancials:
    def test_complete_dataset(self):
        result = compute_all_financials(
            revenue=1000,
            previous_revenue=800,
            gross_profit=400,
            operating_income=200,
            net_income=150,
            ebitda=250,
            current_eps=5.0,
            previous_eps=4.0,
            shareholders_equity=500,
            ebit=200,
            capital_employed=1000,
            total_debt=300,
            current_assets=400,
            current_liabilities=200,
            operating_cash_flow=180,
            capital_expenditures=50,
            market_price=150,
            book_value_per_share=30,
            market_cap=5000,
            enterprise_value=5500,
        )
        assert result["revenue_growth"] == 0.25
        assert result["gross_margin"] == 0.4
        assert result["operating_margin"] == 0.2
        assert result["net_margin"] == 0.15
        assert result["ebitda_margin"] == 0.25
        assert result["eps_growth"] == 0.25
        assert result["roe"] == 0.3
        assert result["roce"] == 0.2
        assert result["debt_to_equity"] == 0.6
        assert result["current_ratio"] == 2.0
        assert result["free_cash_flow"] == 130
        assert result["pe_ratio"] == 30.0
        assert result["pb_ratio"] == 5.0
        assert result["ps_ratio"] == 5.0
        assert result["ev_ebitda"] == 22.0

    def test_partial_dataset(self):
        result = compute_all_financials(revenue=100, gross_profit=40)
        assert result["gross_margin"] == 0.4
        assert result["revenue_growth"] is None
        assert result["net_margin"] is None
        assert result["roe"] is None

    def test_empty_dataset(self):
        result = compute_all_financials()
        assert all(v is None for v in result.values())


class TestValidateFinancialMetrics:
    def test_valid_metrics(self):
        result = validate_financial_metrics(
            {
                "gross_margin": 0.4,
                "net_margin": 0.15,
                "roe": 0.2,
                "debt_to_equity": 0.5,
                "current_ratio": 2.0,
                "pe_ratio": 20.0,
            }
        )
        for name, val in result.items():
            assert val["valid"] is True, f"{name} should be valid: {val['warnings']}"

    def test_invalid_margin(self):
        result = validate_financial_metrics({"gross_margin": 1.5})
        assert result["gross_margin"]["valid"] is False
        assert "outside [-1, 1]" in result["gross_margin"]["warnings"][0]

    def test_negative_debt_to_equity(self):
        result = validate_financial_metrics({"debt_to_equity": -0.5})
        assert result["debt_to_equity"]["valid"] is False

    def test_none_value(self):
        result = validate_financial_metrics({"roe": None})
        assert result["roe"]["valid"] is False

    def test_high_pe(self):
        result = validate_financial_metrics({"pe_ratio": 2000})
        assert result["pe_ratio"]["valid"] is True
        assert "unusually high" in result["pe_ratio"]["warnings"][0]


class TestFinancialEdgeCases:
    """Edge case tests for financial calculations."""

    def test_zero_values(self):
        assert revenue_growth(0, 100) == -1.0
        assert gross_margin(0, 100) == 0.0
        assert net_margin(0, 100) == 0.0

    def test_very_large_values(self):
        result = gross_margin(1_000_000_000, 2_000_000_000)
        assert result == 0.5

    def test_tiny_values(self):
        result = gross_margin(0.001, 0.002)
        assert result == 0.5

    def test_negative_revenue_growth(self):
        result = revenue_growth(50, 100)
        assert result == -0.5

    def test_negative_eps_growth(self):
        result = eps_growth(1.0, 2.0)
        assert result == -0.5

    def test_negative_roe(self):
        result = roe(-100, 500)
        assert result == -0.2

    def test_zero_current_ratio(self):
        assert current_ratio(0, 100) == 0.0

    def test_negative_free_cash_flow(self):
        result = free_cash_flow(10, 50)
        assert result == -40

    def test_precision_rounding(self):
        result = gross_margin(1, 3)
        assert abs(result - 0.333333) < 0.001

    def test_all_none_compute_all(self):
        result = compute_all_financials()
        assert all(v is None for v in result.values())


class TestFinancialDataValidation:
    """Validate financial calculations against known company data."""

    def test_apple_like_financials(self):
        """Validate against Apple Inc.-like financials (approximate public data)."""
        result = compute_all_financials(
            revenue=394_328_000_000,
            previous_revenue=365_817_000_000,
            gross_profit=171_792_000_000,
            operating_income=119_437_000_000,
            net_income=99_803_000_000,
            ebitda=129_000_000_000,
            current_eps=6.11,
            previous_eps=5.61,
            shareholders_equity=65_339_000_000,
            ebit=119_437_000_000,
            capital_employed=352_756_000_000,
            total_debt=124_693_000_000,
            current_assets=135_356_000_000,
            current_liabilities=153_885_000_000,
            operating_cash_flow=110_543_000_000,
            capital_expenditures=10_957_000_000,
            market_price=150.0,
            book_value_per_share=4.25,
            market_cap=2_500_000_000_000,
            enterprise_value=2_600_000_000_000,
        )

        # Revenue growth should be positive (~7.8%)
        assert result["revenue_growth"] is not None
        assert 0.05 < result["revenue_growth"] < 0.10

        # Gross margin should be ~43%
        assert result["gross_margin"] is not None
        assert 0.40 < result["gross_margin"] < 0.45

        # Net margin should be ~25%
        assert result["net_margin"] is not None
        assert 0.20 < result["net_margin"] < 0.30

        # ROE should be > 1.0 (Apple has high ROE due to low equity)
        assert result["roe"] is not None
        assert result["roe"] > 1.0

    def test_validation_catches_absurd_values(self):
        """Ensure validation flags impossible financial values."""
        result = validate_financial_metrics({"gross_margin": 2.5})
        assert result["gross_margin"]["valid"] is False

        result = validate_financial_metrics({"current_ratio": -5.0})
        assert result["current_ratio"]["valid"] is False

        result = validate_financial_metrics({"pe_ratio": -10.0})
        assert result["pe_ratio"]["valid"] is False


class TestReportEvaluatorEdgeCases:
    """Edge case tests for report evaluation."""

    def test_empty_report(self):
        result = evaluate_completeness("")
        assert result == 0.0

    def test_empty_citations(self):
        assert evaluate_citation_precision([]) == 0.0
        assert evaluate_citation_coverage("text", []) == 0.0
        assert evaluate_unsupported_claim_rate("text", []) == 1.0

    def test_report_with_all_sections(self):
        report = """
        Company Overview: TechCorp Inc.
        Financial Performance: Revenue grew 20%.
        Growth Analysis: User base expanded 30%.
        Profitability: Net margin 25%.
        Balance Sheet Risk: Debt-to-equity 0.3.
        Cash Flow Analysis: Operating cash flow $50M.
        Risk Factors: Market competition.
        Bull Case: Strong brand moat.
        Bear Case: High valuation.
        Neutral Case: Stable outlook.
        """
        result = evaluate_completeness(report)
        assert result >= 0.9

    def test_numerical_accuracy_with_tolerance(self):
        report = "Revenue was approximately $100 million."
        financial_data = {"revenue": 100.0}
        result = evaluate_numerical_correctness(report, financial_data)
        assert result["numerical_accuracy"] >= 0.5

    def test_numerical_accuracy_wrong_value(self):
        report = "Revenue was $1 billion."
        financial_data = {"revenue": 100.0}
        result = evaluate_numerical_correctness(report, financial_data)
        assert result["numerical_accuracy"] == 0.0
