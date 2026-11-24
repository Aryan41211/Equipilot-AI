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
