"""
Analytical Engine - The Wolf's Ledger
-------------------------------------
Consolidated analytics functions for deal scoring, ROI calculation,
inflation hedging, and market analysis.

CRITICAL: Never let the LLM do math. All calculations are code-based.

Functions:
- calculate_true_roi(property): Rental yield + appreciation
- calculate_inflation_hedge(investment): Cash vs Property comparison
- score_property(property): Osool Score calculation
- detect_bargains(properties): Find below-market deals
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# Market data constants (Egyptian market 2024-2025)
# Updated for 2025 moderated inflation and strong real growth
# Market data constants (Egyptian market 2025-2026 Strategy)
# SOURCE: Regional Market Research (Feb 2026)
# "Liquidity Shift" Era: Real Estate > Bank Certificates
MARKET_DATA = {
    "inflation_rate": 0.136,            # 13.6% (2026 Mid-Year Forecast vs 30%+ Peak)
    "inflation_rate_2024": 0.337,       # Historical context
    "bank_cd_rate": 0.22,               # 22% (Decreased from 27.25% Peak)
    "real_property_growth": 0.145,      # 14.5% Real Growth (Demand-Driven)
    "nominal_property_appreciation": 0.304, # 30.4% YoY Aggregated
    "property_appreciation": 0.20,      # Conservative 20% for future projections
    "rental_yield_avg": 0.075,          # 7.5% Blended Avg (up from 6.5%)
    "rent_increase_rate": 0.12,         # 12% annual rent increase (High demand)
    "gold_appreciation": 0.15,          # 15% (Stabilized vs Bricks)
}

# Construction cost constants for Replacement Cost logic
CONSTRUCTION_COSTS = {
    "base_cost_sqm": 15000,             # Base construction cost per sqm (pre-inflation)
    "cost_index_2025": 1.30,            # 30% increase YoY due to iron, cement, labor
    "land_value_share": 0.40,           # Land = ~40% of unit price
    "developer_margin_avg": 0.15,       # Developer margin ~15%
}

# Area price data (EGP per sqm, Dec 2025 Research)
# "Cost-Push" Pricing Floor in effect
AREA_PRICES = {
    "New Cairo": 61550,      # Research: +157.3% Growth
    "Sheikh Zayed": 64050,   # Research: +185.3% Growth
    "New Capital": 45000,    # R7/R8 Resale avg
    "6th October": 47000,    # Research: +153.7%
    "North Coast": 76150,    # Research: +209% YoY
    "Maadi": 26950,         # Research: Stable/Mature
    "Zamalek": 64400,       # Comparison Benchmark
    "Ain Sokhna": 91200,    # Usage-based premium
    "Madinaty": 55000,
    "Rehab": 50000,
}

# Area growth rates (Historical YoY 2025)
# Used for "Why Buy Here?" argumentation
AREA_GROWTH = {
    "New Cairo": 1.57,      # +157%
    "Sheikh Zayed": 1.85,   # +185%
    "New Capital": 0.25,    # Stabilized
    "6th October": 1.53,    # +153%
    "North Coast": 2.09,    # +209%
    "Maadi": 0.39,          # +39%
    "Ain Sokhna": 2.83,     # +283%
    "Madinaty": 0.20,
}

# ═══════════════════════════════════════════════════════════════
# COMPREHENSIVE AREA BENCHMARKS (Wolf Intelligence Layer)
# ═══════════════════════════════════════════════════════════════
AREA_BENCHMARKS = {
    "new cairo": {
        "ar_name": "التجمع الخامس",
        "avg_price_sqm": 61550, 
        "rental_yield": 0.0775, # 7.75% Research
        "growth_rate": 1.57,    # 157% YoY
        "property_minimums": {
            "apartment": 5_000_000, # Market floor raised
            "villa": 15_000_000,
            "townhouse": 9_000_000,
            "duplex": 7_000_000,
        },
        "tier1_developers": ["اعمار", "سوديك", "ماونتن ڤيو", "بالم هيلز", "هايد بارك"],
        "tier2_developers": ["لافيستا", "تطوير مصر", "المقاصد"],
        "tier3_developers": ["كابيتال جروب", "السعودية المصرية"],
    },
    "sheikh zayed": {
        "ar_name": "الشيخ زايد",
        "avg_price_sqm": 64050,
        "rental_yield": 0.0687, # 6.87% Research
        "growth_rate": 1.85,    # 185% YoY
        "property_minimums": {
            "apartment": 6_000_000,
            "villa": 18_000_000,
            "townhouse": 12_000_000,
            "duplex": 8_000_000,
        },
        "tier1_developers": ["سوديك", "أورا", "بالم هيلز", "إعمار"],
        "tier2_developers": ["زيد ويست", "O ويست"],
        "tier3_developers": [],
    },
    "new capital": {
        "ar_name": "العاصمة الإدارية",
        "avg_price_sqm": 45000,
        "rental_yield": 0.05,
        "growth_rate": 0.25,
        "property_minimums": {
            "apartment": 2_500_000, # R7 entry
            "villa": 8_000_000,
            "townhouse": 5_000_000,
            "duplex": 4_000_000,
        },
        "tier1_developers": ["المقاولون العرب", "المراسم"],
        "tier2_developers": ["مصر إيطاليا", "بيتر هوم"],
        "tier3_developers": ["كابيتال جروب"],
    },
    "6th october": {
        "ar_name": "السادس من أكتوبر",
        "avg_price_sqm": 47000, # Updated
        "rental_yield": 0.0607, # 6.07% Research
        "growth_rate": 1.53,    # 153% YoY
        "property_minimums": {
            "apartment": 2_000_000,
            "villa": 6_000_000,
            "townhouse": 4_000_000,
            "duplex": 3_500_000,
        },
        "tier1_developers": ["بالم هيلز"],
        "tier2_developers": ["دريم لاند"],
        "tier3_developers": [],
    },
    "north coast": {
        "ar_name": "الساحل الشمالي",
        "avg_price_sqm": 76150, # Updated
        "rental_yield": 0.10,   # High seasonal yield
        "growth_rate": 2.09,    # 209% YoY
        "property_minimums": {
            "chalet": 7_000_000,
            "villa": 25_000_000,
            "townhouse": 15_000_000,
        },
        "tier1_developers": ["اعمار", "سوديك", "ماونتن ڤيو", "سيتي إيدج"],
        "tier2_developers": ["لافيستا", "تطوير مصر"],
        "tier3_developers": [],
    },
    "maadi": {
        "ar_name": "المعادي",
        "avg_price_sqm": 70000,
        "rental_yield": 0.07,
        "growth_rate": 0.08,
        "property_minimums": {
            "apartment": 4_000_000,
            "villa": 20_000_000,
        },
        "tier1_developers": [],
        "tier2_developers": [],
        "tier3_developers": [],
    },
}

# ═══════════════════════════════════════════════════════════════
# MARKET SEGMENTS - Class A vs Class B Developer Segmentation
# For the "Market Education" consultation flow
# ═══════════════════════════════════════════════════════════════
MARKET_SEGMENTS = {
    "new_cairo": {
        "name_ar": "التجمع",
        "name_en": "New Cairo",
        "class_a": {
            "name_ar": "مطورين الفئة الأولى (Class A)",
            "developers": ["إعمار (Emaar)", "سوديك (Sodic)", "مراكز (Marakez)", "المراسم (Al Marasem)", "ماونتن فيو (Mountain View)", "بالم هيلز (Palm Hills)"],
            "developers_ar": ["إعمار", "سوديك", "مراكز", "المراسم", "ماونتن فيو", "بالم هيلز"],
            "price_range_ar": "٦,٠٠٠,٠٠٠ - ٢٥,٠٠٠,٠٠٠",
            "price_range_en": "6,000,000 - 25,000,000",
            "avg_price": 12_000_000,
            "avg_price_ar": "١٢ مليون",
            "min_price": 6_000_000,  # Updated: was 13.5M, now 6M (Emaar 2BR starts at ~8M)
            "max_price": 25_000_000,
        },
        "class_b": {
            "name_ar": "مطورين الفئة الثانية (Class B)",
            "developers": ["هايد بارك (Hyde Park)", "صبور (Sabbour)", "تطوير مصر (Tatweer Misr)", "LMD"],
            "developers_ar": ["هايد بارك", "صبور", "تطوير مصر", "LMD"],
            "price_range_ar": "٤,٠٠٠,٠٠٠ - ١٠,٠٠٠,٠٠٠",
            "price_range_en": "4,000,000 - 10,000,000",
            "avg_price": 6_500_000,
            "avg_price_ar": "٦.٥ مليون",
            "min_price": 4_000_000,  # Updated: was 12M, now 4M (LMD One Ninety starts at 4.5M)
            "max_price": 10_000_000,
        },
        "market_floor": 4_000_000,  # Updated: actual minimum in market (was 6M)
        "market_floor_ar": "٤ مليون",
        "market_ceiling": 15_000_000,
        "market_ceiling_ar": "١٥ مليون",
    },
    "sheikh_zayed": {
        "name_ar": "الشيخ زايد",
        "name_en": "Sheikh Zayed",
        "class_a": {
            "name_ar": "مطورين الفئة الأولى (Class A)",
            "developers": ["أورا (Ora)", "سوديك (Sodic)", "إعمار (Belle Vie)", "ماونتن فيو (Mountain View)", "بالم هيلز (Palm Hills)", "مراكز (Marakez)"],
            "developers_ar": ["أورا", "سوديك", "إعمار", "ماونتن فيو", "بالم هيلز", "مراكز"],
            "price_range_ar": "١٥,٠٠٠,٠٠٠ - ٣٠,٠٠٠,٠٠٠",
            "price_range_en": "15,000,000 - 30,000,000",
            "avg_price": 20_000_000,
            "avg_price_ar": "٢٠ مليون",
            "min_price": 15_000_000,
            "max_price": 30_000_000,
        },
        "class_b": {
            "name_ar": "مطورين الفئة الثانية (Class B)",
            "developers": ["درة (Dorra)", "كونتيننتال (Continental)", "بدر الدين (Badr Eldin)", "ايوان (Iwan)"],
            "developers_ar": ["درة", "كونتيننتال", "بدر الدين", "ايوان"],
            "price_range_ar": "٩,٠٠٠,٠٠٠ - ١٤,٠٠٠,٠٠٠",
            "price_range_en": "9,000,000 - 14,000,000",
            "avg_price": 11_500_000,
            "avg_price_ar": "١١.٥ مليون",
            "min_price": 9_000_000,
            "max_price": 14_000_000,
        },
        "market_floor": 8_000_000,
        "market_floor_ar": "٨ مليون",
        "market_ceiling": 22_000_000,
        "market_ceiling_ar": "٢٢ مليون",
    },
    "new_capital": {
        "name_ar": "العاصمة الإدارية",
        "name_en": "New Capital",
        "class_a": {
            "name_ar": "مطورين الفئة الأولى (Class A)",
            "developers": ["المقاولون العرب", "المراسم", "سيتي إيدج"],
            "developers_ar": ["المقاولون العرب", "المراسم", "سيتي إيدج"],
            "price_range_ar": "٤,٠٠٠,٠٠٠ - ٧,٠٠٠,٠٠٠",
            "price_range_en": "4,000,000 - 7,000,000",
            "avg_price": 5_500_000,
            "avg_price_ar": "٥.٥ مليون",
            "min_price": 4_000_000,
            "max_price": 7_000_000,
        },
        "class_b": {
            "name_ar": "مطورين الفئة الثانية (Class B)",
            "developers": ["مصر إيطاليا", "بيتر هوم", "كابيتال جروب"],
            "developers_ar": ["مصر إيطاليا", "بيتر هوم", "كابيتال جروب"],
            "price_range_ar": "١,٨٠٠,٠٠٠ - ٣,٥٠٠,٠٠٠",
            "price_range_en": "1,800,000 - 3,500,000",
            "avg_price": 2_500_000,
            "avg_price_ar": "٢.٥ مليون",
            "min_price": 1_800_000,
            "max_price": 3_500_000,
        },
        "market_floor": 1_800_000,
        "market_floor_ar": "١.٨ مليون",
        "market_ceiling": 7_000_000,
        "market_ceiling_ar": "٧ مليون",
    },
}

# Property type mappings (Arabic to English)
PROPERTY_TYPE_MAP = {
    "شقة": "apartment",
    "شقق": "apartment",
    "فيلا": "villa",
    "فلل": "villa",
    "تاون هاوس": "townhouse",
    "تاونهاوس": "townhouse",
    "دوبلكس": "duplex",
    "شاليه": "chalet",
}

# Developer tiers
TIER1_DEVELOPERS = [
    "al marasem", "marakez", "sodic", "emaar", "emmar", "mountain view", 
    "lake view", "lakeview", "palm hills", "ora", "la vista", "lavista",
    "المراسم", "مراكز", "سوديك", "إعمار", "ماونتن فيو", "ليك فيو", "بالم هيلز", "أورا", "لافيستا"
]
TIER2_DEVELOPERS = [
    "hyde park", "hydepark", "tatweer misr", "misr italia", 
    "better home", "gates", "iq", "حسن علام", "درة", "dorra"
]

# ═══════════════════════════════════════════════════════════════
# DEVELOPER KNOWLEDGE GRAPH (The Wolf's Reputation Ledger)
# For relationship-aware insights: "Why is Emaar expensive?"
# ═══════════════════════════════════════════════════════════════
DEVELOPER_GRAPH = {
    "emaar": {
        "tier": 1,
        "name_ar": "إعمار",
        "name_en": "Emaar",
        "competitors": ["sodic", "palm hills", "mountain view"],
        "strength": "Highest Resale Value",
        "strength_ar": "أعلى قيمة إعادة بيع في السوق",
        "delivery_reliability": 95,  # 95% on-time delivery
        "resale_premium": 20,  # 20% above competitors
        "avg_price_sqm": 85000,
        "flagship_projects": ["Mivida", "Uptown Cairo", "Belle Vie"],
    },
    "sodic": {
        "tier": 1,
        "name_ar": "سوديك",
        "name_en": "SODIC",
        "competitors": ["emaar", "ora", "palm hills"],
        "strength": "Community Management & Lifestyle",
        "strength_ar": "إدارة المجتمع والـ Lifestyle",
        "delivery_reliability": 90,
        "resale_premium": 15,
        "avg_price_sqm": 75000,
        "flagship_projects": ["Allegria", "Eastown", "Villette", "The Estates"],
    },
    "palm hills": {
        "tier": 1,
        "name_ar": "بالم هيلز",
        "name_en": "Palm Hills",
        "competitors": ["emaar", "sodic", "mountain view"],
        "strength": "Large Master-Planned Communities",
        "strength_ar": "مشاريع ضخمة متكاملة",
        "delivery_reliability": 88,
        "resale_premium": 12,
        "avg_price_sqm": 68000,
        "flagship_projects": ["Palm Hills October", "Palm Hills New Cairo", "Badya"],
    },
    "ora": {
        "tier": 1,
        "name_ar": "أورا",
        "name_en": "Ora Developers",
        "competitors": ["sodic", "emaar"],
        "strength": "Premium Design & Finishing",
        "strength_ar": "تصميم وتشطيب بريميوم",
        "delivery_reliability": 92,
        "resale_premium": 18,
        "avg_price_sqm": 90000,
        "flagship_projects": ["ZED East", "ZED West", "Silversands"],
    },
    "mountain view": {
        "tier": 1,
        "name_ar": "ماونتن ڤيو",
        "name_en": "Mountain View",
        "competitors": ["emaar", "palm hills", "hyde park"],
        "strength": "Community Premium & Landscaping",
        "strength_ar": "بريميوم المجتمع والمساحات الخضراء",
        "delivery_reliability": 85,
        "resale_premium": 15,
        "avg_price_sqm": 72000,
        "flagship_projects": ["iCity", "Mountain View Ras El Hikma", "Lagoon Beach Park"],
    },
    "hyde park": {
        "tier": 2,
        "name_ar": "هايد بارك",
        "name_en": "Hyde Park Developments",
        "competitors": ["mountain view", "tatweer misr", "lmd"],
        "strength": "Value for Money",
        "strength_ar": "قيمة مقابل السعر",
        "delivery_reliability": 82,
        "resale_premium": 8,
        "avg_price_sqm": 55000,
        "flagship_projects": ["Hyde Park New Cairo", "Coast 82"],
    },
    "tatweer misr": {
        "tier": 2,
        "name_ar": "تطوير مصر",
        "name_en": "Tatweer Misr",
        "competitors": ["hyde park", "lmd", "better home"],
        "strength": "Flexible Payment Plans",
        "strength_ar": "خطط سداد مرنة",
        "delivery_reliability": 78,
        "resale_premium": 5,
        "avg_price_sqm": 48000,
        "flagship_projects": ["Il Monte Galala", "Fouka Bay", "D-Bay"],
    },
    "city edge": {
        "tier": 2,
        "name_ar": "سيتي إيدج",
        "name_en": "City Edge Developments",
        "competitors": ["tatweer misr", "al marasem"],
        "strength": "Government-Backed Reliability",
        "strength_ar": "شركة حكومية = ضمان التسليم",
        "delivery_reliability": 95,
        "resale_premium": 10,
        "avg_price_sqm": 52000,
        "flagship_projects": ["Etapa", "North Edge", "Mazarine"],
    },
    "taj misr": {
        "tier": 3,
        "name_ar": "تاج مصر",
        "name_en": "Taj Misr",
        "competitors": ["better home", "capital group"],
        "strength": "Budget-Friendly Options",
        "strength_ar": "أسعار اقتصادية",
        "delivery_reliability": 70,
        "resale_premium": 0,
        "avg_price_sqm": 35000,
        "flagship_projects": ["Taj City", "De Joya"],
    },
}


@dataclass
class ROIAnalysis:
    """ROI calculation result."""
    rental_yield: float
    capital_appreciation: float
    total_annual_return: float
    break_even_years: float
    annual_rent_income: int
    
    def to_dict(self) -> Dict:
        return {
            "rental_yield": self.rental_yield,
            "capital_appreciation": self.capital_appreciation,
            "total_annual_return": self.total_annual_return,
            "break_even_years": self.break_even_years,
            "annual_rent_income": self.annual_rent_income
        }


@dataclass
class OsoolScore:
    """Property scoring result (formerly Wolf Score)."""
    total_score: int
    value_score: int
    growth_score: int
    developer_score: int
    verdict: str  # BARGAIN, FAIR, PREMIUM
    
    def to_dict(self) -> Dict:
        return {
            "osool_score": self.total_score,
            "score_breakdown": {
                "value": self.value_score,
                "growth": self.growth_score,
                "developer": self.developer_score
            },
            "verdict": self.verdict
        }



# Import Async Session
from sqlalchemy.ext.asyncio import AsyncSession
from .market_analytics_layer import MarketAnalyticsLayer

class AnalyticalEngine:
    """
    The Wolf's Ledger - Zero hallucination analytics.
    
    Refactored for Async & Real-time DB (Protocol 7).
    """
    
    async def get_live_market_data(self, session: AsyncSession) -> Dict[str, float]:
        """Fetch live economic indicators from DB (Inflation, Rates)."""
        try:
            from app.models import MarketIndicator
            result = await session.execute(select(MarketIndicator.key, MarketIndicator.value))
            db_data = {row[0]: row[1] for row in result.all()}
            
            # Merge with defaults (DB overrides constants)
            live_data = MARKET_DATA.copy()
            live_data.update(db_data)
            return live_data
        except Exception as e:
            logger.error(f"Failed to fetch market indicators: {e}")
            return MARKET_DATA

    def calculate_true_roi(self, property_data: Dict, market_data: Optional[Dict] = None) -> ROIAnalysis:
        """
        Calculate true ROI for a property. (Sync - Math only)
        Args:
            property_data: Property dict
            market_data: Optional dict of rates (inflation, appreciation, etc.)
        """
        rates = market_data or MARKET_DATA # Use provided dynamic rates or fallback

        price = property_data.get("price", 0)
        location = property_data.get("location", "")
        # ... logic remains same ...
        if price <= 0:
            return ROIAnalysis(0,0,0,0,0)
        
        # NOTE: This uses hardcoded rates for now. To make this fully dynamic, 
        # we'd need to async fetch growth rates too, but we will keep math sync 
        # for simplicity unless critical.
        appreciation_rate = self._get_appreciation_rate(location)
        rental_yield_rate = self._get_rental_yield(location)
        
        annual_rent = int(price * rental_yield_rate)
        capital_appreciation = price * appreciation_rate
        total_return = annual_rent + capital_appreciation
        total_return_percent = (total_return / price) * 100
        break_even = price / annual_rent if annual_rent > 0 else 99
        
        return ROIAnalysis(
            rental_yield=round(rental_yield_rate * 100, 1),
            capital_appreciation=round(appreciation_rate * 100, 1),
            total_annual_return=round(total_return_percent, 1),
            break_even_years=round(break_even, 1),
            annual_rent_income=annual_rent
        )

    def calculate_replacement_cost(self, property_data: Dict) -> Dict[str, Any]:
        """
        The "Replacement Cost" Logic - Counter for MACRO_SKEPTIC users.
        
        Calculates if a property is priced at or below the cost to build it today.
        Uses 2025 construction cost indices (iron, cement, labor inflation).
        
        ARGUMENT: "You're buying at cost. To BUILD this unit today costs [X]. You're paying [Y]."
        
        Args:
            property_data: Property dict with price, size_sqm
            
        Returns:
            Dict with replacement cost analysis and verdicts
        """
        area_sqm = property_data.get('size_sqm', 0) or property_data.get('area', 0)
        unit_price = property_data.get('price', 0)
        
        if area_sqm <= 0 or unit_price <= 0:
            return {
                "replacement_cost": 0,
                "replacement_cost_ratio": 0,
                "is_inflation_safe": False,
                "verdict_ar": "بيانات غير كافية",
                "verdict_en": "Insufficient data"
            }
        
        # Get construction costs from constants
        base_cost = CONSTRUCTION_COSTS["base_cost_sqm"]
        cost_index = CONSTRUCTION_COSTS["cost_index_2025"]
        land_share = CONSTRUCTION_COSTS["land_value_share"]
        
        # Calculate replacement cost
        construction_cost = area_sqm * base_cost * cost_index
        estimated_land_value = unit_price * land_share
        replacement_cost = construction_cost + estimated_land_value
        
        # Calculate price per sqm
        price_per_sqm = unit_price / area_sqm
        replacement_cost_per_sqm = replacement_cost / area_sqm
        
        # Determine if it's at replacement cost (within 10% margin)
        is_at_replacement_cost = unit_price <= (replacement_cost * 1.10)
        is_below_replacement_cost = unit_price < replacement_cost
        
        # Generate verdicts
        if is_below_replacement_cost:
            verdict_ar = "أقل من تكلفة الإحلال - لقطة"
            verdict_en = "Below Replacement Cost - BARGAIN"
            verdict_category = "BARGAIN"
        elif is_at_replacement_cost:
            verdict_ar = "تسعير عند تكلفة الإحلال - آمن"
            verdict_en = "At Replacement Cost - SAFE"
            verdict_category = "SAFE"
        else:
            verdict_ar = "بريميوم فوق تكلفة الإحلال"
            verdict_en = "Premium Above Replacement Cost"
            verdict_category = "PREMIUM"
        
        return {
            "replacement_cost": int(replacement_cost),
            "replacement_cost_per_sqm": int(replacement_cost_per_sqm),
            "unit_price_per_sqm": int(price_per_sqm),
            "replacement_cost_ratio": round(unit_price / replacement_cost, 2),
            "is_inflation_safe": is_at_replacement_cost,
            "is_below_replacement": is_below_replacement_cost,
            "verdict_category": verdict_category,
            "verdict_ar": verdict_ar,
            "verdict_en": verdict_en,
            # Talking point for AI
            "talking_point_ar": f"الوحدة دي سعرها {int(price_per_sqm):,} جنيه/متر. تكلفة بناءها النهاردة {int(replacement_cost_per_sqm):,} جنيه/متر. يعني حضرتك بتشتري بتكلفة الإحلال تقريباً.",
            "talking_point_en": f"This unit is priced at {int(price_per_sqm):,} EGP/sqm. Building it today would cost {int(replacement_cost_per_sqm):,} EGP/sqm. You're buying near replacement cost."
        }

    # Inflation Hedge & Bank vs Property (Math based on constants)
    def calculate_inflation_hedge(
        self,
        initial_investment: int,
        years: int = 5
    ) -> Dict[str, Any]:
        """
        Calculate inflation hedge comparison: Property vs Cash vs Bank CDs.

        Shows how real estate protects against inflation compared to alternatives.
        Egyptian market context: High inflation (13.6%), high bank rates (22%),
        but property appreciation (20%+) + rental yield (7.5%) beats both.
        """
        try:
            inflation_rate = MARKET_DATA.get("inflation_rate", 0.136)
            bank_rate = MARKET_DATA.get("bank_cd_rate", 0.22)
            property_appreciation = MARKET_DATA.get("property_appreciation", 0.20)
            rental_yield = MARKET_DATA.get("rental_yield_avg", 0.075)

            projections = []
            cash_value = initial_investment
            bank_value = initial_investment
            property_value = initial_investment

            for year in range(1, years + 1):
                # Cash loses to inflation
                cash_value = cash_value * (1 - inflation_rate)

                # Bank CD grows but taxed against inflation
                bank_nominal = bank_value * (1 + bank_rate)
                bank_real = bank_nominal * (1 - inflation_rate)
                bank_value = bank_nominal  # Track nominal for display

                # Property grows + generates rental income
                property_value = property_value * (1 + property_appreciation)
                rental_income = initial_investment * rental_yield * year

                projections.append({
                    "year": year,
                    "cash_value": int(cash_value),
                    "bank_value": int(bank_value),
                    "bank_real_value": int(bank_real),
                    "property_value": int(property_value),
                    "property_with_rent": int(property_value + rental_income),
                    "rental_income_cumulative": int(rental_income)
                })

            final = projections[-1]
            total_property_return = final["property_with_rent"] - initial_investment
            total_bank_return = final["bank_value"] - initial_investment

            return {
                "initial_investment": initial_investment,
                "years": years,
                "projections": projections,
                "summary": {
                    "final_property_value": final["property_with_rent"],
                    "final_bank_value": final["bank_value"],
                    "final_cash_value": final["cash_value"],
                    "property_gain": total_property_return,
                    "bank_gain": total_bank_return,
                    "property_vs_bank_advantage": total_property_return - total_bank_return,
                    "property_beats_bank": total_property_return > total_bank_return
                },
                "rates_used": {
                    "inflation": inflation_rate,
                    "bank_cd": bank_rate,
                    "property_growth": property_appreciation,
                    "rental_yield": rental_yield
                },
                "verdict_ar": "العقار بيحميك من التضخم + بيجيبلك إيجار",
                "verdict_en": "Property hedges inflation + generates rental income"
            }
        except Exception as e:
            logger.error(f"Failed to calculate inflation hedge: {e}")
            return {
                "initial_investment": initial_investment,
                "years": years,
                "projections": [],
                "summary": {},
                "error": str(e)
            }

    def calculate_bank_vs_property(
        self,
        initial_investment: int,
        years: int = 5
    ) -> Dict[str, Any]:
        """
        Compare Bank CD investment vs Property investment.

        Egyptian market context (2025-2026):
        - Bank CDs: 22% nominal return
        - Property: 20% appreciation + 7.5% rental yield = ~27.5% effective return
        - After inflation adjustment, property wins
        """
        try:
            bank_rate = MARKET_DATA.get("bank_cd_rate", 0.22)
            property_appreciation = MARKET_DATA.get("property_appreciation", 0.20)
            rental_yield = MARKET_DATA.get("rental_yield_avg", 0.075)
            inflation_rate = MARKET_DATA.get("inflation_rate", 0.136)

            data_points = []
            bank_value = initial_investment
            property_value = initial_investment
            cumulative_rent = 0

            for year in range(1, years + 1):
                # Bank grows at CD rate
                bank_value = bank_value * (1 + bank_rate)

                # Property appreciates + generates rent
                property_value = property_value * (1 + property_appreciation)
                yearly_rent = initial_investment * rental_yield
                cumulative_rent += yearly_rent

                data_points.append({
                    "year": year,
                    "bank_value": int(bank_value),
                    "property_value": int(property_value),
                    "cumulative_rent": int(cumulative_rent),
                    "property_total": int(property_value + cumulative_rent)
                })

            final = data_points[-1]
            bank_total_return = ((final["bank_value"] - initial_investment) / initial_investment) * 100
            property_total_return = ((final["property_total"] - initial_investment) / initial_investment) * 100

            winner = "property" if final["property_total"] > final["bank_value"] else "bank"

            return {
                "initial_investment": initial_investment,
                "years": years,
                "data_points": data_points,
                "summary": {
                    "final_bank_value": final["bank_value"],
                    "final_property_total": final["property_total"],
                    "bank_return_percent": round(bank_total_return, 1),
                    "property_return_percent": round(property_total_return, 1),
                    "winner": winner,
                    "advantage_amount": abs(final["property_total"] - final["bank_value"])
                },
                "rates_used": {
                    "bank_cd": bank_rate,
                    "property_growth": property_appreciation,
                    "rental_yield": rental_yield,
                    "inflation": inflation_rate
                },
                "verdict_ar": f"العقار بيكسب {round(property_total_return - bank_total_return, 1)}% أكتر من البنك",
                "verdict_en": f"Property beats bank by {round(property_total_return - bank_total_return, 1)}%"
            }
        except Exception as e:
            logger.error(f"Failed to calculate bank vs property: {e}")
            return {
                "initial_investment": initial_investment,
                "years": years,
                "data_points": [],
                "summary": {},
                "error": str(e)
            }

    async def score_property(
        self, 
        property_data: Dict, 
        session: Optional[AsyncSession] = None
    ) -> OsoolScore:
        """
        Calculate Osool Score (Async).
        Accepts optional DB session for real-time benchmarking.
        """
        price = property_data.get("price", 0)
        size_sqm = property_data.get("size_sqm", 1) or 1
        location = property_data.get("location", "")
        developer = property_data.get("developer", "").lower() if property_data.get("developer") else ""
        
        # 1. VALUE SCORE (Price per sqm vs market)
        price_per_sqm = price / size_sqm
        
        # Async Fetch of Market Average
        market_avg = await self._get_area_avg_price(location, session)
        
        value_ratio = market_avg / (price_per_sqm or 1)
        value_score = min(100, max(0, int(value_ratio * 70)))
        
        # 2. GROWTH SCORE (Keep sync for now, growth rates are usually static/macro)
        growth_rate = self._get_appreciation_rate(location)
        growth_score = min(100, max(50, int(50 + (growth_rate * 200))))
        
        # 3. DEVELOPER SCORE
        if any(d in developer for d in TIER1_DEVELOPERS):
            developer_score = 95
        elif any(d in developer for d in TIER2_DEVELOPERS):
            developer_score = 80
        else:
            developer_score = 60
        
        # Final weighted score
        total_score = int(
            (value_score * 0.35) +
            (developer_score * 0.35) +
            (growth_score * 0.30)
        )
        
        # Verdict
        if value_score > 85:
            verdict = "BARGAIN"
        elif value_score > 60:
            verdict = "FAIR"
        else:
            verdict = "PREMIUM"
        
        return OsoolScore(
            total_score=total_score,
            value_score=value_score,
            growth_score=growth_score,
            developer_score=developer_score,
            verdict=verdict
        )
    
    async def score_properties(
        self, 
        properties: List[Dict], 
        session: Optional[AsyncSession] = None
    ) -> List[Dict]:
        """
        Score and rank multiple properties (Async).
        """
        if not properties:
            return []
        
        scored = []
        for prop in properties:
            score = await self.score_property(prop, session)
            prop_copy = prop.copy()
            prop_copy.update(score.to_dict())
            scored.append(prop_copy)
        
        # Sort by score (highest first)
        return sorted(scored, key=lambda x: x.get("osool_score", 0), reverse=True)
    
    async def detect_bargains(
        self,
        properties: List[Dict],
        threshold_percent: float = 10.0,
        session: Optional[AsyncSession] = None
    ) -> List[Dict]:
        """
        Find properties significantly below market value (Async).
        """
        bargains = []
        
        for prop in properties:
            price = prop.get("price", 0)
            size_sqm = prop.get("size_sqm", 1) or 1
            location = prop.get("location", "")
            
            price_per_sqm = price / size_sqm
            market_avg = await self._get_area_avg_price(location, session)
            
            if market_avg > 0:
                discount_percent = ((market_avg - price_per_sqm) / market_avg) * 100
                
                if discount_percent >= threshold_percent:
                    bargain = prop.copy()
                    bargain["la2ta_score"] = round(discount_percent, 1)
                    bargain["savings"] = int((market_avg - price_per_sqm) * size_sqm)
                    bargain["market_price_estimate"] = int(market_avg * size_sqm)
                    bargains.append(bargain)
        
        return sorted(bargains, key=lambda x: x.get("la2ta_score", 0), reverse=True)
    
    async def _get_area_avg_price(self, location: str, session: Optional[AsyncSession] = None) -> int:
        """
        Get average price per sqm.
        PRIORITY 1: Real-time DB (if session provided)
        PRIORITY 2: Hardcoded Constants (Fallback)
        """
        # 1. Try DB
        if session:
            analytics = MarketAnalyticsLayer(session)
            pulse = await analytics.get_real_time_market_pulse(location)
            if pulse and pulse.get("avg_price_sqm"):
                return pulse["avg_price_sqm"]
        
        # 2. Fallback
        for area, price in AREA_PRICES.items():
            if area.lower() in location.lower() or location.lower() in area.lower():
                return price
        return 50000  # Default fallback

    def _get_appreciation_rate(self, location: str) -> float:
        """Get appreciation rate for location. (Sync)"""
        for area, rate in AREA_GROWTH.items():
            if area.lower() in location.lower() or location.lower() in area.lower():
                return rate
        return 0.12  # Default 12%
    
    def _get_rental_yield(self, location: str) -> float:
        """Get rental yield for location. (Sync)"""
        # ... logic stays same ...
        high_yield_areas = ["6th October", "Rehab", "Madinaty"]
        for area in high_yield_areas:
            if area.lower() in location.lower():
                return 0.075
        
        low_yield_areas = ["New Capital", "North Coast"]
        for area in low_yield_areas:
            if area.lower() in location.lower():
                return 0.05
        
        return 0.065

    def get_developer_insight(self, developer_name: str, language: str = "ar") -> Optional[Dict[str, Any]]:
        """
        Developer Knowledge Graph: Get relationship-aware insights about a developer.
        
        Answers questions like: "Why is Emaar expensive?" or "Compare Sodic to Palm Hills"
        
        Returns:
            Dict with insight text and data, or None if developer not found
        """
        # Normalize developer name
        dev_key = developer_name.lower().strip()
        
        # Try exact match first
        dev_data = DEVELOPER_GRAPH.get(dev_key)
        
        # Try partial match if not found
        if not dev_data:
            for key, data in DEVELOPER_GRAPH.items():
                if key in dev_key or dev_key in key:
                    dev_data = data
                    dev_key = key
                    break
                # Check Arabic name
                if data.get("name_ar") and data["name_ar"] in developer_name:
                    dev_data = data
                    dev_key = key
                    break
        
        if not dev_data:
            return None
        
        # Get competitor info
        competitors = dev_data.get("competitors", [])
        competitor_insights = []
        for comp in competitors[:3]:  # Top 3 competitors
            comp_data = DEVELOPER_GRAPH.get(comp)
            if comp_data:
                competitor_insights.append({
                    "name": comp_data.get("name_en"),
                    "name_ar": comp_data.get("name_ar"),
                    "avg_price_sqm": comp_data.get("avg_price_sqm", 0),
                    "resale_premium": comp_data.get("resale_premium", 0),
                })
        
        # Generate insight text
        tier_labels = {1: "Tier 1 (Class A)", 2: "Tier 2 (Class B)", 3: "Tier 3 (Budget)"}
        tier_labels_ar = {1: "الفئة الأولى (Class A)", 2: "الفئة الثانية (Class B)", 3: "الفئة الثالثة (اقتصادي)"}
        
        tier = dev_data.get("tier", 2)
        
        if language == "ar":
            insight_text = f"""
{dev_data.get('name_ar')} من {tier_labels_ar.get(tier, 'الفئة الثانية')}.
قوتهم الأساسية: {dev_data.get('strength_ar', '')}
نسبة التسليم في الوقت: {dev_data.get('delivery_reliability', 0)}%
بريميوم إعادة البيع: +{dev_data.get('resale_premium', 0)}% فوق المنافسين
متوسط سعر المتر: {dev_data.get('avg_price_sqm', 0):,} جنيه
"""
            if competitor_insights:
                comp_names = [c['name_ar'] for c in competitor_insights if c.get('name_ar')]
                insight_text += f"المنافسين الرئيسيين: {', '.join(comp_names)}"
        else:
            insight_text = f"""
{dev_data.get('name_en')} is {tier_labels.get(tier, 'Tier 2')}.
Key Strength: {dev_data.get('strength', '')}
On-Time Delivery: {dev_data.get('delivery_reliability', 0)}%
Resale Premium: +{dev_data.get('resale_premium', 0)}% above competitors
Avg Price/sqm: {dev_data.get('avg_price_sqm', 0):,} EGP
"""
            if competitor_insights:
                comp_names = [c['name'] for c in competitor_insights if c.get('name')]
                insight_text += f"Main Competitors: {', '.join(comp_names)}"
        
        return {
            "developer": dev_data.get("name_en"),
            "developer_ar": dev_data.get("name_ar"),
            "tier": tier,
            "tier_label": tier_labels.get(tier),
            "tier_label_ar": tier_labels_ar.get(tier),
            "strength": dev_data.get("strength"),
            "strength_ar": dev_data.get("strength_ar"),
            "delivery_reliability": dev_data.get("delivery_reliability", 0),
            "resale_premium": dev_data.get("resale_premium", 0),
            "avg_price_sqm": dev_data.get("avg_price_sqm", 0),
            "flagship_projects": dev_data.get("flagship_projects", []),
            "competitors": competitor_insights,
            "insight_text": insight_text.strip(),
        }


# ═══════════════════════════════════════════════════════════════
# MARKET INTELLIGENCE CLASS (The Wolf's Gatekeeper)
# ═══════════════════════════════════════════════════════════════

@dataclass
class FeasibilityResult:
    """Result of feasibility screening."""
    is_feasible: bool
    message_ar: str
    message_en: str
    budget_gap: int  # How much more they need
    alternatives: List[Dict]  # Alternative suggestions
    
    def to_dict(self) -> Dict:
        return {
            "is_feasible": self.is_feasible,
            "message_ar": self.message_ar,
            "message_en": self.message_en,
            "budget_gap": self.budget_gap,
            "alternatives": self.alternatives
        }


@dataclass
class PropertyBenchmark:
    """Property benchmarking result."""
    wolf_analysis: str  # BARGAIN_DEAL, FAIR_VALUE, PREMIUM
    price_vs_market_percent: float  # -15% = 15% below market
    market_price_sqm: int
    actual_price_sqm: int
    verdict_ar: str
    verdict_en: str
    
    def to_dict(self) -> Dict:
        return {
            "wolf_analysis": self.wolf_analysis,
            "price_vs_market_percent": self.price_vs_market_percent,
            "market_price_sqm": self.market_price_sqm,
            "actual_price_sqm": self.actual_price_sqm,
            "verdict_ar": self.verdict_ar,
            "verdict_en": self.verdict_en
        }


class MarketIntelligence:
    """
    The Wolf's Gatekeeper - Market intelligence and feasibility screening.
    
    Features:
    1. screen_feasibility() - Check if request is realistic
    2. benchmark_property() - Compare property to market averages
    3. get_area_context() - Get market context for an area
    """
    
    def screen_feasibility(
        self,
        location: str,
        property_type: str,
        budget: int
    ) -> FeasibilityResult:
        """
        Screen if user request is feasible given market realities.
        
        The Gatekeeper Protocol: Never search for impossible requests.
        
        Args:
            location: Requested area (e.g., "new cairo", "التجمع")
            property_type: Type of property (e.g., "villa", "apartment")
            budget: User's budget in EGP
            
        Returns:
            FeasibilityResult with alternatives if not feasible
        """
        # Normalize inputs
        location_key = self._normalize_location(location)
        prop_type = self._normalize_property_type(property_type)
        
        # Get area benchmarks
        area_data = AREA_BENCHMARKS.get(location_key, {})
        
        if not area_data:
            # Unknown area - allow search
            return FeasibilityResult(
                is_feasible=True,
                message_ar="",
                message_en="",
                budget_gap=0,
                alternatives=[]
            )
        
        # Get minimum for property type
        minimums = area_data.get("property_minimums", {})
        min_price = minimums.get(prop_type, 0)
        
        if min_price == 0:
            # Property type not tracked, allow
            return FeasibilityResult(
                is_feasible=True,
                message_ar="",
                message_en="",
                budget_gap=0,
                alternatives=[]
            )
        
        # Check feasibility
        if budget >= min_price:
            return FeasibilityResult(
                is_feasible=True,
                message_ar="",
                message_en="",
                budget_gap=0,
                alternatives=[]
            )
        
        # NOT FEASIBLE - Generate alternatives
        gap = min_price - budget
        alternatives = self._generate_alternatives(location_key, prop_type, budget)
        
        area_name_ar = area_data.get("ar_name", location)
        min_price_m = min_price / 1_000_000
        budget_m = budget / 1_000_000
        gap_m = gap / 1_000_000
        
        message_ar = f"""🛑 **واقع السوق:**
{prop_type.capitalize()} في {area_name_ar} بتبدأ من **{min_price_m:.1f} مليون**.
ميزانيتك {budget_m:.1f} مليون = فرق {gap_m:.1f} مليون.

