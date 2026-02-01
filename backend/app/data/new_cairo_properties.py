"""
New Cairo Property Seed Data
----------------------------
Real property data for the AMR AI agent to query.
This data represents actual market prices and developers in New Cairo (التجمع الخامس).

Note: Prices are in EGP (Egyptian Pounds) as of 2024-2025.
"""

from typing import List, Dict, Any

# Class A Developers (مطورين الفئة الأولى)
CLASS_A_DEVELOPERS = ["Emaar", "Sodic", "Marakez", "Mountain View", "La Vista", "Lake View", "Al Marasem"]

# New Cairo Property Seed Data
NEW_CAIRO_PROPERTIES: List[Dict[str, Any]] = [
    # ═══════════════════════════════════════════════════════════════
    # CLASS A DEVELOPERS - Premium Tier
    # ═══════════════════════════════════════════════════════════════

    # EMAAR Properties (إعمار)
    {
        "title": "Emaar Mivida - 3BR Apartment with Garden View",
        "description": "Luxurious 3-bedroom apartment in Mivida compound with stunning garden views. Fully finished with high-end materials. 24/7 security, clubhouse, and international school nearby.",
        "type": "Apartment",
        "location": "New Cairo - Mivida",
        "compound": "Mivida",
        "developer": "Emaar",
        "price": 12500000,
        "price_per_sqm": 52000,
        "size_sqm": 240,
        "bedrooms": 3,
        "bathrooms": 3,
        "finishing": "Fully Finished",
        "delivery_date": "Ready to Move",
        "down_payment": 10,
        "installment_years": 7,
        "monthly_installment": 134000,
        "image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9",
        "sale_type": "Developer",
        "wolf_score": 92,
        "roi_percentage": 15.5
    },
    {
        "title": "Emaar Mivida - 2BR Modern Apartment",
        "description": "Contemporary 2-bedroom apartment with open-plan living. Walking distance to Mivida Strip mall and restaurants.",
        "type": "Apartment",
        "location": "New Cairo - Mivida",
        "compound": "Mivida",
        "developer": "Emaar",
        "price": 8500000,
        "price_per_sqm": 50000,
        "size_sqm": 170,
        "bedrooms": 2,
        "bathrooms": 2,
        "finishing": "Fully Finished",
        "delivery_date": "Ready to Move",
        "down_payment": 15,
        "installment_years": 6,
        "monthly_installment": 100000,
        "image_url": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c",
        "sale_type": "Developer",
        "wolf_score": 88,
        "roi_percentage": 14.2
    },
    {
        "title": "Emaar Uptown Cairo - Penthouse",
        "description": "Stunning penthouse with panoramic city views in Uptown Cairo. Private rooftop terrace, smart home system.",
        "type": "Penthouse",
        "location": "New Cairo - Uptown Cairo",
        "compound": "Uptown Cairo",
        "developer": "Emaar",
        "price": 22000000,
        "price_per_sqm": 55000,
        "size_sqm": 400,
        "bedrooms": 4,
        "bathrooms": 4,
        "finishing": "Fully Finished",
        "delivery_date": "2025",
        "down_payment": 20,
        "installment_years": 8,
        "monthly_installment": 183000,
        "image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c",
        "sale_type": "Developer",
        "wolf_score": 95,
        "roi_percentage": 18.0
    },

    # SODIC Properties (سوديك)
    {
        "title": "Sodic Eastown - 2BR Smart Apartment",
        "description": "Modern smart apartment in Eastown with integrated home automation. Close to AUC and major business districts.",
        "type": "Apartment",
        "location": "New Cairo - Eastown",
        "compound": "Eastown",
        "developer": "Sodic",
        "price": 7200000,
        "price_per_sqm": 45000,
        "size_sqm": 160,
        "bedrooms": 2,
        "bathrooms": 2,
        "finishing": "Fully Finished",
        "delivery_date": "Ready to Move",
        "down_payment": 10,
        "installment_years": 7,
        "monthly_installment": 77000,
        "image_url": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3",
        "sale_type": "Developer",
        "wolf_score": 87,
        "roi_percentage": 13.8
    },
    {
        "title": "Sodic Eastown - 3BR Family Apartment",
        "description": "Spacious family apartment with large balcony overlooking green spaces. Walking distance to international schools.",
        "type": "Apartment",
        "location": "New Cairo - Eastown",
        "compound": "Eastown",
        "developer": "Sodic",
        "price": 9800000,
        "price_per_sqm": 46000,
        "size_sqm": 213,
        "bedrooms": 3,
        "bathrooms": 3,
        "finishing": "Fully Finished",
        "delivery_date": "Ready to Move",
        "down_payment": 15,
        "installment_years": 6,
        "monthly_installment": 115000,
        "image_url": "https://images.unsplash.com/photo-1600573472550-8090b5e0745e",
        "sale_type": "Developer",
        "wolf_score": 89,
        "roi_percentage": 14.5
    },
    {
        "title": "Sodic Villette - Twin House",
        "description": "Premium twin house with private garden in Villette compound. Exclusive community with golf course access.",
        "type": "Twin House",
        "location": "New Cairo - Villette",
        "compound": "Villette",
        "developer": "Sodic",
        "price": 18500000,
        "price_per_sqm": 48000,
        "size_sqm": 385,
        "bedrooms": 4,
        "bathrooms": 4,
        "finishing": "Semi-Finished",
        "delivery_date": "2025",
        "down_payment": 10,
        "installment_years": 8,
        "monthly_installment": 173000,
        "image_url": "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde",
        "sale_type": "Developer",
        "wolf_score": 91,
        "roi_percentage": 16.2
    },

    # MOUNTAIN VIEW Properties (ماونتن فيو)
    {
        "title": "Mountain View iCity - 2BR Garden Apartment",
        "description": "Beautiful garden apartment in the award-winning iCity development. Innovative design with maximum natural light.",
        "type": "Apartment",
        "location": "New Cairo - iCity",
        "compound": "iCity",
        "developer": "Mountain View",
        "price": 6800000,
        "price_per_sqm": 42500,
        "size_sqm": 160,
        "bedrooms": 2,
        "bathrooms": 2,
        "finishing": "Fully Finished",
        "delivery_date": "2025",
        "down_payment": 10,
        "installment_years": 8,
        "monthly_installment": 63750,
        "image_url": "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0",
        "sale_type": "Developer",
        "wolf_score": 86,
        "roi_percentage": 13.5
    },
    {
        "title": "Mountain View iCity - 3BR Roof Apartment",
        "description": "Unique roof apartment with private terrace. Panoramic views of the compound's central park.",
        "type": "Apartment",
        "location": "New Cairo - iCity",
        "compound": "iCity",
        "developer": "Mountain View",
        "price": 9500000,
        "price_per_sqm": 44000,
        "size_sqm": 216,
        "bedrooms": 3,
        "bathrooms": 3,
        "finishing": "Fully Finished",
        "delivery_date": "2025",
        "down_payment": 15,
        "installment_years": 7,
        "monthly_installment": 96000,
        "image_url": "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea",
        "sale_type": "Developer",
        "wolf_score": 88,
        "roi_percentage": 14.0
    },

    # MARAKEZ Properties (مراكز)
    {
        "title": "Marakez Aeon - 2BR Contemporary Apartment",
        "description": "Contemporary apartment in Aeon development with access to premium retail and dining at District 5.",
        "type": "Apartment",
        "location": "New Cairo - Aeon",
        "compound": "Aeon",
        "developer": "Marakez",
        "price": 7500000,
        "price_per_sqm": 44000,
        "size_sqm": 170,
        "bedrooms": 2,
        "bathrooms": 2,
        "finishing": "Fully Finished",
        "delivery_date": "2026",
        "down_payment": 10,
        "installment_years": 8,
        "monthly_installment": 70000,
        "image_url": "https://images.unsplash.com/photo-1600607687644-c7171b42498f",
        "sale_type": "Developer",
        "wolf_score": 85,
        "roi_percentage": 13.2
    },
    {
        "title": "Marakez District 5 - 3BR Luxury Apartment",
        "description": "Luxury apartment above District 5 mall with direct mall access. Prime location for urban lifestyle.",
        "type": "Apartment",
        "location": "New Cairo - District 5",
        "compound": "District 5",
        "developer": "Marakez",
        "price": 11000000,
        "price_per_sqm": 48000,
        "size_sqm": 229,
        "bedrooms": 3,
        "bathrooms": 3,
        "finishing": "Fully Finished",
        "delivery_date": "2025",
        "down_payment": 15,
        "installment_years": 7,
        "monthly_installment": 111000,
        "image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9",
        "sale_type": "Developer",
        "wolf_score": 90,
        "roi_percentage": 15.0
    },

    # AL MARASEM Properties (المراسم)
    {
        "title": "Al Marasem Fifth Square - 2BR Premium Apartment",
        "description": "Premium apartment in Fifth Square with world-class amenities. Minutes from Point 90 Mall.",
        "type": "Apartment",
        "location": "New Cairo - Fifth Square",
        "compound": "Fifth Square",
        "developer": "Al Marasem",
        "price": 8200000,
        "price_per_sqm": 48000,
        "size_sqm": 171,
        "bedrooms": 2,
        "bathrooms": 2,
        "finishing": "Fully Finished",
        "delivery_date": "Ready to Move",
        "down_payment": 20,
        "installment_years": 5,
        "monthly_installment": 109000,
        "image_url": "https://images.unsplash.com/photo-1600585154526-990dced4db0d",
        "sale_type": "Developer",
        "wolf_score": 89,
        "roi_percentage": 14.8
    },

    # ═══════════════════════════════════════════════════════════════
    # OTHER DEVELOPERS - باقي المطورين
    # ═══════════════════════════════════════════════════════════════

    # PALM HILLS Properties
    {
        "title": "Palm Hills Katameya - 2BR Apartment",
        "description": "Modern apartment in the established Katameya compound. Great value with proven track record.",
        "type": "Apartment",
        "location": "New Cairo - Katameya",
        "compound": "Palm Hills Katameya",
        "developer": "Palm Hills",
        "price": 5500000,
        "price_per_sqm": 36000,
        "size_sqm": 153,
        "bedrooms": 2,
        "bathrooms": 2,
        "finishing": "Semi-Finished",
        "delivery_date": "Ready to Move",
        "down_payment": 15,
        "installment_years": 6,
        "monthly_installment": 65000,
        "image_url": "https://images.unsplash.com/photo-1600573472591-ee6981cf81f8",
        "sale_type": "Resale",
        "wolf_score": 82,
        "roi_percentage": 12.5
    },
    {
        "title": "Palm Hills Katameya Extension - 3BR Apartment",
        "description": "Spacious apartment in the Katameya Extension phase. Family-friendly with excellent schools nearby.",
        "type": "Apartment",
        "location": "New Cairo - Katameya Extension",
        "compound": "Palm Hills Katameya Extension",
        "developer": "Palm Hills",
        "price": 6800000,
        "price_per_sqm": 34000,
        "size_sqm": 200,
        "bedrooms": 3,
        "bathrooms": 2,
        "finishing": "Semi-Finished",
        "delivery_date": "2025",
        "down_payment": 10,
        "installment_years": 7,
        "monthly_installment": 73000,
        "image_url": "https://images.unsplash.com/photo-1600047509358-9dc75507daeb",
        "sale_type": "Developer",
        "wolf_score": 83,
        "roi_percentage": 12.8
    },

    # HASSAN ALLAM Properties
    {
        "title": "Hassan Allam Swan Lake - 2BR Lake View Apartment",
        "description": "Beautiful lake view apartment in Swan Lake compound. Tranquil environment with premium amenities.",
        "type": "Apartment",
        "location": "New Cairo - Swan Lake",
        "compound": "Swan Lake",
        "developer": "Hassan Allam",
        "price": 5200000,
        "price_per_sqm": 33000,
        "size_sqm": 158,
        "bedrooms": 2,
        "bathrooms": 2,
        "finishing": "Fully Finished",
        "delivery_date": "Ready to Move",
        "down_payment": 20,
        "installment_years": 5,
        "monthly_installment": 69000,
        "image_url": "https://images.unsplash.com/photo-1600607688969-a5bfcd646154",
        "sale_type": "Resale",
        "wolf_score": 81,
        "roi_percentage": 12.0
    },

    # TATWEER MISR Properties
    {
        "title": "Tatweer Misr Bloomfields - 2BR Garden Apartment",
        "description": "Garden apartment in Bloomfields with lush landscaping. Affordable luxury in a growing area.",
        "type": "Apartment",
        "location": "New Cairo - Bloomfields",
        "compound": "Bloomfields",
        "developer": "Tatweer Misr",
        "price": 4800000,
        "price_per_sqm": 30000,
        "size_sqm": 160,
        "bedrooms": 2,
        "bathrooms": 2,
        "finishing": "Semi-Finished",
        "delivery_date": "2026",
        "down_payment": 10,
        "installment_years": 8,
        "monthly_installment": 45000,
        "image_url": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3",
        "sale_type": "Developer",
        "wolf_score": 79,
        "roi_percentage": 11.5
    },
    {
        "title": "Tatweer Misr Bloomfields - 3BR Family Apartment",
        "description": "Spacious family apartment with views of the central park. Great for growing families.",
        "type": "Apartment",
        "location": "New Cairo - Bloomfields",
        "compound": "Bloomfields",
        "developer": "Tatweer Misr",
        "price": 6200000,
        "price_per_sqm": 31000,
        "size_sqm": 200,
        "bedrooms": 3,
        "bathrooms": 2,
        "finishing": "Semi-Finished",
        "delivery_date": "2026",
        "down_payment": 10,
        "installment_years": 8,
        "monthly_installment": 58000,
        "image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c",
        "sale_type": "Developer",
        "wolf_score": 80,
        "roi_percentage": 11.8
    },

    # LMD Properties
    {
        "title": "LMD One Ninety - 2BR Modern Apartment",
        "description": "Modern apartment in One Ninety with contemporary design. Walking distance to 90th Street commercial area.",
        "type": "Apartment",
        "location": "New Cairo - One Ninety",
        "compound": "One Ninety",
        "developer": "LMD",
        "price": 4500000,
        "price_per_sqm": 28000,
        "size_sqm": 161,
        "bedrooms": 2,
        "bathrooms": 2,
        "finishing": "Semi-Finished",
        "delivery_date": "2025",
        "down_payment": 15,
        "installment_years": 6,
        "monthly_installment": 53000,
        "image_url": "https://images.unsplash.com/photo-1600210491892-03d54c0aaf87",
        "sale_type": "Developer",
        "wolf_score": 78,
        "roi_percentage": 11.2
    },

    # NOTE: City Edge Etapa properties have been moved to sheikh_zayed_properties.py
    # Etapa compound is located in Sheikh Zayed, not New Cairo
]

