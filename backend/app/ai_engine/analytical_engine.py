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

# Area price data (EGP per sqm, Mar 2026 Market Snapshot)
# SOURCE: Current market snapshot broken down by category and key projects
AREA_PRICES = {
    "New Cairo": 75000,      # Updated: range 38k-160k across projects; weighted avg ~75k
    "Sheikh Zayed": 130000,  # Updated: range 90k-220k across projects; weighted avg ~130k
    "New Capital": 58000,    # Updated: range 40k-67k across projects; avg ~58k
    "6th October": 47000,    # Research: +153.7%
    "North Coast": 175000,   # Updated: Marassi 150k-250k+, MV Ras El Hekma 70k-95k; avg ~175k
    "Red Sea": 100000,       # Updated: El Gouna 100k-180k, Makadi 32k-46k; blended ~100k
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
    "Rehab": 0.15,       # +15% Stable mature area
    "Zamalek": 0.08,     # +8% Limited supply premium
}

# ═══════════════════════════════════════════════════════════════
# HISTORICAL PRICE DATA (2021–2026) — EGP per sqm
# Based on market research: baseline 2021 → sharp spikes 2024/2025
# Used for growth trajectory line charts
# ═══════════════════════════════════════════════════════════════
AREA_PRICE_HISTORY = {
    "New Cairo": {
        2021: 14000, 2022: 18500, 2023: 26000, 2024: 40000, 2025: 55000, 2026: 75000
    },
    "Sheikh Zayed": {
        2021: 13500, 2022: 17000, 2023: 24500, 2024: 38000, 2025: 56000, 2026: 130000
    },
    "New Capital": {
        2021: 20000, 2022: 24000, 2023: 30000, 2024: 40000, 2025: 50000, 2026: 58000
    },
    "6th October": {
        2021: 10000, 2022: 13000, 2023: 18000, 2024: 28000, 2025: 40000, 2026: 47000
    },
    "North Coast": {
        2021: 15000, 2022: 20000, 2023: 35000, 2024: 65000, 2025: 120000, 2026: 175000
    },
    "Red Sea": {
        2021: 12000, 2022: 16000, 2023: 26000, 2024: 55000, 2025: 82000, 2026: 100000
    },
    "Maadi": {
        2021: 18000, 2022: 20000, 2023: 22000, 2024: 25000, 2025: 26950, 2026: 31000
    },
    "Ain Sokhna": {
        2021: 12000, 2022: 16000, 2023: 25000, 2024: 45000, 2025: 75000, 2026: 91200
    },
    "Madinaty": {
        2021: 22000, 2022: 26000, 2023: 32000, 2024: 40000, 2025: 50000, 2026: 55000
    },
    "Rehab": {
        2021: 20000, 2022: 24000, 2023: 29000, 2024: 36000, 2025: 45000, 2026: 50000
    },
}

# Developer-specific price history (per sqm, finished units)
# SOURCE: Mar 2026 Market Snapshot — Key Projects by Category
DEVELOPER_PRICE_HISTORY = {
    # ── East Cairo (New Cairo & Mostakbal City) ──────────────────
    "Emaar (Mivida)": {
        "area": "New Cairo",
        "type": "apartment",
        "market_notes": "Heavy premium on resale; units are fully finished.",
        "price_min": 110000, "price_max": 160000,
        2021: 25000, 2022: 35000, 2023: 48000, 2024: 65000, 2025: 95000, 2026: 135000,
    },
    "Marakez (District 5 & 6)": {
        "area": "New Cairo",
        "type": "mixed",
        "market_notes": "High demand for premium commercial/residential mix.",
        "price_min": 85000, "price_max": 115000,
        2021: 18000, 2022: 25000, 2023: 38000, 2024: 58000, 2025: 80000, 2026: 100000,
    },
    "SODIC (Villette / Eastown)": {
        "area": "New Cairo",
        "type": "apartment",
        "market_notes": "Established, high-end signature communities.",
        "price_min": 80000, "price_max": 120000,
        2021: 18000, 2022: 24000, 2023: 35000, 2024: 50000, 2025: 72000, 2026: 100000,
    },
    "Mountain View (iCity New Cairo)": {
        "area": "New Cairo",
        "type": "apartment",
        "market_notes": "Family-focused with flexible, long-term payment plans.",
        "price_min": 40000, "price_max": 55000,
        2021: 15000, 2022: 22000, 2023: 30000, 2024: 38000, 2025: 45000, 2026: 47500,
    },
    "Palm Hills (Palm Hills New Cairo)": {
        "area": "New Cairo",
        "type": "apartment",
        "market_notes": "Predominantly core and shell or semi-finished units.",
        "price_min": 40000, "price_max": 50000,
        2021: 22000, 2022: 30000, 2023: 38000, 2024: 42000, 2025: 44000, 2026: 45000,
    },
    "Madinet Masr (Taj City / Sarai)": {
        "area": "New Cairo",
        "type": "apartment",
        "market_notes": "Large-scale master plans offering competitive entry points.",
        "price_min": 38000, "price_max": 55000,
        2021: 12000, 2022: 18000, 2023: 25000, 2024: 34000, 2025: 42000, 2026: 46500,
    },
    # ── West Cairo (Sheikh Zayed & New Zayed) ────────────────────
    "Ora (Casa D'or Zayed)": {
        "area": "Sheikh Zayed",
        "type": "apartment",
        "market_notes": "Ultra-luxury, branded residences (Armani).",
        "price_min": 220000, "price_max": 220000,
        2021: 45000, 2022: 65000, 2023: 90000, 2024: 140000, 2025: 195000, 2026: 220000,
    },
    "Ora (ZED West)": {
        "area": "Sheikh Zayed",
        "type": "apartment",
        "market_notes": "Fully finished luxury apartments with park views.",
        "price_min": 120000, "price_max": 160000,
        2021: 25000, 2022: 38000, 2023: 58000, 2024: 85000, 2025: 120000, 2026: 140000,
    },
    "Emaar (Cairo Gate)": {
        "area": "Sheikh Zayed",
        "type": "apartment",
        "market_notes": "Boutique, high-end compound targeting expats and upper-class.",
        "price_min": 120000, "price_max": 150000,
        2021: 28000, 2022: 40000, 2023: 60000, 2024: 88000, 2025: 118000, 2026: 135000,
    },
    "SODIC (The Estates / Karmell)": {
        "area": "Sheikh Zayed",
        "type": "apartment",
        "market_notes": "High demand for signature villas and premium apartments.",
        "price_min": 90000, "price_max": 130000,
        2021: 20000, 2022: 30000, 2023: 48000, 2024: 72000, 2025: 95000, 2026: 110000,
    },
    # ── New Administrative Capital (NAC) ─────────────────────────
    "City Edge (Jade Park / Al Maqsad)": {
        "area": "New Capital",
        "type": "apartment",
        "market_notes": "Government-backed developer; strong ready-to-move options.",
        "price_min": 53000, "price_max": 67000,
        2021: 18000, 2022: 24000, 2023: 32000, 2024: 42000, 2025: 52000, 2026: 60000,
    },
    "TMG (Celia)": {
        "area": "New Capital",
        "type": "apartment",
        "market_notes": "Integrated community highly sought after in the Green River zone.",
        "price_min": 50000, "price_max": 65000,
        2021: 17000, 2022: 22000, 2023: 30000, 2024: 40000, 2025: 50000, 2026: 57500,
    },
    "Sky Capital": {
        "area": "New Capital",
        "type": "apartment",
        "market_notes": "Focuses heavily on high-end investors.",
        "price_min": 40000, "price_max": 50000,
        2021: 14000, 2022: 19000, 2023: 26000, 2024: 34000, 2025: 42000, 2026: 45000,
    },
    # ── Coastal Destinations (North Coast & Red Sea) ─────────────
    "Emaar (Marassi / Soul)": {
        "area": "North Coast",
        "type": "chalet",
        "market_notes": "The absolute peak of the North Coast luxury market.",
        "price_min": 150000, "price_max": 250000,
        2021: 25000, 2022: 38000, 2023: 65000, 2024: 110000, 2025: 170000, 2026: 200000,
    },
    "Orascom (El Gouna)": {
        "area": "Red Sea",
        "type": "chalet",
        "market_notes": "Established resort town with a massive premium on water views.",
        "price_min": 100000, "price_max": 180000,
        2021: 18000, 2022: 28000, 2023: 48000, 2024: 78000, 2025: 118000, 2026: 140000,
    },
    "Mountain View (Ras El Hekma / Evia)": {
        "area": "North Coast",
        "type": "chalet",
        "market_notes": "High demand for summer homes; rapid year-over-year appreciation.",
        "price_min": 70000, "price_max": 95000,
        2021: 15000, 2022: 22000, 2023: 38000, 2024: 58000, 2025: 72000, 2026: 82500,
    },
    "Orascom (Makadi Heights)": {
        "area": "Red Sea",
        "type": "chalet",
        "market_notes": "High-yield, budget-friendly Red Sea investment.",
        "price_min": 32000, "price_max": 46000,
        2021: 8000, 2022: 12000, 2023: 20000, 2024: 28000, 2025: 36000, 2026: 39000,
    },
    # ── Legacy entries (kept for historical chart continuity) ────
    "Hyde Park": {
        "area": "New Cairo",
        "type": "apartment",
        "price_min": 48000, "price_max": 62000,
        2021: 14000, 2022: 20000, 2023: 28000, 2024: 40000, 2025: 52000, 2026: 55000,
    },
}

