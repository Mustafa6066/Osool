"""
Property Data Loader
--------------------
Loads real property data from the public data.js file.
This ensures the AI only uses actual market data, not mock data.
"""

import json
import os
import re
from typing import List, Dict, Any, Optional

# Path to the data file
DATA_FILE_PATH = os.path.join(
    os.path.dirname(__file__),
    '..', '..', '..', 'public', 'assets', 'js', 'data.js'
)

# Cached data
_cached_data: Optional[Dict[str, Any]] = None


def load_property_data() -> Dict[str, Any]:
    """
    Load and parse the property data from data.js file.
    Returns the parsed egyptianData object.
    """
    global _cached_data

    if _cached_data is not None:
        return _cached_data

    try:
        # Try multiple possible paths
        possible_paths = [
            DATA_FILE_PATH,
            os.path.join(os.getcwd(), 'public', 'assets', 'js', 'data.js'),
            os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'public', 'assets', 'js', 'data.js'),
        ]

        data_content = None
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    data_content = f.read()
                break

        if data_content is None:
            print("Warning: data.js not found, returning empty data")
            return {"metadata": {}, "properties": []}

        # Extract JSON from "window.egyptianData = {...}"
        match = re.search(r'window\.egyptianData\s*=\s*(\{[\s\S]*\})\s*;?\s*$', data_content)
        if match:
            json_str = match.group(1)
            _cached_data = json.loads(json_str)
            return _cached_data
        else:
            print("Warning: Could not parse egyptianData from data.js")
            return {"metadata": {}, "properties": []}

    except Exception as e:
        print(f"Error loading property data: {e}")
        return {"metadata": {}, "properties": []}


def get_all_properties() -> List[Dict[str, Any]]:
    """Get all properties from the data file."""
    data = load_property_data()
    return data.get("properties", [])


def get_metadata() -> Dict[str, Any]:
    """Get market metadata."""
    data = load_property_data()
    return data.get("metadata", {})


def search_properties(
    location: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    bedrooms: Optional[int] = None,
    property_type: Optional[str] = None,
    developer: Optional[str] = None,
    compound: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search properties with filters.

    Args:
        location: Filter by location (e.g., "New Cairo", "Sheikh Zayed")
        min_price: Minimum price in EGP
        max_price: Maximum price in EGP
        bedrooms: Number of bedrooms
        property_type: Type (Apartment, Villa, Townhouse, etc.)
        developer: Developer name
        compound: Compound name
        limit: Maximum number of results

    Returns:
        List of matching properties
    """
    properties = get_all_properties()
    results = []

    for prop in properties:
        # Location filter
        if location and location.lower() not in prop.get("location", "").lower():
            continue

        # Price filters
        price = prop.get("price", 0)
        if min_price and price < min_price:
            continue
        if max_price and price > max_price:
            continue

        # Bedrooms filter
        if bedrooms is not None and prop.get("bedrooms") != bedrooms:
            continue

        # Property type filter
        if property_type and property_type.lower() not in prop.get("type", "").lower():
            continue

        # Developer filter
        if developer and developer.lower() not in prop.get("developer", "").lower():
            continue

        # Compound filter
        if compound and compound.lower() not in prop.get("compound", "").lower():
            continue

        results.append(prop)

        if len(results) >= limit:
            break

    return results


def get_properties_by_location(location: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Get properties in a specific location."""
    return search_properties(location=location, limit=limit)


def get_properties_by_budget(min_budget: int, max_budget: int, limit: int = 20) -> List[Dict[str, Any]]:
    """Get properties within a budget range."""
    return search_properties(min_price=min_budget, max_price=max_budget, limit=limit)


def get_market_stats() -> Dict[str, Any]:
    """Get market statistics."""
    metadata = get_metadata()
    return metadata.get("marketStats", {
        "averagePricePerSqm": 45000,
        "hotLocations": ["New Cairo", "Sheikh Zayed", "6th October"]
    })


def format_property_for_ai(prop: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a property object for AI response.
    Ensures consistent field names for the frontend.
    """
    payment = prop.get("paymentPlan", {})

    return {
        "id": prop.get("id"),
        "title": prop.get("title"),
        "type": prop.get("type"),
        "location": prop.get("location"),
        "compound": prop.get("compound"),
        "developer": prop.get("developer"),
        "price": prop.get("price"),
        "price_per_sqm": prop.get("pricePerSqm"),
        "size_sqm": prop.get("area") or prop.get("size") or prop.get("sqm"),
        "bedrooms": prop.get("bedrooms"),
        "bathrooms": prop.get("bathrooms"),
        "delivery_date": prop.get("deliveryDate"),
        "down_payment": payment.get("downPayment"),
        "installment_years": payment.get("installmentYears"),
        "monthly_installment": payment.get("monthlyInstallment"),
        "image_url": prop.get("image"),
        "nawy_url": prop.get("nawyUrl"),
        "sale_type": prop.get("saleType"),
        "description": prop.get("description"),
    }


# Export functions
__all__ = [
    "load_property_data",
    "get_all_properties",
    "get_metadata",
    "search_properties",
    "get_properties_by_location",
    "get_properties_by_budget",
    "get_market_stats",
    "format_property_for_ai"
]
