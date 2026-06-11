"""
Osool Backend — Buyer Tools Tests
----------------------------------
Mortgage calculator (CBE initiative tiers, amortization math, Pro
affordability gating) and installment-vs-cash NPV endpoint contract.
"""

import math
import pytest
from unittest.mock import MagicMock

from app.api.tools_endpoints import (
    InstallmentVsCashRequest,
    MortgageRequest,
    _max_principal,
    _monthly_payment,
    installment_vs_cash,
    mortgage_calculator,
)
from app.services.interest_rate import InterestRateService


def _request():
    """Real starlette Request — slowapi's limiter rejects mocks."""
    from starlette.requests import Request as StarletteRequest

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/tools/mortgage",
        "headers": [],
        "query_string": b"",
        "client": ("203.0.113.50", 1234),
        "server": ("testserver", 80),
        "scheme": "http",
    }
    return StarletteRequest(scope)


class TestMortgageMath:
    def test_known_amortization_fixture(self):
        """2.4M over 15y at 3% → ≈ 16,574 EGP/month (standard annuity)."""
        payment = _monthly_payment(2_400_000, 3.0, 15)
        assert math.isclose(payment, 16_574.03, rel_tol=1e-3)

    def test_zero_rate_divides_evenly(self):
        assert _monthly_payment(120_000, 0.0, 10) == pytest.approx(1_000.0)

    def test_max_principal_inverts_payment(self):
        principal = 2_400_000
        payment = _monthly_payment(principal, 8.0, 20)
        assert _max_principal(payment, 8.0, 20) == pytest.approx(principal, rel=1e-6)

    def test_eligibility_tiers(self):
        assert InterestRateService.eligible_tier(10_000, 2_000_000) == "initiative_low"
        assert InterestRateService.eligible_tier(30_000, 2_000_000) == "initiative_middle"
        assert InterestRateService.eligible_tier(100_000, 2_000_000) == "market"
        # Over the unit-price cap → market regardless of income
        assert InterestRateService.eligible_tier(10_000, 5_000_000) == "market"


class TestMortgageEndpoint:
    @pytest.mark.asyncio
    async def test_three_tiers_with_eligibility_flags(self):
        result = await mortgage_calculator(
            _request(),
            MortgageRequest(
                unit_price_egp=2_000_000,
                down_payment_egp=400_000,
                years=15,
                monthly_income_egp=10_000,
            ),
            current_user=None,
        )
        assert [t["id"] for t in result["tiers"]] == [
            "initiative_low", "initiative_middle", "market",
        ]
        assert result["best_eligible_tier"] == "initiative_low"
        low = result["tiers"][0]
        assert low["eligible"] is True
        # Subsidized 3% must be far cheaper than the 25% market rate
        market = result["tiers"][2]
        assert low["monthly_payment_egp"] < market["monthly_payment_egp"] / 2

    @pytest.mark.asyncio
    async def test_free_user_gets_gated_affordability(self):
        free_user = MagicMock()
        free_user.subscription_tier = "free"
        result = await mortgage_calculator(
            _request(),
            MortgageRequest(
                unit_price_egp=2_000_000,
                down_payment_egp=400_000,
                years=15,
                monthly_income_egp=20_000,
            ),
            current_user=free_user,
        )
        assert result.get("affordability_gated") is True
        assert "affordability" not in result

    @pytest.mark.asyncio
    async def test_premium_user_gets_affordability_block(self):
        pro_user = MagicMock()
        pro_user.subscription_tier = "premium"
        result = await mortgage_calculator(
            _request(),
            MortgageRequest(
                unit_price_egp=2_000_000,
                down_payment_egp=400_000,
                years=15,
                monthly_income_egp=20_000,
            ),
            current_user=pro_user,
        )
        afford = result["affordability"]
        assert afford["income_ceiling_egp"] == pytest.approx(8_000.0)
        assert isinstance(afford["affordable"], bool)
        assert afford["max_affordable_unit_price_egp"] > 0

    @pytest.mark.asyncio
    async def test_expensive_unit_excludes_initiatives(self):
        result = await mortgage_calculator(
            _request(),
            MortgageRequest(
                unit_price_egp=10_000_000,
                down_payment_egp=2_000_000,
                years=15,
            ),
            current_user=None,
        )
        assert result["tiers"][0]["eligible"] is False
        assert result["tiers"][1]["eligible"] is False
        assert result["tiers"][2]["eligible"] is True


class TestInstallmentVsCash:
    @pytest.mark.asyncio
    async def test_npv_below_nominal_price(self):
        result = await installment_vs_cash(
            _request(),
            InstallmentVsCashRequest(
                total_price_egp=5_000_000,
                down_payment_egp=500_000,
                installment_years=8,
                installments_per_year=4,
            ),
        )
        assert result["cash_equivalent_npv_egp"] < result["nominal_price_egp"]
        assert result["time_value_discount_pct"] > 0
        assert result["installments_count"] == 32
        assert result["per_installment_egp"] == pytest.approx(140_625.0)
        assert result["verdict"] is None  # no cash price supplied

    @pytest.mark.asyncio
    async def test_verdict_cash_when_cash_price_below_npv(self):
        base = await installment_vs_cash(
            _request(),
            InstallmentVsCashRequest(
                total_price_egp=5_000_000,
                down_payment_egp=500_000,
                installment_years=8,
            ),
        )
        cheap_cash = base["cash_equivalent_npv_egp"] * 0.9
        result = await installment_vs_cash(
            _request(),
            InstallmentVsCashRequest(
                total_price_egp=5_000_000,
                down_payment_egp=500_000,
                installment_years=8,
                cash_price_egp=cheap_cash,
            ),
        )
        assert result["verdict"] == "cash"
        assert result["savings_if_cash_egp"] > 0

    @pytest.mark.asyncio
    async def test_verdict_installments_when_cash_price_above_npv(self):
        result = await installment_vs_cash(
            _request(),
            InstallmentVsCashRequest(
                total_price_egp=5_000_000,
                down_payment_egp=500_000,
                installment_years=8,
                cash_price_egp=4_999_999,
            ),
        )
        assert result["verdict"] == "installments"