# ═══════════════════════════════════════════════════════════════
# COMPREHENSIVE AREA BENCHMARKS (Wolf Intelligence Layer)
# ═══════════════════════════════════════════════════════════════
AREA_BENCHMARKS = {
    "new cairo": {
        "ar_name": "التجمع الخامس",
        "avg_price_sqm": 75000,
        "rental_yield": 0.0775, # 7.75% Research
        "growth_rate": 1.57,    # 157% YoY
        "property_minimums": {
            "apartment": 5_000_000, # Market floor raised
            "villa": 15_000_000,
            "townhouse": 9_000_000,
            "duplex": 7_000_000,
        },
        "tier1_developers": ["اعمار", "سوديك", "مراكز", "ماونتن ڤيو", "بالم هيلز", "هايد بارك"],
        "tier2_developers": ["لافيستا", "تطوير مصر", "مدينت مصر"],
        "tier3_developers": ["كابيتال جروب", "السعودية المصرية"],
    },
    "sheikh zayed": {
        "ar_name": "الشيخ زايد",
        "avg_price_sqm": 130000,
        "rental_yield": 0.0687, # 6.87% Research
        "growth_rate": 1.85,    # 185% YoY
        "property_minimums": {
            "apartment": 10_000_000,
            "villa": 30_000_000,
            "townhouse": 18_000_000,
            "duplex": 14_000_000,
        },
        "tier1_developers": ["أورا", "سوديك", "إعمار", "ماونتن ڤيو", "بالم هيلز", "مراكز"],
        "tier2_developers": ["زيد ويست", "O ويست"],
        "tier3_developers": [],
    },
    "new capital": {
        "ar_name": "العاصمة الإدارية",
        "avg_price_sqm": 58000,
        "rental_yield": 0.05,
        "growth_rate": 0.25,
        "property_minimums": {
            "apartment": 3_500_000, # R7 entry
            "villa": 10_000_000,
            "townhouse": 6_500_000,
            "duplex": 5_000_000,
        },
        "tier1_developers": ["سيتي إيدج", "TMG"],
        "tier2_developers": ["مصر إيطاليا", "بيتر هوم", "سكاي كابيتال"],
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
        "avg_price_sqm": 175000, # Updated: Marassi 150k-250k+, MV Ras El Hekma 70k-95k
        "rental_yield": 0.10,   # High seasonal yield
        "growth_rate": 2.09,    # 209% YoY
        "property_minimums": {
            "chalet": 12_000_000,
            "villa": 40_000_000,
            "townhouse": 22_000_000,
        },
        "tier1_developers": ["اعمار (ماراسي/سول)", "ماونتن ڤيو (رأس الحكمة/إيفيا)"],
        "tier2_developers": ["لافيستا", "تطوير مصر", "سيتي إيدج"],
        "tier3_developers": [],
    },
    "red sea": {
        "ar_name": "البحر الأحمر",
        "avg_price_sqm": 100000, # El Gouna 100k-180k, Makadi 32k-46k; blended avg
        "rental_yield": 0.08,
        "growth_rate": 1.50,
        "property_minimums": {
            "chalet": 5_000_000,
            "villa": 20_000_000,
            "townhouse": 10_000_000,
        },
        "tier1_developers": ["أوراسكوم (الجونة)"],
        "tier2_developers": ["أوراسكوم (مكادي هايتس)"],
        "tier3_developers": [],
    },
    "maadi": {
        "ar_name": "المعادي",
        "avg_price_sqm": 29000,  # Aligned with AREA_PRICES 26,950 + 2026 uplift
        "rental_yield": 0.07,
        "growth_rate": 0.39,  # Aligned with AREA_GROWTH 39%
        "property_minimums": {
            "apartment": 3_000_000,
            "villa": 15_000_000,
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
            "developers": ["إعمار/ميفيدا (Emaar/Mivida)", "سوديك/فيليت (SODIC/Villette)", "مراكز/ديستريكت 5-6 (Marakez)", "ماونتن فيو/iCity (Mountain View)", "بالم هيلز (Palm Hills)"],
            "developers_ar": ["إعمار", "سوديك", "مراكز", "ماونتن فيو", "بالم هيلز"],
            "price_range_ar": "٤٠,٠٠٠ - ١٦٠,٠٠٠ جنيه/م²",
            "price_range_en": "40,000 - 160,000 EGP/sqm",
            "avg_price": 15_000_000,
            "avg_price_ar": "١٥ مليون",
            "min_price": 7_000_000,
            "max_price": 35_000_000,
        },
        "class_b": {
            "name_ar": "مطورين الفئة الثانية (Class B)",
            "developers": ["مدينت مصر/تاج سيتي (Madinet Masr)", "هايد بارك (Hyde Park)", "تطوير مصر (Tatweer Misr)", "LMD"],
            "developers_ar": ["مدينت مصر", "هايد بارك", "تطوير مصر", "LMD"],
            "price_range_ar": "٣٨,٠٠٠ - ٥٥,٠٠٠ جنيه/م²",
            "price_range_en": "38,000 - 55,000 EGP/sqm",
            "avg_price": 7_000_000,
            "avg_price_ar": "٧ مليون",
            "min_price": 4_500_000,
            "max_price": 12_000_000,
        },
        "market_floor": 4_500_000,
        "market_floor_ar": "٤.٥ مليون",
        "market_ceiling": 35_000_000,
        "market_ceiling_ar": "٣٥ مليون",
    },
    "sheikh_zayed": {
        "name_ar": "الشيخ زايد",
        "name_en": "Sheikh Zayed",
        "class_a": {
            "name_ar": "مطورين الفئة الأولى (Class A)",
            "developers": ["أورا/كاسا دور زايد (Ora/Casa D'or)", "أورا/ZED West (Ora)", "إعمار/كايرو جيت (Emaar/Cairo Gate)", "سوديك/إيستيتس-كارميل (SODIC)"],
            "developers_ar": ["أورا", "إعمار", "سوديك"],
            "price_range_ar": "٩٠,٠٠٠ - ٢٢٠,٠٠٠+ جنيه/م²",
            "price_range_en": "90,000 - 220,000+ EGP/sqm",
            "avg_price": 35_000_000,
            "avg_price_ar": "٣٥ مليون",
            "min_price": 15_000_000,
            "max_price": 80_000_000,
        },
        "class_b": {
            "name_ar": "مطورين الفئة الثانية (Class B)",
            "developers": ["درة (Dorra)", "كونتيننتال (Continental)", "بدر الدين (Badr Eldin)", "ايوان (Iwan)"],
            "developers_ar": ["درة", "كونتيننتال", "بدر الدين", "ايوان"],
            "price_range_ar": "٤٠,٠٠٠ - ٧٠,٠٠٠ جنيه/م²",
            "price_range_en": "40,000 - 70,000 EGP/sqm",
            "avg_price": 14_000_000,
            "avg_price_ar": "١٤ مليون",
            "min_price": 10_000_000,
            "max_price": 20_000_000,
        },
        "market_floor": 10_000_000,
        "market_floor_ar": "١٠ مليون",
        "market_ceiling": 80_000_000,
        "market_ceiling_ar": "٨٠ مليون",
    },
    "new_capital": {
        "name_ar": "العاصمة الإدارية",
        "name_en": "New Capital",
        "class_a": {
            "name_ar": "مطورين الفئة الأولى (Class A)",
            "developers": ["سيتي إيدج/جيد بارك (City Edge)", "TMG/سيليا (TMG/Celia)"],
            "developers_ar": ["سيتي إيدج", "TMG"],
            "price_range_ar": "٥٠,٠٠٠ - ٦٧,٠٠٠ جنيه/م²",
            "price_range_en": "50,000 - 67,000 EGP/sqm",
            "avg_price": 7_000_000,
            "avg_price_ar": "٧ مليون",
            "min_price": 5_000_000,
            "max_price": 12_000_000,
        },
        "class_b": {
            "name_ar": "مطورين الفئة الثانية (Class B)",
            "developers": ["سكاي كابيتال (Sky Capital)", "مصر إيطاليا", "بيتر هوم", "كابيتال جروب"],
            "developers_ar": ["سكاي كابيتال", "مصر إيطاليا", "بيتر هوم", "كابيتال جروب"],
            "price_range_ar": "٤٠,٠٠٠ - ٥٠,٠٠٠ جنيه/م²",
            "price_range_en": "40,000 - 50,000 EGP/sqm",
            "avg_price": 4_000_000,
            "avg_price_ar": "٤ مليون",
            "min_price": 2_800_000,
            "max_price": 7_000_000,
        },
        "market_floor": 2_800_000,
        "market_floor_ar": "٢.٨ مليون",
        "market_ceiling": 12_000_000,
        "market_ceiling_ar": "١٢ مليون",
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
        "avg_price_sqm": 135000,  # Mivida 110k-160k; Cairo Gate 120k-150k; Marassi 150k-250k+
        "flagship_projects": ["Mivida", "Cairo Gate", "Marassi", "Soul North Coast"],
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
        "avg_price_sqm": 100000,  # Villette/Eastown 80k-120k; The Estates/Karmell 90k-130k
        "flagship_projects": ["Villette", "Eastown", "The Estates", "Karmell"],
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
        "avg_price_sqm": 45000,  # Palm Hills New Cairo 40k-50k
        "flagship_projects": ["Palm Hills New Cairo", "Palm Hills October", "Badya"],
    },
    "ora": {
        "tier": 1,
        "name_ar": "أورا",
        "name_en": "Ora Developers",
        "competitors": ["sodic", "emaar"],
        "strength": "Ultra-Premium Design & Branded Residences",
        "strength_ar": "تصميم فائق الجودة وشقق برندد",
        "delivery_reliability": 92,
        "resale_premium": 18,
        "avg_price_sqm": 170000,  # Casa D'or ~220k; ZED West 120k-160k; blended avg
        "flagship_projects": ["Casa D'or Zayed", "ZED West", "ZED East", "Silversands"],
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
        "avg_price_sqm": 65000,  # iCity 40k-55k; Ras El Hekma/Evia 70k-95k; blended avg
        "flagship_projects": ["iCity New Cairo", "Ras El Hekma", "Evia North Coast", "Lagoon Beach Park"],
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
        "avg_price_sqm": 60000,  # Jade Park/Al Maqsad 53k-67k
        "flagship_projects": ["Jade Park", "Al Maqsad", "Etapa", "North Edge", "Mazarine"],
    },
    "tmg": {
        "tier": 2,
        "name_ar": "TMG القابضة",
        "name_en": "TMG Holding",
        "competitors": ["city edge", "al marasem"],
        "strength": "Integrated Communities in New Capital",
        "strength_ar": "مجتمعات متكاملة في العاصمة الإدارية",
        "delivery_reliability": 85,
        "resale_premium": 8,
        "avg_price_sqm": 57500,  # Celia 50k-65k
        "flagship_projects": ["Celia"],
    },
    "orascom": {
        "tier": 1,
        "name_ar": "أوراسكوم للتطوير",
        "name_en": "Orascom Development",
        "competitors": ["emaar", "mountain view"],
        "strength": "Established Red Sea Resort Towns",
        "strength_ar": "مدن منتجعات راسخة على البحر الأحمر",
        "delivery_reliability": 88,
        "resale_premium": 20,
        "avg_price_sqm": 109000,  # El Gouna 100k-180k; Makadi 32k-46k; blended avg
        "flagship_projects": ["El Gouna", "Makadi Heights", "O West"],
    },
    "madinet masr": {
        "tier": 2,
        "name_ar": "مدينت مصر",
        "name_en": "Madinet Masr",
        "competitors": ["hyde park", "tatweer misr"],
        "strength": "Competitive Entry Points in Large Master Plans",
        "strength_ar": "نقاط دخول تنافسية في مشاريع ضخمة",
        "delivery_reliability": 80,
        "resale_premium": 5,
        "avg_price_sqm": 46500,  # Taj City/Sarai 38k-55k
        "flagship_projects": ["Taj City", "Sarai"],
    },
    "marakez": {
        "tier": 1,
        "name_ar": "مراكز",
        "name_en": "Marakez",
        "competitors": ["emaar", "sodic"],
        "strength": "Premium Commercial/Residential Mix",
        "strength_ar": "تطوير تجاري-سكني متكامل فائق الجودة",
        "delivery_reliability": 82,
        "resale_premium": 12,
        "avg_price_sqm": 100000,  # District 5 & 6: 85k-115k
        "flagship_projects": ["District 5", "District 6"],
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
        # Note: "Taj City" compound belongs to Madinet Masr (not Taj Misr).
        # Taj Misr is a different, smaller developer known for De Joya in the New Capital.
        "flagship_projects": ["De Joya"],
    },
}