خليني أوريك بدائل تناسب ميزانيتك."""
        
        message_en = f"""🛑 **Market Reality Check:**
{prop_type.capitalize()}s in {location} start at **{min_price_m:.1f}M EGP**.
Your budget {budget_m:.1f}M = {gap_m:.1f}M gap.

Let me show you alternatives within your budget."""
        
        return FeasibilityResult(
            is_feasible=False,
            message_ar=message_ar,
            message_en=message_en,
            budget_gap=gap,
            alternatives=alternatives
        )
    
    def benchmark_property(
        self,
        property_data: Dict
    ) -> PropertyBenchmark:
        """
        Compare property price against market averages AND replacement cost.
        
        The "Smart" Benchmark:
        1. Market Comparison: Is it cheaper than area average?
        2. Replacement Cost: Is it cheaper than building it today?
        """
        price = property_data.get("price", 0)
        size_sqm = property_data.get("size_sqm", 1) or 1
        location = property_data.get("location", "")
        
        price_per_sqm = price / size_sqm
        market_avg = self._get_area_avg_price(location)
        
        # 1. Market Comparison
        if market_avg > 0:
            diff_percent = ((market_avg - price_per_sqm) / market_avg) * 100
        else:
            diff_percent = 0
            
        # 2. Replacement Cost Calculation (2025 Estimates)
        # Construction Cost: ~25,000 EGP/sqm (High-end)
        # Land Share: ~20,000 EGP/sqm (New Cairo/Zayed average)
        construction_cost_sqm = 25000 
        land_share_cost_sqm = 20000   
        min_replacement_cost = construction_cost_sqm + land_share_cost_sqm
        
        is_below_cost = price_per_sqm < min_replacement_cost
            
        # Determine Wolf Analysis
        if is_below_cost and diff_percent > 0:
             wolf_analysis = "BELOW_COST"
             verdict_ar = "السعر ده تحت تكلفة البنا والأرض! دي فرصة مش هتتكرر."
             verdict_en = "Price is below replacement cost! Rare opportunity."
        elif diff_percent >= 15:
            wolf_analysis = "BARGAIN_DEAL"
            verdict_ar = f"أقل من سعر السوق بـ {diff_percent:.0f}% (لقطة)."
            verdict_en = f"{diff_percent:.0f}% Below Market Price (Bargain)."
        elif diff_percent >= -5:
            wolf_analysis = "FAIR_VALUE"
            verdict_ar = "سعر عادل جداً مقارنة بالسوق."
            verdict_en = "Fair market value."
        elif diff_percent >= -15:
            wolf_analysis = "PREMIUM"
            verdict_ar = "سعر بريميوم (غالباً بسبب الموقع أو التشطيب)."
            verdict_en = "Premium pricing (Location/Finishing)."
        else:
            wolf_analysis = "OVERPRICED"
            verdict_ar = "السعر مبالغ فيه جداً (Overpriced)."
            verdict_en = "Significantly overpriced."
            
        return PropertyBenchmark(
            wolf_analysis=wolf_analysis,
            price_vs_market_percent=round(diff_percent, 1),
            market_price_sqm=market_avg,
            actual_price_sqm=int(price_per_sqm),
            verdict_ar=verdict_ar,
            verdict_en=verdict_en
        )

    def get_market_segment(self, location: str) -> Dict[str, Any]:
        """
        Get market segmentation data for the 'Give-to-Get' protocol.
        Returns Tier 1 / Tier 2 breakdowns.
        """
        normalized_loc = location.lower().replace(" ", "_").replace("6th", "6th") # simplistic fallback
        
        # Try exact match first
        if normalized_loc in MARKET_SEGMENTS:
            data = MARKET_SEGMENTS[normalized_loc]
            data["found"] = True
            return data
            
        # Try partial match
        for key, data in MARKET_SEGMENTS.items():
            if key.replace("_", " ") in location.lower() or location.lower() in key.replace("_", " "):
                data_copy = data.copy()
                data_copy["found"] = True
                return data_copy
                
        return {"found": False}

    def get_avg_price_per_sqm(self, location: str) -> int:
        """Expose average price per sqm publically."""
        return self._get_area_avg_price(location)

    
    def get_area_context(self, location: str) -> Dict:
        """
        Get comprehensive market context for an area.
        
        Used during discovery phase to educate the user.
        """
        location_key = self._normalize_location(location)
        area_data = AREA_BENCHMARKS.get(location_key, {})
        
        if not area_data:
            return {
                "found": False,
                "message": "Area not in database"
            }
        
        avg_sqm = area_data.get("avg_price_sqm", 50000)
        minimums = area_data.get("property_minimums", {})
        tier1 = area_data.get("tier1_developers", [])
        tier2 = area_data.get("tier2_developers", [])
        
        return {
            "found": True,
            "ar_name": area_data.get("ar_name", location),
            "avg_price_sqm": avg_sqm,
            "rental_yield": area_data.get("rental_yield", 0.065),
            "growth_rate": area_data.get("growth_rate", 0.12),
            "apartment_start": minimums.get("apartment", 0),
            "villa_start": minimums.get("villa", 0),
            "tier1_developers": tier1,
            "tier2_developers": tier2,
            "price_context_ar": f"متوسط السعر: {avg_sqm:,} جنيه/متر",
            "price_context_en": f"Average: {avg_sqm:,} EGP/sqm"
        }
    
    def get_market_segment(self, location: str) -> Dict:
        """
        Get market segment data (Class A vs Class B developers).
        
        For the Market Education consultation flow - educates users
        on price ranges before asking for budget.
        
        Args:
            location: Requested area (e.g., "new cairo", "التجمع")
            
        Returns:
            Dict with Class A and Class B developer segmentation
        """
        location_key = self._normalize_location(location)
        
        # Map to MARKET_SEGMENTS key format
        segment_key_map = {
            "new cairo": "new_cairo",
            "sheikh zayed": "sheikh_zayed", 
            "new capital": "new_capital",
            "6th october": "new_cairo",  # Fallback to new_cairo
            "north coast": "new_cairo",   # Fallback
            "maadi": "new_cairo",         # Fallback
        }
        
        segment_key = segment_key_map.get(location_key, "new_cairo")
        segment_data = MARKET_SEGMENTS.get(segment_key, MARKET_SEGMENTS["new_cairo"])
        
        return {
            "found": True,
            "location_key": segment_key,
            "name_ar": segment_data.get("name_ar", location),
            "name_en": segment_data.get("name_en", location),
            "class_a": segment_data.get("class_a", {}),
            "class_b": segment_data.get("class_b", {}),
            "market_floor": segment_data.get("market_floor", 0),
            "market_floor_ar": segment_data.get("market_floor_ar", ""),
            "market_ceiling": segment_data.get("market_ceiling", 0),
            "market_ceiling_ar": segment_data.get("market_ceiling_ar", ""),
        }
    
    def _normalize_location(self, location: str) -> str:
        """Normalize location to benchmark key."""
        loc_lower = location.lower().strip()
        
        # Direct matches
        if loc_lower in AREA_BENCHMARKS:
            return loc_lower
        
        # Arabic to English mapping
        arabic_map = {
            "التجمع": "new cairo",
            "القاهرة الجديدة": "new cairo",
            "الشيخ زايد": "sheikh zayed",
            "زايد": "sheikh zayed",
            "العاصمة": "new capital",
            "العاصمة الإدارية": "new capital",
            "اكتوبر": "6th october",
            "الساحل": "north coast",
            "المعادي": "maadi",
        }
        
        for ar, en in arabic_map.items():
            if ar in location:
                return en
        
        # Partial matches
        for key in AREA_BENCHMARKS.keys():
            if key in loc_lower or loc_lower in key:
                return key
        
        return "new cairo"  # Default
    
    def _normalize_property_type(self, prop_type: str) -> str:
        """Normalize property type."""
        prop_lower = prop_type.lower().strip()
        
        # Check Arabic mapping
        for ar, en in PROPERTY_TYPE_MAP.items():
            if ar in prop_type:
                return en
        
        # English normalization
        if "villa" in prop_lower:
            return "villa"
        elif "town" in prop_lower:
            return "townhouse"
        elif "duplex" in prop_lower:
            return "duplex"
        elif "chalet" in prop_lower or "شاليه" in prop_type:
            return "chalet"
        else:
            return "apartment"
    
    def _generate_alternatives(
        self,
        location_key: str,
        property_type: str,
        budget: int
    ) -> List[Dict]:
        """Generate alternative suggestions for unfeasible request."""
        alternatives = []
        
        # Alternative 1: Different property type in same area
        area_data = AREA_BENCHMARKS.get(location_key, {})
        minimums = area_data.get("property_minimums", {})
        
        for ptype, min_price in minimums.items():
            if min_price <= budget and ptype != property_type:
                alternatives.append({
                    "type": "same_area_different_type",
                    "property_type": ptype,
                    "location": location_key,
                    "min_price": min_price,
                    "message_ar": f"{ptype.capitalize()} في نفس المنطقة (من {min_price/1_000_000:.1f}M)",
                    "message_en": f"{ptype.capitalize()} in same area (from {min_price/1_000_000:.1f}M)"
                })
        
        # Alternative 2: Same property type in cheaper area
        for area_key, area_info in AREA_BENCHMARKS.items():
            if area_key != location_key:
                other_minimums = area_info.get("property_minimums", {})
                other_min = other_minimums.get(property_type, 0)
                
                if other_min > 0 and other_min <= budget:
                    alternatives.append({
                        "type": "same_type_different_area",
                        "property_type": property_type,
                        "location": area_key,
                        "location_ar": area_info.get("ar_name", area_key),
                        "min_price": other_min,
                        "message_ar": f"{property_type.capitalize()} في {area_info.get('ar_name', area_key)} (من {other_min/1_000_000:.1f}M)",
                        "message_en": f"{property_type.capitalize()} in {area_key.title()} (from {other_min/1_000_000:.1f}M)"
                    })
        
        return alternatives[:3]  # Max 3 alternatives

    def _normalize_location(self, location: str) -> str:
        """Normalize location string to key."""
        loc_lower = location.lower()
        if "zayed" in loc_lower: return "sheikh zayed"
        if "tagamo" in loc_lower or "cairo" in loc_lower or "تجمع" in loc_lower: return "new cairo"
        if "capital" in loc_lower or "administrative" in loc_lower or "عاصمة" in loc_lower: return "new capital"
        if "october" in loc_lower or "أكتوبر" in loc_lower: return "6th october"
        if "coast" in loc_lower or "sahel" in loc_lower or "ساحل" in loc_lower: return "north coast"
        if "maadi" in loc_lower or "معادي" in loc_lower: return "maadi"
        return "new cairo" # Default

    def _normalize_property_type(self, ptype: str) -> str:
        """Normalize property type."""
        ptype = ptype.lower()
        if "villa" in ptype or "فيلا" in ptype: return "villa"
        if "town" in ptype or "تاون" in ptype: return "townhouse"
        if "duplex" in ptype or "دوبلكس" in ptype: return "duplex"
        if "chalet" in ptype or "شاليه" in ptype: return "chalet"
        return "apartment"

    def _get_area_avg_price(self, location: str) -> int:
        """Get average price per sqm for location."""
        # Use simple lookup first
        for area, price in AREA_PRICES.items():
            if area.lower() in location.lower() or location.lower() in area.lower():
                return price
        return 50000


# Singleton instances
analytical_engine = AnalyticalEngine()
market_intelligence = MarketIntelligence()

__all__ = [
    "AnalyticalEngine", 
    "analytical_engine", 
    "MarketIntelligence",
    "market_intelligence",
    "ROIAnalysis", 
    "OsoolScore",
    "FeasibilityResult",
    "PropertyBenchmark",
    "MARKET_DATA",
    "AREA_PRICES",
    "AREA_GROWTH",
    "AREA_BENCHMARKS",
    "MARKET_SEGMENTS",
]
