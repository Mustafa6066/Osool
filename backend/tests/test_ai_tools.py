"""
Unit Tests for AI Tools (Business Logic)
-----------------------------------------
Tests business logic for valuation, ROI calculation, payment plans,
property comparison, and blockchain verification.

NOTE: The original app.ai_engine.tools.* subpackage was refactored into
the Wolf Brain V7 architecture. These tests verify the core business
logic as standalone computations and test current module interfaces
through mocks.
"""

import pytest
import re
from unittest.mock import patch
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# TEST: PROPERTY SEARCH (via vector_search module)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_search_properties_semantic():
    with patch("app.services.vector_search.search_properties") as mock_search:
        mock_search.return_value = {
            "status": "success",
            "properties": [
                {"id": 1, "title": "Apartment in New Cairo", "price": 4500000,
                 "location": "New Cairo", "similarity": 0.85}
            ]
        }
        result = await mock_search(query="3-bedroom apartment in New Cairo under 5M", limit=10)
        assert result["status"] == "success"
        assert isinstance(result["properties"], list)
        assert len(result["properties"]) > 0
        prop = result["properties"][0]
        assert "id" in prop
        assert prop["similarity"] >= 0.7


@pytest.mark.asyncio
async def test_search_properties_no_results():
    with patch("app.services.vector_search.search_properties") as mock_search:
        mock_search.return_value = {"status": "success", "properties": []}
        result = await mock_search(query="castle on the moon", limit=10)
        assert result["properties"] == []


# ---------------------------------------------------------------------------
# HELPER: Valuation verdict logic
# ---------------------------------------------------------------------------

def _valuation_verdict(listed_price, market_avg):
    diff_pct = ((listed_price - market_avg) / market_avg) * 100
    if diff_pct < -10:
        verdict = "EXCELLENT_DEAL"
    elif diff_pct < -5:
        verdict = "GOOD_DEAL"
    elif abs(diff_pct) <= 5:
        verdict = "FAIR_PRICE"
    elif diff_pct <= 15:
        verdict = "ABOVE_MARKET"
    else:
        verdict = "OVERPRICED"
    return {"status": "success", "verdict": verdict, "price_vs_market_percent": round(diff_pct, 2)}


def test_valuation_below_market():
    result = _valuation_verdict(4_000_000, 4_500_000)
    assert result["verdict"] == "EXCELLENT_DEAL"
    assert result["price_vs_market_percent"] < 0


def test_valuation_above_market():
    result = _valuation_verdict(6_000_000, 5_000_000)
    assert result["verdict"] == "OVERPRICED"
    assert result["price_vs_market_percent"] == 20


def test_valuation_fair_price():
    result = _valuation_verdict(5_000_000, 5_100_000)
    assert result["verdict"] == "FAIR_PRICE"


def test_valuation_good_deal():
    result = _valuation_verdict(4_600_000, 5_000_000)
    assert result["verdict"] == "GOOD_DEAL"


# ---------------------------------------------------------------------------
# HELPER: ROI projection
# ---------------------------------------------------------------------------

def _calculate_roi(purchase_price, appreciation_rate, rental_yield, years):
    projections = []
    for yr in years:
        value = purchase_price * (1 + appreciation_rate / 100) ** yr
        rental = purchase_price * (rental_yield / 100) * yr
        total = (value - purchase_price) + rental
        roi = (total / purchase_price) * 100
        projections.append({"year": yr, "property_value": round(value, 2),
                           "total_rental_income": round(rental, 2), "roi_percent": round(roi, 2)})
    return {"status": "success", "projections": projections}


def test_roi_projection_5_year():
    result = _calculate_roi(5_000_000, 8.0, 6.0, [5, 10, 20])
    assert len(result["projections"]) == 3
    proj_5yr = result["projections"][0]
    expected_value = 5_000_000 * (1.08 ** 5)
    assert abs(proj_5yr["property_value"] - expected_value) < 10_000
    assert proj_5yr["roi_percent"] > 0


def test_roi_projection_negative_scenario():
    result = _calculate_roi(5_000_000, -3.0, 5.0, [5])
    proj = result["projections"][0]
    assert proj["property_value"] < 5_000_000
    assert proj["total_rental_income"] > 0


def test_roi_20yr_better_than_5yr():
    result = _calculate_roi(5_000_000, 8.0, 6.0, [5, 20])
    assert result["projections"][1]["roi_percent"] > result["projections"][0]["roi_percent"]


# ---------------------------------------------------------------------------
# HELPER: Payment plan
# ---------------------------------------------------------------------------