# ═══════════════════════════════════════════════════════════════
# MARKET SNAPSHOT — Mar 2026 (by category and key projects)
# SOURCE: Current market intelligence broken down by region.
# Used by the AI to answer "What's the market like in X?" queries.
# ═══════════════════════════════════════════════════════════════
MARKET_SNAPSHOT = {
    "east_cairo": {
        "region_name": "East Cairo (New Cairo & Mostakbal City)",
        "region_name_ar": "شرق القاهرة (التجمع الخامس ومستقبل سيتي)",
        "overview": (
            "East Cairo remains one of the most active markets, with a noticeable "
            "premium on established, ready-to-move communities."
        ),
        "projects": [
            {
                "developer": "Emaar Misr",
                "project": "Mivida",
                "price_min_sqm": 110000,
                "price_max_sqm": 160000,
                "market_notes": "Heavy premium on resale; units are fully finished.",
            },
            {
                "developer": "Marakez",
                "project": "District 5 & District 6",
                "price_min_sqm": 85000,
                "price_max_sqm": 115000,
                "market_notes": "High demand for premium commercial/residential mix.",
            },
            {
                "developer": "SODIC",
                "project": "Villette / Eastown",
                "price_min_sqm": 80000,
                "price_max_sqm": 120000,
                "market_notes": "Established, high-end signature communities.",
            },
            {
                "developer": "Mountain View",
                "project": "iCity New Cairo",
                "price_min_sqm": 40000,
                "price_max_sqm": 55000,
                "market_notes": "Family-focused with flexible, long-term payment plans.",
            },
            {
                "developer": "Palm Hills",
                "project": "Palm Hills New Cairo",
                "price_min_sqm": 40000,
                "price_max_sqm": 50000,
                "market_notes": "Predominantly core and shell or semi-finished units.",
            },
            {
                "developer": "Madinet Masr",
                "project": "Taj City / Sarai",
                "price_min_sqm": 38000,
                "price_max_sqm": 55000,
                "market_notes": "Large-scale master plans offering competitive entry points.",
            },
        ],
    },
    "west_cairo": {
        "region_name": "West Cairo (Sheikh Zayed & New Zayed)",
        "region_name_ar": "غرب القاهرة (الشيخ زايد وزايد الجديدة)",
        "overview": (
            "The West Cairo market, particularly New Zayed, currently commands some of "
            "the highest prices in the country for luxury and ultra-prime developments."
        ),
        "projects": [
            {
                "developer": "Ora Developers",
                "project": "Casa D'or Zayed",
                "price_min_sqm": 220000,
                "price_max_sqm": 220000,
                "market_notes": "Ultra-luxury, branded residences (Armani).",
            },
            {
                "developer": "Ora Developers",
                "project": "ZED West",
                "price_min_sqm": 120000,
                "price_max_sqm": 160000,
                "market_notes": "Fully finished luxury apartments with park views.",
            },
            {
                "developer": "Emaar Misr",
                "project": "Cairo Gate",
                "price_min_sqm": 120000,
                "price_max_sqm": 150000,
                "market_notes": "Boutique, high-end compound targeting expats and upper-class.",
            },
            {
                "developer": "SODIC",
                "project": "The Estates / Karmell",
                "price_min_sqm": 90000,
                "price_max_sqm": 130000,
                "market_notes": "High demand for signature villas and premium apartments.",
            },
        ],
    },
    "new_administrative_capital": {
        "region_name": "New Administrative Capital (NAC)",
        "region_name_ar": "العاصمة الإدارية الجديدة",
        "overview": (
            "Prices in the NAC are steadily rising as government entities fully relocate "
            "and infrastructure comes online. Commercial units here can easily exceed "
            "100,000 EGP per square meter."
        ),
        "projects": [
            {
                "developer": "City Edge",
                "project": "Jade Park / Al Maqsad",
                "price_min_sqm": 53000,
                "price_max_sqm": 67000,
                "market_notes": "Government-backed developer; strong ready-to-move options.",
            },
            {
                "developer": "TMG",
                "project": "Celia",
                "price_min_sqm": 50000,
                "price_max_sqm": 65000,
                "market_notes": "Integrated community highly sought after in the Green River zone.",
            },
            {
                "developer": "Sky Capital",
                "project": "Sky Capital",
                "price_min_sqm": 40000,
                "price_max_sqm": 50000,
                "market_notes": "Focuses heavily on high-end investors.",
            },
        ],
    },
    "coastal": {
        "region_name": "Coastal Destinations (North Coast & Red Sea)",
        "region_name_ar": "الوجهات الساحلية (الساحل الشمالي والبحر الأحمر)",
        "overview": (
            "Coastal properties are increasingly priced in dollars or heavily pegged to "
            "currency fluctuations, driven heavily by expat and Gulf investments."
        ),
        "projects": [
            {
                "developer": "Emaar Misr",
                "project": "Marassi / Soul (North Coast)",
                "price_min_sqm": 150000,
                "price_max_sqm": 250000,
                "market_notes": "The absolute peak of the North Coast luxury market.",
            },
            {
                "developer": "Orascom",
                "project": "El Gouna (Red Sea)",
                "price_min_sqm": 100000,
                "price_max_sqm": 180000,
                "market_notes": "Established resort town with a massive premium on water views.",
            },
            {
                "developer": "Mountain View",
                "project": "Ras El Hekma / Evia (North Coast)",
                "price_min_sqm": 70000,
                "price_max_sqm": 95000,
                "market_notes": "High demand for summer homes; rapid year-over-year appreciation.",
            },
            {
                "developer": "Orascom",
                "project": "Makadi Heights (Red Sea)",
                "price_min_sqm": 32000,
                "price_max_sqm": 46000,
                "market_notes": "High-yield, budget-friendly Red Sea investment.",
            },
        ],
    },
}


# ═══════════════════════════════════════════════════════════════
# RESALE MARKUP DATA (Pre-delivery appreciation by developer)
# Historical data for speculator/flipper segment
# ═══════════════════════════════════════════════════════════════
RESALE_MARKUP_DATA = {
    "emaar_mivida": {"phase_1_launch": 0, "6_months": 15, "1_year": 25, "pre_delivery": 40, "post_delivery": 60},
    "emaar_belle_vie": {"phase_1_launch": 0, "6_months": 18, "1_year": 30, "pre_delivery": 45, "post_delivery": 65},
    "sodic_villette": {"phase_1_launch": 0, "6_months": 12, "1_year": 20, "pre_delivery": 35, "post_delivery": 50},
    "sodic_east": {"phase_1_launch": 0, "6_months": 10, "1_year": 18, "pre_delivery": 30, "post_delivery": 45},
    "palm_hills_new_cairo": {"phase_1_launch": 0, "6_months": 10, "1_year": 18, "pre_delivery": 30, "post_delivery": 45},
    "palm_hills_october": {"phase_1_launch": 0, "6_months": 8, "1_year": 15, "pre_delivery": 25, "post_delivery": 40},
    "mountain_view_icity": {"phase_1_launch": 0, "6_months": 12, "1_year": 22, "pre_delivery": 35, "post_delivery": 55},
    "ora_zed": {"phase_1_launch": 0, "6_months": 15, "1_year": 28, "pre_delivery": 42, "post_delivery": 62},
    "hyde_park": {"phase_1_launch": 0, "6_months": 8, "1_year": 15, "pre_delivery": 25, "post_delivery": 35},
    "tatweer_misr_il_monte": {"phase_1_launch": 0, "6_months": 10, "1_year": 20, "pre_delivery": 30, "post_delivery": 50},
    "city_edge_etapa": {"phase_1_launch": 0, "6_months": 12, "1_year": 22, "pre_delivery": 32, "post_delivery": 48},
}