# Market Statistics for New Cairo (2024-2025)
NEW_CAIRO_MARKET_STATS = {
    "average_price_per_sqm": {
        "class_a_developers": 48000,  # EGP per sqm
        "other_developers": 32000,     # EGP per sqm
        "overall": 38000
    },
    "price_ranges": {
        "2_bedroom": {
            "min": 3800000,
            "max": 8500000,
            "average": 5800000
        },
        "3_bedroom": {
            "min": 4200000,
            "max": 12500000,
            "average": 7500000
        },
        "4_bedroom": {
            "min": 9500000,
            "max": 22000000,
            "average": 15000000
        }
    },
    "roi_averages": {
        "class_a_developers": 15.2,  # Percentage
        "other_developers": 11.8,
        "overall": 13.0
    },
    "popular_compounds": [
        "Mivida (Emaar)",
        "Eastown (Sodic)",
        "Villette (Sodic)",
        "iCity (Mountain View)",
        "Fifth Square (Al Marasem)",
        "Palm Hills Katameya",
        "Swan Lake (Hassan Allam)",
        "Bloomfields (Tatweer Misr)"
    ],
    "year_over_year_appreciation": 12.4,  # Percentage
    "rental_yield": {
        "average": 6.5,  # Percentage
        "class_a": 7.2,
        "other": 5.8
    }
}