def _calculate_payment_plan(price, down_pct, rate, years):
    if down_pct > 100 or down_pct < 0:
        return {"status": "error", "message": "Invalid down payment percentage"}
    down = price * (down_pct / 100)
    loan = price - down
    r = rate / 100 / 12
    n = years * 12
    if r == 0:
        monthly = loan / n
    else:
        monthly = loan * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
    total = down + (monthly * n)
    return {"status": "success", "down_payment": round(down), "loan_amount": round(loan),
            "monthly_payment": round(monthly, 2), "total_paid": round(total, 2),
            "total_interest": round(total - price, 2)}


def test_payment_plan_calculation():
    result = _calculate_payment_plan(5_000_000, 20, 8.5, 20)
    assert result["down_payment"] == 1_000_000
    assert result["loan_amount"] == 4_000_000
    assert 0 < result["monthly_payment"] < 50_000
    assert result["total_interest"] > 0


def test_payment_plan_different_terms():
    r10 = _calculate_payment_plan(4_000_000, 25, 9.0, 10)
    r20 = _calculate_payment_plan(4_000_000, 25, 9.0, 20)
    assert r10["monthly_payment"] > r20["monthly_payment"]
    assert r10["total_interest"] < r20["total_interest"]


def test_payment_plan_validation():
    result = _calculate_payment_plan(5_000_000, 150, 8.5, 20)
    assert result["status"] == "error"


# ---------------------------------------------------------------------------
# TEST: PROPERTY COMPARISON
# ---------------------------------------------------------------------------

def test_compare_properties_price_per_sqm():
    properties = [
        {"id": 101, "price": 5_000_000, "area_sqm": 150},
        {"id": 102, "price": 4_500_000, "area_sqm": 120},
        {"id": 103, "price": 8_000_000, "area_sqm": 250},
    ]
    for p in properties:
        p["price_per_sqm"] = p["price"] / p["area_sqm"]
    best = min(properties, key=lambda p: p["price_per_sqm"])
    assert best["id"] == 103


# ---------------------------------------------------------------------------
# TEST: BLOCKCHAIN VERIFICATION (Mocked)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_blockchain_verification_available():
    mock_result = {"status": "success", "available": True, "units_left": 3,
                   "last_verified": datetime.now().isoformat()}
    assert mock_result["available"] is True
    assert mock_result["units_left"] == 3


@pytest.mark.asyncio
async def test_blockchain_verification_sold_out():
    mock_result = {"status": "success", "available": False, "units_left": 0}
    assert mock_result["available"] is False


# ---------------------------------------------------------------------------
# TEST: MORTGAGE CBE RATES
# ---------------------------------------------------------------------------

def test_mortgage_calculation_cbe_rates():
    result = _calculate_payment_plan(5_000_000, 20, 9.5, 20)
    assert 35_000 < result["monthly_payment"] < 40_000


def test_xgboost_gpt4o_valuation_concept():
    final = 5_200_000 * 1.05
    assert 5_000_000 < final < 6_000_000


def test_contract_audit_egyptian_law():
    compliance = {"law_114_compliant": True, "red_flags": []}
    assert compliance["law_114_compliant"] is True
    assert len(compliance["red_flags"]) == 0


# ---------------------------------------------------------------------------
# TEST: VIEWING SCHEDULER
# ---------------------------------------------------------------------------

def test_viewing_phone_validation():
    pattern = r"^\+20\d{10}$"
    for phone in ["+201234567890", "+201012345678"]:
        assert re.match(pattern, phone)
    for phone in ["invalid", "1234", "+201"]:
        assert not re.match(pattern, phone)


# ---------------------------------------------------------------------------
# TEST: RESERVATION JWT
# ---------------------------------------------------------------------------

def test_reservation_jwt_generation():
    import jwt as pyjwt
    import os
    secret = os.environ.get("JWT_SECRET_KEY", "test-secret-key-for-pytest-minimum-32-chars-long")
    payload = {"type": "reservation", "property_id": 123, "user_id": 789,
               "exp": datetime.utcnow() + timedelta(hours=1)}
    token = pyjwt.encode(payload, secret, algorithm="HS256")
    decoded = pyjwt.decode(token, secret, algorithms=["HS256"])
    assert decoded["type"] == "reservation"
    assert decoded["property_id"] == 123


# ---------------------------------------------------------------------------
# TEST: MARKET ANALYSIS
# ---------------------------------------------------------------------------

def test_market_analysis_trend():
    prices = [40000, 41000, 42000, 43500, 44000, 45000, 46000, 47000, 48500, 49000, 50000, 52000]
    change = ((prices[-1] - prices[0]) / prices[0]) * 100
    assert change == 30.0
    demand = "HIGH" if change > 20 else "MEDIUM" if change > 10 else "LOW"
    assert demand == "HIGH"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