# Average rent by area (monthly, 2BR, EGP) — for rent-vs-buy comparison
AVERAGE_RENT_BY_AREA = {
    "New Cairo": 18000,
    "Sheikh Zayed": 20000,
    "6th October": 12000,
    "New Capital": 10000,
    "North Coast": 25000,  # Seasonal premium
    "Maadi": 22000,
    "Madinaty": 15000,
    "Rehab": 13000,
    "Mostakbal City": 11000,
    "Ain Sokhna": 15000,
}


# ═══════════════════════════════════════════════════════════════
# PAYMENT PLAN ANALYZER — Egyptian-specific installment intelligence
# 80% of Egyptian purchases are installment-based
# ═══════════════════════════════════════════════════════════════
class PaymentPlanAnalyzer:
    """
    Egyptian-specific payment plan analysis.
    Models: 5-10% down payment, 6-10 year installment,
    quarterly/semi-annual/monthly payments.
    """

    def calculate_installment_plan(
        self,
        total_price: int,
        down_payment_pct: float = 0.10,
        years: int = 8,
        payment_frequency: str = "quarterly",
        location: str = "",
    ) -> Dict:
        """
        Calculate a detailed installment plan with rent comparison.

        Args:
            total_price: Total property price in EGP
            down_payment_pct: Down payment percentage (0.05 to 0.30)
            years: Installment period in years (1-10)
            payment_frequency: quarterly, semi_annual, annual, monthly
            location: For rent comparison context
        """
        down_payment = int(total_price * down_payment_pct)
        remaining = total_price - down_payment

        freq_map = {"quarterly": 4, "semi_annual": 2, "annual": 1, "monthly": 12}
        payments_per_year = freq_map.get(payment_frequency, 4)
        total_payments = years * payments_per_year
        installment = remaining / total_payments if total_payments > 0 else remaining

        monthly_equivalent = int(remaining / (years * 12))

        # Rent comparison (the "you're paying rent anyway" argument)
        rent_comparison = self._compare_to_rent(monthly_equivalent, location)

        # Multiple plan options for comparison
        plans = []
        for dp_pct in [0.05, 0.10, 0.15, 0.20, 0.25]:
            dp = int(total_price * dp_pct)
            rem = total_price - dp
            inst = rem / total_payments if total_payments > 0 else rem
            plans.append({
                "down_payment_pct": dp_pct,
                "down_payment": dp,
                "installment_amount": int(inst),
                "monthly_equivalent": int(rem / (years * 12)),
            })

        return {
            "total_price": total_price,
            "down_payment": down_payment,
            "down_payment_pct": down_payment_pct,
            "remaining": remaining,
            "installment_amount": int(installment),
            "payment_frequency": payment_frequency,
            "years": years,
            "total_payments": total_payments,
            "monthly_equivalent": monthly_equivalent,
            "rent_comparison": rent_comparison,
            "alternative_plans": plans,
        }

    def _compare_to_rent(self, monthly_installment: int, location: str) -> Dict:
        """Compare monthly installment equivalent to average rent."""
        avg_rent = AVERAGE_RENT_BY_AREA.get(location, 15000)

        difference = monthly_installment - avg_rent
        ratio = monthly_installment / avg_rent if avg_rent > 0 else 0

        if ratio <= 1.0:
            verdict_ar = "🟢 القسط الشهري أقل من الإيجار! أنت بتبني ملكية بنفس اللي كنت هتدفعه إيجار"
            verdict_en = "🟢 Monthly installment is LESS than rent! You're building equity for the same cost"
        elif ratio <= 1.3:
            verdict_ar = "🟡 القسط أعلى من الإيجار بشوية، بس أنت بتبني ملكية"
            verdict_en = "🟡 Slightly more than rent, but you're building ownership"
        elif ratio <= 1.5:
            verdict_ar = "🟠 القسط أعلى من الإيجار بـ 30-50%، بس العقار بيزيد قيمته سنوياً"
            verdict_en = "🟠 30-50% more than rent, but the asset appreciates annually"
        else:
            verdict_ar = "🔴 القسط أعلى من الإيجار بكتير — تأكد إن الميزانية مريحة"
            verdict_en = "🔴 Significantly more than rent — ensure this fits your budget"

        return {
            "monthly_installment": monthly_installment,
            "avg_rent": avg_rent,
            "difference": difference,
            "ratio": round(ratio, 2),
            "verdict_ar": verdict_ar,
            "verdict_en": verdict_en,
            "location": location,
        }

    def format_for_prompt(self, plan: Dict, language: str) -> str:
        """Format payment plan data for injection into Claude's context."""
        rc = plan.get("rent_comparison", {})

        if language == "ar":
            return f"""
[PAYMENT_PLAN_INTELLIGENCE]
💰 إجمالي السعر: {plan['total_price']:,} جنيه
💵 المقدم ({plan['down_payment_pct']*100:.0f}%): {plan['down_payment']:,} جنيه
📅 القسط ({plan['payment_frequency']}): {plan['installment_amount']:,} جنيه
📅 المكافئ الشهري: {plan['monthly_equivalent']:,} جنيه/شهر
🏠 متوسط الإيجار في {rc.get('location', 'المنطقة')}: {rc.get('avg_rent', 0):,} جنيه/شهر
{rc.get('verdict_ar', '')}

MENTION THIS when discussing price:
- "المقدم بس {plan['down_payment']:,} جنيه — يعني {plan['down_payment_pct']*100:.0f}% من السعر"
- "القسط الشهري {plan['monthly_equivalent']:,} جنيه — قارنه بالإيجار ({rc.get('avg_rent', 0):,})"
"""
        else:
            return f"""
[PAYMENT_PLAN_INTELLIGENCE]
💰 Total Price: {plan['total_price']:,} EGP
💵 Down Payment ({plan['down_payment_pct']*100:.0f}%): {plan['down_payment']:,} EGP
📅 Installment ({plan['payment_frequency']}): {plan['installment_amount']:,} EGP
📅 Monthly Equivalent: {plan['monthly_equivalent']:,} EGP/month
🏠 Avg Rent in {rc.get('location', 'area')}: {rc.get('avg_rent', 0):,} EGP/month
{rc.get('verdict_en', '')}

MENTION THIS when discussing price:
- "Down payment is only {plan['down_payment']:,} EGP — just {plan['down_payment_pct']*100:.0f}%"
- "Monthly equivalent is {plan['monthly_equivalent']:,} EGP — compare to rent ({rc.get('avg_rent', 0):,})"
"""


# ═══════════════════════════════════════════════════════════════
# DEVELOPER TRUST SCORE CALCULATOR
# Surfaces DEVELOPER_GRAPH data as a visible "Trust Score"
# DELIVERY_FEAR is the #2 psychological state
# ═══════════════════════════════════════════════════════════════
class DeveloperTrustScorer:
    """
    Calculate a 0-100 Trust Score for a developer.
    Based on: Delivery reliability, resale premium, project count, tier.
    """

    def calculate_trust_score(self, developer: str) -> Dict:
        """Calculate a composite trust score for a developer."""
        dev_key = self._normalize_developer(developer)
        dev_data = DEVELOPER_GRAPH.get(dev_key)

        if not dev_data:
            return {"score": 0, "found": False, "developer": developer}

        # Weighted scoring
        delivery_weight = 0.40   # Most important for Egyptians
        resale_weight = 0.25     # Proves value retention
        tier_weight = 0.20       # Brand recognition
        project_weight = 0.15    # Track record depth

        delivery_score = dev_data.get("delivery_reliability", 50)
        resale_score = min(dev_data.get("resale_premium", 0) * 5, 100)
        tier_score = {1: 100, 2: 70, 3: 40}.get(dev_data.get("tier", 3), 30)
        project_score = min(len(dev_data.get("flagship_projects", [])) * 33, 100)

        total = int(
            delivery_score * delivery_weight
            + resale_score * resale_weight
            + tier_score * tier_weight
            + project_score * project_weight
        )

        return {
            "score": total,
            "found": True,
            "developer": dev_data.get("name_en", developer),
            "developer_ar": dev_data.get("name_ar", developer),
            "tier": dev_data.get("tier", 3),
            "delivery_reliability": dev_data.get("delivery_reliability", 0),
            "resale_premium": dev_data.get("resale_premium", 0),
            "strength": dev_data.get("strength", ""),
            "strength_ar": dev_data.get("strength_ar", ""),
            "flagship_projects": dev_data.get("flagship_projects", []),
            "verdict_ar": self._trust_verdict_ar(total),
            "verdict_en": self._trust_verdict_en(total),
            "breakdown": {
                "delivery": int(delivery_score * delivery_weight),
                "resale": int(resale_score * resale_weight),
                "brand": int(tier_score * tier_weight),
                "experience": int(project_score * project_weight),
            },
        }

    def _normalize_developer(self, developer: str) -> str:
        """Normalize developer name to DEVELOPER_GRAPH key."""
        dev_lower = developer.lower().strip()
        # Direct match
        if dev_lower in DEVELOPER_GRAPH:
            return dev_lower
        # Partial match
        for key in DEVELOPER_GRAPH:
            dev_data = DEVELOPER_GRAPH[key]
            if (key in dev_lower or dev_lower in key
                or dev_data.get("name_en", "").lower() in dev_lower
                or dev_lower in dev_data.get("name_en", "").lower()
                or dev_data.get("name_ar", "") in developer):
                return key
        return dev_lower

    def _trust_verdict_ar(self, score: int) -> str:
        if score >= 85:
            return "🟢 مطور موثوق جداً — سجل تسليم ممتاز وقيمة إعادة بيع عالية"
        if score >= 70:
            return "🟡 مطور جيد — التزام معقول بالمواعيد وسمعة سوقية قوية"
        if score >= 50:
            return "🟠 مطور متوسط — تحقق من سجل التسليم والضمانات القانونية"
        return "🔴 احذر — مطور بدون سجل كافي أو سمعة ضعيفة"

    def _trust_verdict_en(self, score: int) -> str:
        if score >= 85:
            return "🟢 Highly Trusted — Excellent delivery track record and strong resale value"
        if score >= 70:
            return "🟡 Good Developer — Reasonable delivery commitment and solid market reputation"
        if score >= 50:
            return "🟠 Average — Verify delivery track record and legal guarantees"
        return "🔴 Caution — Insufficient track record or weak reputation"

    def format_for_prompt(self, trust_data: Dict, language: str) -> str:
        """Format trust score for injection into Claude's context."""
        if not trust_data.get("found"):
            return ""

        s = trust_data
        if language == "ar":
            return f"""
[DEVELOPER_TRUST_SCORE — {s['developer_ar']}]
🛡️ درجة الثقة: {s['score']}/100
{s['verdict_ar']}
- نسبة الالتزام بالتسليم: {s['delivery_reliability']}%
- علاوة إعادة البيع: +{s['resale_premium']}%
- نقطة القوة: {s['strength_ar']}
- أبرز المشاريع: {', '.join(s['flagship_projects'][:3])}

MENTION THIS when user asks about developer or shows DELIVERY_FEAR:
- "المطور ده عنده {s['delivery_reliability']}% نسبة التزام بالتسليم"
- "{s['verdict_ar']}"
"""
        else:
            return f"""
[DEVELOPER_TRUST_SCORE — {s['developer']}]
🛡️ Trust Score: {s['score']}/100
{s['verdict_en']}
- Delivery Reliability: {s['delivery_reliability']}%
- Resale Premium: +{s['resale_premium']}%
- Key Strength: {s['strength']}
- Flagship Projects: {', '.join(s['flagship_projects'][:3])}

MENTION THIS when user asks about developer or shows DELIVERY_FEAR:
- "This developer has a {s['delivery_reliability']}% on-time delivery rate"
- "{s['verdict_en']}"
"""


