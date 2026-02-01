"""
Sheikh Zayed Property Seed Data
-------------------------------
Real property data for the AMR AI agent to query.
City Edge Etapa is located in Sheikh Zayed, not New Cairo.

Note: Prices are in EGP (Egyptian Pounds) as of 2024-2025.
"""

from typing import List, Dict, Any

# Sheikh Zayed Property Seed Data
SHEIKH_ZAYED_PROPERTIES: List[Dict[str, Any]] = [
    # ═══════════════════════════════════════════════════════════════
    # CITY EDGE Properties (سيتي إيدج) - Etapa Compound
    # ═══════════════════════════════════════════════════════════════
    {
        "title": "City Edge Etapa - 2BR Affordable Apartment",
        "description": "Affordable apartment in Etapa compound. Great entry point for first-time buyers.",
        "type": "Apartment",
        "location": "Sheikh Zayed - Etapa",
        "compound": "Etapa",
        "developer": "City Edge",
        "price": 3800000,
        "price_per_sqm": 25000,
        "size_sqm": 152,
        "bedrooms": 2,
        "bathrooms": 1,
        "finishing": "Semi-Finished",
        "delivery_date": "2026",
        "down_payment": 10,
        "installment_years": 8,
        "monthly_installment": 35600,
        "image_url": "https://images.unsplash.com/photo-1600047509782-20d39509f26d",
        "sale_type": "Developer",
        "wolf_score": 75,
        "roi_percentage": 10.5
    },
    {
        "title": "City Edge Etapa - 3BR Value Apartment",
        "description": "Value-oriented 3BR apartment in Etapa. Best price per sqm in Sheikh Zayed.",
        "type": "Apartment",
        "location": "Sheikh Zayed - Etapa",
        "compound": "Etapa",
        "developer": "City Edge",
        "price": 4200000,
        "price_per_sqm": 24000,
        "size_sqm": 175,
        "bedrooms": 3,
        "bathrooms": 2,
        "finishing": "Semi-Finished",
        "delivery_date": "2026",
        "down_payment": 10,
        "installment_years": 8,
        "monthly_installment": 39000,
        "image_url": "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea",
        "sale_type": "Developer",
        "wolf_score": 76,
        "roi_percentage": 10.8
    },
]

# Market Statistics for Sheikh Zayed (2024-2025)
SHEIKH_ZAYED_MARKET_STATS = {
    "average_price_per_sqm": {
        "class_a_developers": 72000,  # EGP per sqm
        "other_developers": 45000,     # EGP per sqm
        "overall": 55000
    },
    "price_ranges": {
        "2_bedroom": {
            "min": 3800000,
            "max": 9000000,
            "average": 6000000
        },
        "3_bedroom": {
            "min": 4200000,
            "max": 14000000,
            "average": 8000000
        },
    },
    "roi_averages": {
        "class_a_developers": 12.0,  # Percentage
        "other_developers": 10.5,
        "overall": 11.0
    },
    "popular_compounds": [
        "Zed West (Ora)",
        "Sodic West (Sodic)",
        "Palm Hills October (Palm Hills)",
        "Etapa (City Edge)",
    ],
    "year_over_year_appreciation": 12.0,  # Percentage
    "rental_yield": {
        "average": 6.0,  # Percentage
        "class_a": 6.5,
        "other": 5.5
    }
}


def get_sheikh_zayed_properties_by_budget(min_budget: int = 0, max_budget: int = float('inf')) -> List[Dict]:
    """Filter properties by budget range."""
    return [
        p for p in SHEIKH_ZAYED_PROPERTIES
        if min_budget <= p['price'] <= max_budget
    ]


def get_sheikh_zayed_properties_by_developer(developer: str) -> List[Dict]:
    """Filter properties by developer name."""
    return [
        p for p in SHEIKH_ZAYED_PROPERTIES
        if developer.lower() in p['developer'].lower()
    ]


# Export all
__all__ = [
    "SHEIKH_ZAYED_PROPERTIES",
    "SHEIKH_ZAYED_MARKET_STATS",
    "get_sheikh_zayed_properties_by_budget",
    "get_sheikh_zayed_properties_by_developer"
]
