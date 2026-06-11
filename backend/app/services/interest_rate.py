"""
Central Bank of Egypt (CBE) Interest Rate Service
--------------------------------------------------
Corridor rates plus the CBE subsidized mortgage-initiative tiers
(مبادرة التمويل العقاري). Initiative rates and income-eligibility caps are
configurable via environment variables because they change with CBE decrees.

In production this would track 'cbe.org.eg'; for now rates are conservative
"safe harbor" values updated with releases.
"""

import os
from datetime import datetime


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


class InterestRateService:
    LAST_UPDATED = datetime(2026, 1, 7)
    CORRIDOR_DEPOSIT = 22.25
    CORRIDOR_LENDING = 23.25

    # Mortgage typically moves with Lending Rate + Margin
    BASE_MORTGAGE_RATE = 25.0

    # ── CBE subsidized mortgage initiative (مبادرة التمويل العقاري) ──
    # 3% for low-income, 8% for middle-income buyers, per CBE/MFF programs.
    INITIATIVE_LOW_INCOME_RATE = _env_float("CBE_INITIATIVE_LOW_INCOME_RATE", 3.0)
    INITIATIVE_MIDDLE_INCOME_RATE = _env_float("CBE_INITIATIVE_MIDDLE_INCOME_RATE", 8.0)

    # Monthly-income eligibility ceilings (EGP) — updated by decree
    LOW_INCOME_MONTHLY_CAP = _env_float("CBE_LOW_INCOME_MONTHLY_CAP", 12_000)
    MIDDLE_INCOME_MONTHLY_CAP = _env_float("CBE_MIDDLE_INCOME_MONTHLY_CAP", 40_000)

    # Maximum unit price eligible for the subsidized initiative (EGP)
    INITIATIVE_MAX_UNIT_PRICE = _env_float("CBE_INITIATIVE_MAX_UNIT_PRICE", 2_500_000)

    @staticmethod
    def get_current_mortgage_rate() -> float:
        """Current estimated market mortgage rate (%)."""
        # Feature Flag: Connect to Live Scraper here
        return InterestRateService.BASE_MORTGAGE_RATE

    @classmethod
    def get_rate_tiers(cls) -> list[dict]:
        """All mortgage rate tiers with eligibility rules, for the calculator."""
        return [
            {
                "id": "initiative_low",
                "annual_rate_pct": cls.INITIATIVE_LOW_INCOME_RATE,
                "monthly_income_cap_egp": cls.LOW_INCOME_MONTHLY_CAP,
                "max_unit_price_egp": cls.INITIATIVE_MAX_UNIT_PRICE,
                "name": {
                    "en": "CBE initiative — low income",
                    "ar": "مبادرة البنك المركزي — محدودي الدخل",
                },
            },
            {
                "id": "initiative_middle",
                "annual_rate_pct": cls.INITIATIVE_MIDDLE_INCOME_RATE,
                "monthly_income_cap_egp": cls.MIDDLE_INCOME_MONTHLY_CAP,
                "max_unit_price_egp": cls.INITIATIVE_MAX_UNIT_PRICE,
                "name": {
                    "en": "CBE initiative — middle income",
                    "ar": "مبادرة البنك المركزي — متوسطي الدخل",
                },
            },
            {
                "id": "market",
                "annual_rate_pct": cls.get_current_mortgage_rate(),
                "monthly_income_cap_egp": None,
                "max_unit_price_egp": None,
                "name": {
                    "en": "Standard bank mortgage",
                    "ar": "تمويل عقاري بنكي قياسي",
                },
            },
        ]

    @classmethod
    def eligible_tier(cls, monthly_income_egp: float, unit_price_egp: float) -> str:
        """Best (cheapest) tier id the buyer qualifies for."""
        if unit_price_egp <= cls.INITIATIVE_MAX_UNIT_PRICE:
            if monthly_income_egp <= cls.LOW_INCOME_MONTHLY_CAP:
                return "initiative_low"
            if monthly_income_egp <= cls.MIDDLE_INCOME_MONTHLY_CAP:
                return "initiative_middle"
        return "market"


interest_rate_service = InterestRateService()