# ═══════════════════════════════════════════════════════════════
# RESALE INTELLIGENCE — Speculator/Flipper Analytics
# 10% of market are speculators needing pre-delivery markup data
# ═══════════════════════════════════════════════════════════════
class ResaleIntelligence:
    """
    Calculate resale projections for speculators/flippers.
    Pre-delivery markup, ROI on equity, annualized returns.
    """

    def calculate_resale_projection(
        self,
        developer: str,
        compound: str = "",
        total_price: int = 0,
        down_payment_pct: float = 0.10,
        years_to_delivery: int = 3,
    ) -> Dict:
        """Project resale value for speculators."""
        key = self._normalize_key(developer, compound)
        markup_data = RESALE_MARKUP_DATA.get(key, {})

        # Use matched data or area average
        if not markup_data:
            # Fallback: estimate based on developer tier
            dev_key = developer.lower().strip()
            for dk, dd in DEVELOPER_GRAPH.items():
                if dk in dev_key or dev_key in dk:
                    tier = dd.get("tier", 3)
                    resale_prem = dd.get("resale_premium", 5)
                    markup_data = {
                        "phase_1_launch": 0,
                        "6_months": int(resale_prem * 0.5),
                        "1_year": resale_prem,
                        "pre_delivery": int(resale_prem * 2),
                        "post_delivery": int(resale_prem * 3),
                    }
                    break

        if not markup_data:
            return {"available": False, "developer": developer}

        # Calculate ROI on equity (down payment)
        markup_at_delivery = markup_data.get("pre_delivery", 25) / 100
        roi_on_equity = markup_at_delivery / down_payment_pct if down_payment_pct > 0 else 0
        annualized_roi = (
            ((1 + roi_on_equity) ** (1 / years_to_delivery) - 1) * 100
            if years_to_delivery > 0 and roi_on_equity > 0
            else 0
        )

        # Money calculations
        if total_price > 0:
            down_payment = int(total_price * down_payment_pct)
            profit_at_delivery = int(total_price * markup_at_delivery)
        else:
            down_payment = 0
            profit_at_delivery = 0

        return {
            "available": True,
            "developer": developer,
            "compound": compound,
            "markup_timeline": markup_data,
            "projected_markup_pct": round(markup_at_delivery * 100, 1),
            "roi_on_equity_pct": round(roi_on_equity * 100, 1),
            "annualized_roi_pct": round(annualized_roi, 1),
            "down_payment": down_payment,
            "profit_at_delivery": profit_at_delivery,
            "years_to_delivery": years_to_delivery,
            "verdict_ar": (
                f"لو دفعت {down_payment_pct*100:.0f}% مقدم وبعت قبل التسليم، "
                f"العائد على رأس مالك {roi_on_equity*100:.0f}% "
                f"(يعني {annualized_roi:.0f}% سنوياً)"
            ),
            "verdict_en": (
                f"With {down_payment_pct*100:.0f}% down payment and pre-delivery sale, "
                f"ROI on your equity is {roi_on_equity*100:.0f}% "
                f"({annualized_roi:.0f}% annualized)"
            ),
        }

    def _normalize_key(self, developer: str, compound: str) -> str:
        """Normalize developer + compound to RESALE_MARKUP_DATA key."""
        combined = f"{developer}_{compound}".lower().replace(" ", "_").replace("-", "_")
        for key in RESALE_MARKUP_DATA:
            if key in combined or combined in key:
                return key
        # Try developer only
        dev_lower = developer.lower().replace(" ", "_")
        for key in RESALE_MARKUP_DATA:
            if dev_lower in key:
                return key
        return combined

    def format_for_prompt(self, projection: Dict, language: str) -> str:
        """Format resale projection for prompt injection."""
        if not projection.get("available"):
            return ""

        p = projection
        if language == "ar":
            return f"""
[RESALE_INTELLIGENCE — تحليل الربح لمضاربي السوق]
📈 المطور: {p['developer']}
📊 الربح المتوقع قبل التسليم: +{p['projected_markup_pct']}%
💰 العائد على رأس المال المدفوع: {p['roi_on_equity_pct']}%
📅 العائد السنوي: {p['annualized_roi_pct']}%
🏗️ مدة التسليم: {p['years_to_delivery']} سنوات

{p['verdict_ar']}

جدول الربح المتوقع:
- بعد 6 شهور: +{p['markup_timeline'].get('6_months', 0)}%
- بعد سنة: +{p['markup_timeline'].get('1_year', 0)}%
- قبل التسليم: +{p['markup_timeline'].get('pre_delivery', 0)}%
- بعد التسليم: +{p['markup_timeline'].get('post_delivery', 0)}%

USE THIS for SPECULATOR/INVESTOR persona queries about flipping or resale.
"""
        else:
            return f"""
[RESALE_INTELLIGENCE — Speculator Profit Analysis]
📈 Developer: {p['developer']}
📊 Projected Pre-Delivery Markup: +{p['projected_markup_pct']}%
💰 ROI on Equity (Down Payment): {p['roi_on_equity_pct']}%
📅 Annualized ROI: {p['annualized_roi_pct']}%
🏗️ Years to Delivery: {p['years_to_delivery']}

{p['verdict_en']}

Projected Markup Timeline:
- 6 months: +{p['markup_timeline'].get('6_months', 0)}%
- 1 year: +{p['markup_timeline'].get('1_year', 0)}%
- Pre-delivery: +{p['markup_timeline'].get('pre_delivery', 0)}%
- Post-delivery: +{p['markup_timeline'].get('post_delivery', 0)}%

USE THIS for SPECULATOR/INVESTOR persona queries about flipping or resale.
"""


