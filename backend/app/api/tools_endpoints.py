"""
Tools Endpoints — Egyptian buyer calculators
---------------------------------------------
Free, fast, deterministic tools (no LLM tokens):

  POST /api/tools/mortgage             → تمويل عقاري calculator with CBE
                                         initiative tiers (3% / 8% / market)
  POST /api/tools/installment-vs-cash  → NPV comparison of a developer
                                         payment plan vs cash (existing
                                         valuation engine math)

Free tier gets the full calculations; Pro adds an affordability block on
the mortgage tool (kept simple: gated on subscription_tier).
"""

from __future__ import annotations

import logging
import math
import os
from typing import Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field, model_validator
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.auth import get_current_user_optional
from app.models import User
from app.services.interest_rate import InterestRateService
from app.valuation_engine import DEFAULT_CBE_RATE, PaymentTimeline, ValuationEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tools", tags=["tools"])
limiter = Limiter(key_func=get_remote_address)

_CBE_RATE = float(os.getenv("CBE_BASE_RATE", str(DEFAULT_CBE_RATE)))
_valuation_engine = ValuationEngine(cbe_rate=_CBE_RATE)

from app.api.freemium_router import _tier_is_premium  # expiry-aware premium check


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class MortgageRequest(BaseModel):
    unit_price_egp: float = Field(..., gt=0, le=1_000_000_000)
    down_payment_egp: float = Field(..., ge=0)
    years: int = Field(..., ge=1, le=30)
    monthly_income_egp: Optional[float] = Field(None, gt=0)


class InstallmentVsCashRequest(BaseModel):
    total_price_egp: float = Field(..., gt=0, le=1_000_000_000)
    down_payment_egp: float = Field(..., gt=0)
    installment_years: int = Field(..., ge=1, le=15)
    installments_per_year: int = Field(4, ge=1, le=12)
    cash_price_egp: Optional[float] = Field(
        None, gt=0, description="Seller's cash price, if quoted separately"
    )

    @model_validator(mode="after")
    def down_payment_below_total(self) -> "InstallmentVsCashRequest":
        if self.down_payment_egp >= self.total_price_egp:
            raise ValueError("down_payment_egp must be less than total_price_egp")
        return self


# ---------------------------------------------------------------------------
# Math helpers
# ---------------------------------------------------------------------------

def _monthly_payment(principal: float, annual_rate_pct: float, years: int) -> float:
    """Standard amortized mortgage payment."""
    n = years * 12
    if principal <= 0:
        return 0.0
    r = (annual_rate_pct / 100.0) / 12.0
    if r == 0:
        return principal / n
    factor = (1 + r) ** n
    return principal * r * factor / (factor - 1)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/mortgage")
@limiter.limit("30/minute")
async def mortgage_calculator(
    request: Request,
    req: MortgageRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Monthly payment per CBE rate tier + initiative eligibility.
    Pro users additionally get an affordability verdict against the
    common 40%-of-income installment ceiling used by Egyptian banks.
    """
    principal = max(req.unit_price_egp - req.down_payment_egp, 0.0)
    income = req.monthly_income_egp

    tiers_out = []
    for tier in InterestRateService.get_rate_tiers():
        payment = _monthly_payment(principal, tier["annual_rate_pct"], req.years)
        eligible = True
        if tier["max_unit_price_egp"] is not None and req.unit_price_egp > tier["max_unit_price_egp"]:
            eligible = False
        if (
            tier["monthly_income_cap_egp"] is not None
            and income is not None
            and income > tier["monthly_income_cap_egp"]
        ):
            eligible = False

        total_paid = payment * req.years * 12 + req.down_payment_egp
        tiers_out.append({
            "id": tier["id"],
            "name": tier["name"],
            "annual_rate_pct": tier["annual_rate_pct"],
            "eligible": eligible,
            "monthly_payment_egp": round(payment, 2),
            "total_paid_egp": round(total_paid, 2),
            "total_interest_egp": round(total_paid - req.unit_price_egp, 2),
        })

    best_tier_id = (
        InterestRateService.eligible_tier(income, req.unit_price_egp)
        if income is not None else None
    )

    response: dict = {
        "principal_egp": round(principal, 2),
        "years": req.years,
        "tiers": tiers_out,
        "best_eligible_tier": best_tier_id,
        "rates_last_updated": InterestRateService.LAST_UPDATED.date().isoformat(),
    }

    # Pro extension: affordability verdict (banks cap installments ~40% of income)
    is_premium = current_user is not None and _tier_is_premium(current_user)
    if is_premium and income is not None and best_tier_id:
        best = next(t for t in tiers_out if t["id"] == best_tier_id)
        ceiling = income * 0.40
        payment = best["monthly_payment_egp"]
        max_affordable_principal = _max_principal(ceiling, best["annual_rate_pct"], req.years)
        response["affordability"] = {
            "income_ceiling_egp": round(ceiling, 2),
            "payment_egp": payment,
            "affordable": payment <= ceiling,
            "utilization_pct": round(payment / ceiling * 100, 1) if ceiling else None,
            "max_affordable_unit_price_egp": round(
                max_affordable_principal + req.down_payment_egp, 2
            ),
        }
    elif income is not None:
        response["affordability_gated"] = True  # frontend shows the Pro teaser

    return response


def _max_principal(monthly_payment: float, annual_rate_pct: float, years: int) -> float:
    """Inverse of _monthly_payment: largest loan the payment can service."""
    n = years * 12
    r = (annual_rate_pct / 100.0) / 12.0
    if r == 0:
        return monthly_payment * n
    factor = (1 + r) ** n
    return monthly_payment * (factor - 1) / (r * factor)


@router.post("/installment-vs-cash")
@limiter.limit("30/minute")
async def installment_vs_cash(
    request: Request,
    req: InstallmentVsCashRequest,
):
    """
    'هل التقسيط أحسن من الكاش؟' — flattens the developer payment plan to its
    cash-equivalent NPV at the CBE corridor rate and compares.
    """
    n_payments = req.installments_per_year * req.installment_years
    per_installment = (req.total_price_egp - req.down_payment_egp) / n_payments

    plan = PaymentTimeline(
        down_payment=req.down_payment_egp,
        installments_per_year=req.installments_per_year,
        total_years=req.installment_years,
        periodic_installment_amount=per_installment,
    )
    npv = _valuation_engine.calculate_effective_cash_npv(req.total_price_egp, plan)

    cash_price = req.cash_price_egp
    verdict = None
    savings_egp = None
    if cash_price is not None:
        savings_egp = round(npv - cash_price, 2)
        verdict = "cash" if cash_price < npv else "installments"

    return {
        "nominal_price_egp": req.total_price_egp,
        "cash_equivalent_npv_egp": round(npv, 2),
        "time_value_discount_egp": round(req.total_price_egp - npv, 2),
        "time_value_discount_pct": round(
            (req.total_price_egp - npv) / req.total_price_egp * 100, 2
        ),
        "per_installment_egp": round(per_installment, 2),
        "installments_count": n_payments,
        "cbe_rate_pct": round(_CBE_RATE * 100, 2),
        "cash_price_egp": cash_price,
        "savings_if_cash_egp": savings_egp,
        "verdict": verdict,
    }
