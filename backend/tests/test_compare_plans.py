"""
Tests for installment-first plan comparison (Fix 3).

The /api/valuation/compare-plans endpoint is a thin wrapper that:
  1. builds a PaymentTimeline per item,
  2. calls ValuationEngine.calculate_effective_cash_npv (CBE-discounted),
  3. calls PaymentPlanAnalyzer._compare_to_rent,
  4. sorts rows by npv_today ascending.

Steps 1-3 are the real logic and are exercised directly here (fast, no app
import). Step 4 is a one-line list.sort and is trusted.
"""
from __future__ import annotations

import os

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-minimum-32-chars-long")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-key")

from app.valuation_engine import PaymentTimeline, ValuationEngine  # noqa: E402
from app.ai_engine.analytical_engine import PaymentPlanAnalyzer  # noqa: E402


def _plan(price: float, down: float, years: int) -> PaymentTimeline:
    monthly = (price - down) / (years * 12)
    return PaymentTimeline(
        down_payment=down,
        installments_per_year=12,
        total_years=years,
        periodic_installment_amount=monthly,
    )


def test_longer_cheaper_financed_plan_has_lower_npv():
    """Same sticker: the plan that pushes more money into the future (low down,
    long tenure) is cheaper in today's money than the front-loaded plan."""
    eng = ValuationEngine(cbe_rate=0.22)
    price = 5_000_000.0

    long_low_down = _plan(price, down=250_000, years=10)   # 5% down, 10 yrs
    short_high_down = _plan(price, down=2_500_000, years=3)  # 50% down, 3 yrs

    npv_long = eng.calculate_effective_cash_npv(price, long_low_down)
    npv_short = eng.calculate_effective_cash_npv(price, short_high_down)

    assert npv_long < npv_short < price


def test_cash_npv_equals_sticker():
    eng = ValuationEngine(cbe_rate=0.22)
    assert eng.calculate_effective_cash_npv(3_000_000.0, None) == 3_000_000.0


def test_zero_cbe_rate_npv_is_plan_total():
    """Degenerate r=0: NPV is just the undiscounted sum of all payments."""
    eng = ValuationEngine(cbe_rate=0.0)
    price = 1_200_000.0
    plan = _plan(price, down=200_000, years=5)
    npv = eng.calculate_effective_cash_npv(price, plan)
    # down + 60 monthly payments == price (within float tolerance)
    assert abs(npv - price) < 1.0


def test_rent_ratio_matches_division():
    an = PaymentPlanAnalyzer()
    r = an._compare_to_rent(30_000, "New Cairo")
    assert r["avg_rent"] > 0
    assert r["ratio"] == round(30_000 / r["avg_rent"], 2)
    assert "verdict_en" in r and "verdict_ar" in r


def test_down_payment_normalization():
    """down_payment may arrive as a fraction, a percentage, or absolute EGP —
    all three must collapse to the same EGP amount."""
    from app.valuation_engine import normalize_down_payment_to_egp as norm
    price = 4_000_000.0
    assert norm(0.10, price) == 400_000.0      # fraction
    assert norm(10, price) == 400_000.0        # percentage
    assert norm(400_000, price) == 400_000.0   # absolute EGP
    assert norm(0, price) == 0.0
    assert norm(None, price) == 0.0
    assert norm("bad", price) == 0.0


def test_rent_verdict_flips_below_and_above_rent():
    an = PaymentPlanAnalyzer()
    avg = an._compare_to_rent(1, "New Cairo")["avg_rent"]
    cheap = an._compare_to_rent(int(avg * 0.8), "New Cairo")   # installment < rent
    pricey = an._compare_to_rent(int(avg * 2.0), "New Cairo")  # installment >> rent
    assert cheap["ratio"] <= 1.0
    assert pricey["ratio"] > 1.5
    assert cheap["verdict_en"] != pricey["verdict_en"]