# ═══════════════════════════════════════════════════════════════════════
# V3: TRADE-UP CALCULATOR
# Helps inheritance/upgrade users see what they can afford
# ═══════════════════════════════════════════════════════════════════════
class TradeUpAdvisor:
    """
    V3: Trade-Up Calculator.
    Analyzes: current property value + cash → what they can afford at developer prices.
    Used for INHERITANCE_CONFUSION and UPGRADER persona users.
    """

    def calculate_trade_up(
        self,
        current_property_value: int = 0,
        cash_available: int = 0,
        current_location: str = "",
        target_location: str = "",
        target_type: str = "apartment",  # apartment, villa, twin_house, duplex
    ) -> Dict:
        """
        Calculate trade-up options: sell current + cash → what can you buy?
        
        Args:
            current_property_value: Estimated value of current property (EGP)
            cash_available: Additional cash (EGP)
            current_location: Where current property is
            target_location: Desired area for new property
            target_type: Desired property type
        """
        total_budget = current_property_value + cash_available

        if total_budget <= 0:
            return {"available": False}

        # Get target area pricing
        target_price_sqm = AREA_PRICES.get(target_location, 0)
        if target_price_sqm <= 0:
            # Fuzzy match
            for area, price in AREA_PRICES.items():
                if area.lower() in target_location.lower() or target_location.lower() in area.lower():
                    target_price_sqm = price
                    target_location = area
                    break
        if target_price_sqm <= 0:
            target_price_sqm = 50000  # Default Egyptian average

        # Property type size assumptions (typical Egyptian market)
        _type_sizes = {
            "apartment": {"min_sqm": 90, "mid_sqm": 140, "max_sqm": 220},
            "duplex": {"min_sqm": 180, "mid_sqm": 250, "max_sqm": 350},
            "twin_house": {"min_sqm": 200, "mid_sqm": 280, "max_sqm": 380},
            "villa": {"min_sqm": 250, "mid_sqm": 350, "max_sqm": 500},
        }
        sizes = _type_sizes.get(target_type, _type_sizes["apartment"])

        # What can they afford?
        max_sqm = total_budget / target_price_sqm
        affordable_type = target_type
        if max_sqm < sizes["min_sqm"]:
            # Can't afford target type — suggest downsize
            affordable_type = "apartment"
            sizes = _type_sizes["apartment"]

        # Down payment scenario (10% down, rest installments)
        down_payment_10 = int(total_budget * 0.1)
        remaining_on_plan = total_budget - down_payment_10
        monthly_installment_7y = int(remaining_on_plan / (7 * 12))

        # Growth projection: if they wait vs. trade now
        growth_rate = AREA_GROWTH.get(target_location, 0.15)
        if growth_rate > 1:
            growth_rate = growth_rate * 0.15  # Moderate extreme historical rates

        value_in_1y = int(total_budget * (1 + growth_rate))
        sqm_in_1y = value_in_1y / (target_price_sqm * (1 + growth_rate))
        sqm_lost_by_waiting = max_sqm - sqm_in_1y

        # Current property appreciation if they don't sell
        current_price_sqm = AREA_PRICES.get(current_location, 0)
        if not current_price_sqm:
            for area, price in AREA_PRICES.items():
                if area.lower() in current_location.lower() or current_location.lower() in area.lower():
                    current_price_sqm = price
                    break

        return {
            "available": True,
            "total_budget": total_budget,
            "current_property_value": current_property_value,
            "cash_available": cash_available,
            "target_location": target_location,
            "target_price_sqm": target_price_sqm,
            "max_sqm_affordable": round(max_sqm, 1),
            "affordable_type": affordable_type,
            "suggested_size_range": f"{sizes['min_sqm']}-{sizes['max_sqm']} sqm",
            "down_payment_10pct": down_payment_10,
            "monthly_installment_7y": monthly_installment_7y,
            "if_wait_1y_sqm_lost": round(sqm_lost_by_waiting, 1),
            "growth_rate": round(growth_rate * 100, 1),
        }

    def format_for_prompt(self, result: Dict, language: str) -> str:
        """Format trade-up analysis for Claude context injection."""
        if not result.get("available"):
            return ""

        if language == "ar":
            lines = ["\n[TRADE_UP_ANALYSIS — حاسبة الترقية]"]
            if result["current_property_value"] > 0:
                lines.append(f"💰 قيمة العقار الحالي: {result['current_property_value']:,} جنيه")
            if result["cash_available"] > 0:
                lines.append(f"💵 كاش متاح: {result['cash_available']:,} جنيه")
            lines.append(f"📊 إجمالي الميزانية: {result['total_budget']:,} جنيه")
            lines.append(f"📍 في {result['target_location']}: سعر المتر {result['target_price_sqm']:,} جنيه")
            lines.append(f"📐 تقدر تشتري: حتى {result['max_sqm_affordable']:.0f} متر² ({result['affordable_type']})")
            lines.append(f"💳 لو دفعت 10% مقدم: القسط الشهري ≈ {result['monthly_installment_7y']:,} جنيه (7 سنين)")
            if result["if_wait_1y_sqm_lost"] > 0:
                lines.append(f"⏰ لو استنيت سنة: هتخسر {result['if_wait_1y_sqm_lost']:.0f} متر² بسبب زيادة الأسعار ({result['growth_rate']}%)")
            lines.append("USE: \"لو بعت الشقة القديمة + الكاش اللي معاك، تقدر تشتري [X] متر في [Location]\"")
            return "\n".join(lines)
        else:
            lines = ["\n[TRADE_UP_ANALYSIS — Upgrade Calculator]"]
            if result["current_property_value"] > 0:
                lines.append(f"💰 Current property value: {result['current_property_value']:,} EGP")
            if result["cash_available"] > 0:
                lines.append(f"💵 Available cash: {result['cash_available']:,} EGP")
            lines.append(f"📊 Total budget: {result['total_budget']:,} EGP")
            lines.append(f"📍 In {result['target_location']}: {result['target_price_sqm']:,} EGP/sqm")
            lines.append(f"📐 You can buy: up to {result['max_sqm_affordable']:.0f} sqm ({result['affordable_type']})")
            lines.append(f"💳 With 10% down: monthly ≈ {result['monthly_installment_7y']:,} EGP (7 years)")
            if result["if_wait_1y_sqm_lost"] > 0:
                lines.append(f"⏰ Waiting 1 year: lose {result['if_wait_1y_sqm_lost']:.0f} sqm due to {result['growth_rate']}% price growth")
            lines.append("USE: \"If you sell current + cash, you can buy [X] sqm in [Location]\"")
            return "\n".join(lines)


# Singleton instances for new components
payment_plan_analyzer = PaymentPlanAnalyzer()
developer_trust_scorer = DeveloperTrustScorer()
resale_intelligence = ResaleIntelligence()
trade_up_advisor = TradeUpAdvisor()


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
    """Property scoring result — V2 with rental yield + location premium."""
    total_score: int
    value_score: int
    growth_score: int
    developer_score: int
    rental_score: int       # V2: Rental yield attractiveness
    location_score: int     # V2: Location premium/demand level
    verdict: str  # BARGAIN, FAIR, PREMIUM, BELOW_COST

    def __init__(self, total_score=0, value_score=0, growth_score=0,
                 developer_score=0, rental_score=0, location_score=0, verdict="FAIR"):
        self.total_score = total_score
        self.value_score = value_score
        self.growth_score = growth_score
        self.developer_score = developer_score
        self.rental_score = rental_score
        self.location_score = location_score
        self.verdict = verdict

    def to_dict(self) -> Dict:
        return {
            "osool_score": self.total_score,
            "wolf_score": self.total_score,  # Alias for backwards compatibility
            "score_breakdown": {
                "value": self.value_score,
                "growth": self.growth_score,
                "developer": self.developer_score,
                "rental": self.rental_score,
                "location": self.location_score,
            },
            "verdict": self.verdict
        }



# Import Async Session
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .market_analytics_layer import MarketAnalyticsLayer