def get_properties_by_budget(min_budget: int = 0, max_budget: int = float('inf')) -> List[Dict]:
    """Filter properties by budget range."""
    return [
        p for p in NEW_CAIRO_PROPERTIES
        if min_budget <= p['price'] <= max_budget
    ]


def get_properties_by_developer(developer: str) -> List[Dict]:
    """Filter properties by developer name."""
    return [
        p for p in NEW_CAIRO_PROPERTIES
        if developer.lower() in p['developer'].lower()
    ]


def get_properties_by_bedrooms(bedrooms: int) -> List[Dict]:
    """Filter properties by number of bedrooms."""
    return [
        p for p in NEW_CAIRO_PROPERTIES
        if p['bedrooms'] == bedrooms
    ]


def get_class_a_properties() -> List[Dict]:
    """Get only Class A developer properties."""
    return [
        p for p in NEW_CAIRO_PROPERTIES
        if p['developer'] in CLASS_A_DEVELOPERS
    ]


def get_other_developer_properties() -> List[Dict]:
    """Get properties from non-Class A developers."""
    return [
        p for p in NEW_CAIRO_PROPERTIES
        if p['developer'] not in CLASS_A_DEVELOPERS
    ]


# Export all
__all__ = [
    "NEW_CAIRO_PROPERTIES",
    "NEW_CAIRO_MARKET_STATS",
    "CLASS_A_DEVELOPERS",
    "get_properties_by_budget",
    "get_properties_by_developer",
    "get_properties_by_bedrooms",
    "get_class_a_properties",
    "get_other_developer_properties"
]