class AnalyticalEngine:
    """
    The Wolf's Ledger - Zero hallucination analytics.
    
    Refactored for Async & Real-time DB (Protocol 7).
    """
    
    def format_economic_context(self, market_data: Dict) -> str:
        """Format live economic data for injection into AI prompt."""
        inflation = market_data.get("inflation_rate", 0.136) * 100
        bank_rate = market_data.get("bank_cd_rate", 0.22) * 100
        usd_rate = market_data.get("usd_egp_rate", 51.50)
        real_spread = bank_rate - inflation
        real_growth = market_data.get("real_property_growth", 0.145) * 100
        rental_yield = market_data.get("rental_yield_avg", 0.075) * 100
        nominal_growth = market_data.get("nominal_property_appreciation", 0.304) * 100
        gold = market_data.get("gold_appreciation", 0.15) * 100
        mortgage = market_data.get("mortgage_rate", 0.18) * 100

        return f"""
[LIVE ECONOMIC DATA - VERIFIED FROM DATABASE]
- Inflation Rate: {inflation:.1f}%
- Bank CD Rate: {bank_rate:.1f}%
- Real Bank Yield: {real_spread:+.1f}% (Bank - Inflation = {'NEGATIVE real return' if real_spread < 0 else 'POSITIVE real return'})
- USD/EGP: {usd_rate:.2f}
- Property Growth (Real): {real_growth:.1f}%
- Property Growth (Nominal): {nominal_growth:.1f}% YoY
- Average Rental Yield: {rental_yield:.1f}%
- Gold Appreciation: {gold:.1f}%
- Mortgage Rate: {mortgage:.1f}%

INSTRUCTION: Use these exact numbers when discussing market conditions.
If bank CD rate < inflation, frame bank deposits as losing money in real terms.
Property real growth of {real_growth:.1f}% means property holders beat inflation.
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

    def calculate_price_growth_history(
        self,
        location: str,
        include_developers: bool = True,
    ) -> Dict[str, Any]:
        """
        Return 5-year (2021→2026) price growth trajectory for an area.
        Optionally includes developer-specific price lines.
        Used by the price_growth_chart UI visualization.
        """
        try:
            # Normalize location lookup
            loc_upper = location.strip().title()
            # Fuzzy match: "new cairo", "التجمع الخامس", "fifth settlement" etc.
            loc_map = {
                "التجمع الخامس": "New Cairo",
                "القاهرة الجديدة": "New Cairo",
                "Fifth Settlement": "New Cairo",
                "الشيخ زايد": "Sheikh Zayed",
                "العاصمة الإدارية": "New Capital",
                "أكتوبر": "6th October",
                "السادس من أكتوبر": "6th October",
                "الساحل الشمالي": "North Coast",
                "المعادي": "Maadi",
                "العين السخنة": "Ain Sokhna",
                "مدينتي": "Madinaty",
                "الرحاب": "Rehab",
            }
            resolved = loc_map.get(location.strip(), loc_upper)
            # Try direct match first
            history = AREA_PRICE_HISTORY.get(resolved)
            if not history:
                # Try fuzzy match on keys
                for key in AREA_PRICE_HISTORY:
                    if key.lower() in resolved.lower() or resolved.lower() in key.lower():
                        history = AREA_PRICE_HISTORY[key]
                        resolved = key
                        break

            if not history:
                return {"found": False, "location": location}

            # Build data points
            years_list = sorted([y for y in history.keys() if isinstance(y, int)])
            data_points = []
            for yr in years_list:
                price = history[yr]
                yoy = 0
                if yr - 1 in history and history[yr - 1] > 0:
                    yoy = round(((price - history[yr - 1]) / history[yr - 1]) * 100, 1)
                data_points.append({
                    "year": yr,
                    "price_sqm": price,
                    "yoy_growth": yoy,
                })

            # Overall growth
            start_price = history.get(years_list[0], 0)
            end_price = history.get(years_list[-1], 0)
            total_growth = round(((end_price - start_price) / start_price) * 100, 1) if start_price > 0 else 0

            # Developer lines (only for the same area)
            developer_lines = []
            if include_developers:
                for dev_name, dev_data in DEVELOPER_PRICE_HISTORY.items():
                    if dev_data.get("area", "").lower() == resolved.lower():
                        dev_points = []
                        for yr in years_list:
                            if yr in dev_data:
                                dev_points.append({"year": yr, "price_sqm": dev_data[yr]})
                        if dev_points:
                            dev_start = dev_points[0]["price_sqm"]
                            dev_end = dev_points[-1]["price_sqm"]
                            dev_growth = round(((dev_end - dev_start) / dev_start) * 100, 1) if dev_start > 0 else 0
                            developer_lines.append({
                                "name": dev_name,
                                "type": dev_data.get("type", "apartment"),
                                "data_points": dev_points,
                                "total_growth": dev_growth,
                            })

            return {
                "found": True,
                "location": resolved,
                "location_ar": AREA_BENCHMARKS.get(resolved.lower().replace(" ", " "), {}).get("ar_name", location),
                "data_points": data_points,
                "total_growth_pct": total_growth,
                "start_year": years_list[0],
                "end_year": years_list[-1],
                "start_price": start_price,
                "end_price": end_price,
                "developer_lines": developer_lines,
                "current_growth_rate": AREA_GROWTH.get(resolved, 0),
            }
        except Exception as e:
            logger.error(f"Failed to calculate price growth history: {e}")
            return {"found": False, "location": location, "error": str(e)}

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

        Returns data matching CertificatesVsProperty.tsx contract.
        """
        try:
            bank_rate = MARKET_DATA.get("bank_cd_rate", 0.22)
            property_appreciation = MARKET_DATA.get("property_appreciation", 0.20)
            rental_yield = MARKET_DATA.get("rental_yield_avg", 0.075)
            inflation_rate = MARKET_DATA.get("inflation_rate", 0.136)

            data_points = []
            bank_nominal_val = initial_investment
            property_value = initial_investment
            cumulative_rent = 0

            for year in range(1, years + 1):
                # Bank grows at CD rate (nominal)
                bank_nominal_val = bank_nominal_val * (1 + bank_rate)
                # Bank real value after inflation erosion
                bank_real_val = bank_nominal_val / ((1 + inflation_rate) ** year)

                # Property appreciates + generates rent
                property_value = property_value * (1 + property_appreciation)
                yearly_rent = initial_investment * rental_yield
                cumulative_rent += yearly_rent
                property_total = property_value + cumulative_rent

                data_points.append({
                    "year": year,
                    "label": f"سنة {year}",
                    "label_en": f"Year {year}",
                    "bank_nominal": int(bank_nominal_val),
                    "bank_real": int(bank_real_val),
                    "property_total": int(property_total),
                    "property_value": int(property_value),
                    "cumulative_rent": int(cumulative_rent),
                })

            final = data_points[-1]
            bank_nominal_gain = final["bank_nominal"] - initial_investment
            bank_real_loss = initial_investment - final["bank_real"]
            bank_real_loss_pct = round((bank_real_loss / initial_investment) * 100, 1)
            property_gain_pct = round(((final["property_total"] - initial_investment) / initial_investment) * 100, 1)
            difference = final["property_total"] - final["bank_real"]

            winner = "property" if final["property_total"] > final["bank_nominal"] else "bank"
            advantage_pct = round(property_gain_pct - ((bank_nominal_gain / initial_investment) * 100), 1)

            return {
                "initial_investment": initial_investment,
                "years": years,
                "data_points": data_points,
                "summary": {
                    "bank_nominal_final": final["bank_nominal"],
                    "bank_nominal_gain": int(bank_nominal_gain),
                    "bank_real_final": final["bank_real"],
                    "bank_real_loss": int(bank_real_loss),
                    "bank_real_loss_percent": bank_real_loss_pct,
                    "property_final": final["property_total"],
                    "property_value_only": final["property_value"],
                    "total_rent_earned": final["cumulative_rent"],
                    "property_gain_percent": property_gain_pct,
                    "difference": int(difference),
                    "winner": winner,
                },
                "assumptions": {
                    "bank_cd_rate": bank_rate,
                    "inflation_rate": inflation_rate,
                    "property_appreciation": property_appreciation,
                    "rental_yield": rental_yield,
                    "source": "Central Bank of Egypt & CAPMAS 2025",
                },
                "verdict": {
                    "winner": winner,
                    "headline_ar": "فلوسك في البنك بتخسر قيمتها" if winner == "property" else "الشهادة أفضل حالياً",
                    "headline_en": "Your money in the bank is losing value" if winner == "property" else "Bank CDs are currently better",
                    "message_ar": f"شهادات البنك بتجيب {int(bank_rate*100)}% فايدة بس التضخم {int(inflation_rate*100)}%.\nالعقار بيكسب {advantage_pct}% أكتر من البنك بعد التضخم.",
                    "message_en": f"Bank CDs yield {int(bank_rate*100)}% but inflation is {int(inflation_rate*100)}%.\nProperty beats bank by {advantage_pct}% after inflation adjustment.",
                },
            }
        except Exception as e:
            logger.error(f"Failed to calculate bank vs property: {e}")
            return {
                "initial_investment": initial_investment,
                "years": years,
                "data_points": [],
                "summary": {},
                "assumptions": {},
                "verdict": {},
                "error": str(e)
            }

    async def score_property(
        self,
        property_data: Dict,
        session: Optional[AsyncSession] = None
    ) -> OsoolScore:
        """
        V2 Osool Score — Enhanced multi-factor scoring.

        Factors:
        1. VALUE (25%): Price/sqm vs market average
        2. GROWTH (20%): Area appreciation rate (historical)
        3. DEVELOPER (20%): Developer tier + track record
        4. RENTAL (15%): Expected rental yield attractiveness
        5. LOCATION (20%): Area demand level + infrastructure maturity

        Returns score 0-100 with verdict.
        """
        try:
            price = property_data.get("price", 0) or property_data.get("total_price", 0) or 0
            size_sqm = property_data.get("size_sqm", 0) or property_data.get("area", 0) or property_data.get("size", 0) or 1
            if size_sqm <= 0:
                size_sqm = 1
            location = property_data.get("location", "") or property_data.get("area_name", "") or ""
            developer = (property_data.get("developer", "") or property_data.get("developer_name", "") or "").lower()

            # 1. VALUE SCORE (Price/sqm vs market) — 0-100
            price_per_sqm = price / size_sqm if size_sqm > 0 else 0
            market_avg = await self._get_area_avg_price(location, session)

            if price_per_sqm > 0 and market_avg > 0:
                # Ratio > 1 means cheap vs market, < 1 means expensive
                value_ratio = market_avg / price_per_sqm
                # Map: 0.5 ratio -> 0, 1.0 ratio -> 70, 1.5 ratio -> 100
                value_score = min(100, max(0, int(value_ratio * 70)))
            elif price == 0:
                # No price data — give neutral score
                value_score = 50
            else:
                value_score = 50

            # 2. GROWTH SCORE (Area appreciation) — 0-100
            growth_rate = self._get_appreciation_rate(location)
            # Map: 0% -> 40, 50% -> 60, 100% -> 75, 200% -> 100
            growth_score = min(100, max(40, int(40 + min(growth_rate, 3.0) * 20)))

            # 3. DEVELOPER SCORE — 0-100
            developer_score = 60  # Default for unknown
            if developer:
                if any(d in developer for d in TIER1_DEVELOPERS):
                    developer_score = 95
                elif any(d in developer for d in TIER2_DEVELOPERS):
                    developer_score = 80
                # Check DEVELOPER_GRAPH for additional matches
                for dev_key, dev_data in DEVELOPER_GRAPH.items():
                    dev_names = [dev_key, dev_data.get('name_en', '').lower(), dev_data.get('name_ar', '')]
                    if any(name and name.lower() in developer for name in dev_names):
                        tier = dev_data.get('tier', 3)
                        developer_score = {1: 95, 2: 80}.get(tier, 65)
                        break

            # 4. RENTAL SCORE (Yield attractiveness) — 0-100
            rental_yield = self._get_rental_yield(location)
            # Map: 5% -> 50, 6.5% -> 65, 7.5% -> 75, 10% -> 100
            rental_score = min(100, max(30, int(rental_yield * 1000)))

            # 5. LOCATION SCORE (Demand + infrastructure) — 0-100
            location_score = 60  # Default
            loc_lower = location.lower()
            # Premium locations
            if any(loc in loc_lower for loc in ["new cairo", "التجمع", "cairo", "zayed", "زايد"]):
                location_score = 90
            elif any(loc in loc_lower for loc in ["madinaty", "مدينتي", "rehab", "الرحاب"]):
                location_score = 80
            elif any(loc in loc_lower for loc in ["october", "أكتوبر"]):
                location_score = 75
            elif any(loc in loc_lower for loc in ["capital", "العاصمة"]):
                location_score = 70
            elif any(loc in loc_lower for loc in ["north coast", "الساحل", "sokhna", "سخنة"]):
                location_score = 70
            elif any(loc in loc_lower for loc in ["maadi", "المعادي"]):
                location_score = 85

            # TOTAL WEIGHTED SCORE
            total_score = int(
                (value_score * 0.25) +
                (growth_score * 0.20) +
                (developer_score * 0.20) +
                (rental_score * 0.15) +
                (location_score * 0.20)
            )
            total_score = max(0, min(100, total_score))

            # VERDICT
            if value_score > 85 and total_score > 80:
                verdict = "BELOW_COST"  # Buying below replacement cost
            elif value_score > 75:
                verdict = "BARGAIN"
            elif value_score > 55:
                verdict = "FAIR"
            else:
                verdict = "PREMIUM"

            return OsoolScore(
                total_score=total_score,
                value_score=value_score,
                growth_score=growth_score,
                developer_score=developer_score,
                rental_score=rental_score,
                location_score=location_score,
                verdict=verdict,
            )
        except Exception as e:
            logger.error(f"score_property error: {e}", exc_info=True)
            # Return a safe default instead of crashing
            return OsoolScore(
                total_score=50, value_score=50, growth_score=50,
                developer_score=50, rental_score=50, location_score=50,
                verdict="FAIR"
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

    def get_market_snapshot(self, region: str = None) -> Dict:
        """
        Return the current market snapshot (Mar 2026) broken down by region and key projects.

        Args:
            region: Optional filter — one of 'east_cairo', 'west_cairo',
                    'new_administrative_capital', 'coastal'. If None, returns all regions.

        Returns:
            Dict with region name, overview text, and per-project price ranges.
        """
        if region and region in MARKET_SNAPSHOT:
            return {region: MARKET_SNAPSHOT[region]}
        return MARKET_SNAPSHOT

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

    # ═══════════════════════════════════════════════════════════════
    # RESALE ANALYTICS MODULE (v2)
    # Compare Resale vs Developer pricing, calculate Resale Value Index
    # ═══════════════════════════════════════════════════════════════

    def analyze_resale_value(self, property_data: Dict, market_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Analyze a resale property's value proposition compared to developer pricing.
        
        Key metrics:
        - Resale Premium/Discount vs developer price
        - Price per sqm vs area average
        - Delivery premium (delivered units command premium)
        - Cash-only discount indicator
        - Resale Value Index (RVI): composite score 0-100
        
        Args:
            property_data: Property dict (must have sale_type, price, size_sqm, location)
            market_data: Optional market data override
            
        Returns:
            Dict with resale analysis metrics
        """
        rates = market_data or MARKET_DATA
        
        price = property_data.get("price", 0)
        area_sqm = property_data.get("size_sqm", 0) or property_data.get("area", 0)
        location = property_data.get("location", "")
        sale_type = property_data.get("sale_type", "")
        is_delivered = property_data.get("is_delivered", False)
        is_cash_only = property_data.get("is_cash_only", False)
        finishing = property_data.get("finishing", "")
        
        if price <= 0 or area_sqm <= 0:
            return {
                "resale_analysis": False,
                "reason": "Insufficient data"
            }
        
        price_per_sqm = price / area_sqm
        area_avg_price = self._get_area_avg_price(location)
        
        # 1. Price vs Area Average
        price_vs_avg = ((price_per_sqm - area_avg_price) / area_avg_price) * 100 if area_avg_price > 0 else 0
        
        # 2. Delivery Premium (delivered units typically 15-25% above undelivered)
        DELIVERY_PREMIUM_TYPICAL = 0.20  # 20% typical premium for delivered
        delivery_premium_applied = 0
        if is_delivered:
            # If delivered and below avg + delivery premium, it's a good deal
            expected_delivered_price = area_avg_price * (1 + DELIVERY_PREMIUM_TYPICAL)
            delivery_premium_applied = DELIVERY_PREMIUM_TYPICAL * 100
        else:
            expected_delivered_price = area_avg_price
        
        price_vs_expected = ((price_per_sqm - expected_delivered_price) / expected_delivered_price) * 100
        
        # 3. Cash Discount Factor
        # Cash-only resale often 5-10% cheaper because no installment markup
        CASH_DISCOUNT_TYPICAL = 0.08  # 8%
        cash_factor = CASH_DISCOUNT_TYPICAL * 100 if is_cash_only else 0
        
        # 4. Finishing Value
        finishing_premium = 0
        if finishing and "finished" in finishing.lower():
            finishing_premium = 15  # Finished adds ~15% value
        elif finishing and "semi" in finishing.lower():
            finishing_premium = 7
        
        # 5. Resale Value Index (RVI) — composite 0-100
        rvi_score = 50  # Start at neutral
        
        # Price discount from expected = positive (good deal)
        if price_vs_expected < -15:
            rvi_score += 25  # Great deal
        elif price_vs_expected < -5:
            rvi_score += 15  # Good deal
        elif price_vs_expected < 5:
            rvi_score += 5   # Fair
        else:
            rvi_score -= 10  # Overpriced
        
        # Delivered bonus
        if is_delivered:
            rvi_score += 15  # No delivery risk
        
        # Cash-only vs installments trade-off
        if is_cash_only:
            rvi_score += 5   # Usually cheaper
        
        # Finishing bonus
        if finishing_premium > 10:
            rvi_score += 10
        elif finishing_premium > 0:
            rvi_score += 5
        
        # Location quality
        if area_avg_price > 60000:
            rvi_score += 5   # Premium location
        
        rvi_score = max(0, min(100, rvi_score))
        
        # 6. Verdict
        if rvi_score >= 80:
            verdict_en = "Excellent resale opportunity — below market, delivered, strong area"
            verdict_ar = "فرصة ريسيل ممتازة — أقل من السوق، مسلّمة، منطقة قوية"
        elif rvi_score >= 60:
            verdict_en = "Good resale deal — fairly priced with delivery advantage"
            verdict_ar = "صفقة ريسيل جيدة — سعر معقول مع ميزة التسليم"
        elif rvi_score >= 40:
            verdict_en = "Average resale — compare with developer options for payment flexibility"
            verdict_ar = "ريسيل متوسط — قارن مع خيارات المطور لمرونة الدفع"
        else:
            verdict_en = "Overpriced resale — developer options may offer better value"
            verdict_ar = "ريسيل مبالغ فيه — خيارات المطور قد تكون أفضل"
        
        return {
            "resale_analysis": True,
            "sale_type": sale_type,
            "price_per_sqm": round(price_per_sqm),
            "area_avg_price_sqm": area_avg_price,
            "price_vs_area_avg_pct": round(price_vs_avg, 1),
            "is_delivered": is_delivered,
            "delivery_premium_pct": round(delivery_premium_applied, 1),
            "price_vs_expected_pct": round(price_vs_expected, 1),
            "is_cash_only": is_cash_only,
            "cash_discount_factor_pct": round(cash_factor, 1),
            "finishing": finishing,
            "finishing_premium_pct": finishing_premium,
            "resale_value_index": rvi_score,
            "verdict_en": verdict_en,
            "verdict_ar": verdict_ar,
        }

    def compare_resale_vs_developer(
        self, 
        resale_properties: List[Dict], 
        developer_properties: List[Dict],
        location: str = ""
    ) -> Dict[str, Any]:
        """
        Compare resale vs developer properties in the same area/compound.
        
        Returns side-by-side analysis showing:
        - Average price difference
        - Delivery timeline advantage
        - Payment plan trade-offs
        - Best overall recommendation
        """
        if not resale_properties and not developer_properties:
            return {"comparison": False, "reason": "No properties to compare"}
        
        # Calculate averages for each group
        def avg_metrics(props):
            if not props:
                return {"count": 0, "avg_price": 0, "avg_price_sqm": 0, "avg_area": 0}
            prices = [p.get("price", 0) for p in props if p.get("price", 0) > 0]
            areas = [p.get("size_sqm", 0) or p.get("area", 0) for p in props if (p.get("size_sqm", 0) or p.get("area", 0)) > 0]
            price_sqms = [p.get("price", 0) / (p.get("size_sqm", 0) or p.get("area", 1)) 
                         for p in props 
                         if p.get("price", 0) > 0 and (p.get("size_sqm", 0) or p.get("area", 0)) > 0]
            return {
                "count": len(props),
                "avg_price": round(sum(prices) / len(prices)) if prices else 0,
                "avg_price_sqm": round(sum(price_sqms) / len(price_sqms)) if price_sqms else 0,
                "avg_area": round(sum(areas) / len(areas)) if areas else 0,
            }
        
        resale_avg = avg_metrics(resale_properties)
        dev_avg = avg_metrics(developer_properties)
        
        # Price difference
        if resale_avg["avg_price_sqm"] > 0 and dev_avg["avg_price_sqm"] > 0:
            resale_premium_pct = ((resale_avg["avg_price_sqm"] - dev_avg["avg_price_sqm"]) / dev_avg["avg_price_sqm"]) * 100
        else:
            resale_premium_pct = 0
        
        # Delivery advantage
        resale_delivered = sum(1 for p in resale_properties if p.get("is_delivered"))
        dev_delivered = sum(1 for p in developer_properties if p.get("is_delivered"))
        
        # Payment flexibility
        resale_cash_only = sum(1 for p in resale_properties if p.get("is_cash_only"))
        dev_with_plan = sum(1 for p in developer_properties if p.get("installment_years", 0) > 0)
        
        # Recommendation
        if resale_premium_pct < -5 and resale_delivered > 0:
            recommendation_en = "Resale offers better value: cheaper per sqm AND immediate delivery"
            recommendation_ar = "الريسيل أفضل: أرخص في المتر وتسليم فوري"
        elif resale_premium_pct < 10 and resale_delivered > len(resale_properties) * 0.5:
            recommendation_en = "Resale is comparable in price with delivery advantage — good for immediate movers"
            recommendation_ar = "الريسيل قريب في السعر مع ميزة التسليم الفوري — مناسب للي محتاج ينقل"
        elif dev_with_plan > len(developer_properties) * 0.5:
            recommendation_en = "Developer offers better payment plans — ideal for budget-conscious buyers"
            recommendation_ar = "المطور يقدم خطط دفع أفضل — مثالي للمشترين اللي محتاجين تقسيط"
        else:
            recommendation_en = "Mixed results — evaluate case by case based on your priorities"
            recommendation_ar = "النتائج متنوعة — قيّم كل حالة حسب أولوياتك"
        
        return {
            "comparison": True,
            "location": location,
            "resale": {
                **resale_avg,
                "delivered_count": resale_delivered,
                "cash_only_count": resale_cash_only,
            },
            "developer": {
                **dev_avg,
                "delivered_count": dev_delivered,
                "with_payment_plan": dev_with_plan,
            },
            "resale_premium_pct": round(resale_premium_pct, 1),
            "recommendation_en": recommendation_en,
            "recommendation_ar": recommendation_ar,
        }


# Singleton instances
analytical_engine = AnalyticalEngine()
market_intelligence = MarketIntelligence()

__all__ = [
    "AnalyticalEngine", 
    "analytical_engine", 
    "MarketIntelligence",
    "market_intelligence",
    "PaymentPlanAnalyzer",
    "payment_plan_analyzer",
    "DeveloperTrustScorer",
    "developer_trust_scorer",
    "ResaleIntelligence",
    "resale_intelligence",
    "ROIAnalysis", 
    "OsoolScore",
    "FeasibilityResult",
    "PropertyBenchmark",
    "MARKET_DATA",
    "AREA_PRICES",
    "AREA_GROWTH",
    "AREA_BENCHMARKS",
    "AREA_PRICE_HISTORY",
    "DEVELOPER_PRICE_HISTORY",
    "MARKET_SEGMENTS",
    "MARKET_SNAPSHOT",
    "DEVELOPER_GRAPH",
    "RESALE_MARKUP_DATA",
    "AVERAGE_RENT_BY_AREA",
]
