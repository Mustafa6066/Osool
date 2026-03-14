"""Market Analysis Tool."""
from typing import Any, Dict


async def analyze_market_trends(
    location: str,
    property_type: str = "apartment",
    timeframe: str = "1year",
) -> Dict[str, Any]:
    """Return market trend data for a location."""
    # Stub data — replace with real DB queries in production
    trends = [
        {"month": "Jan 2024", "avg_price": 4800000, "transactions": 45},
        {"month": "Feb 2024", "avg_price": 4900000, "transactions": 52},
        {"month": "Mar 2024", "avg_price": 5050000, "transactions": 61},
        {"month": "Apr 2024", "avg_price": 5100000, "transactions": 58},
    ]

    # Demand heuristic
    avg_change = 6.25  # % over timeframe
    if avg_change >= 8:
        demand = "HIGH"
    elif avg_change >= 3:
        demand = "MEDIUM"
    else:
        demand = "LOW"

    return {
        "status": "success",
        "location": location,
        "property_type": property_type,
        "timeframe": timeframe,
        "trends": trends,
        "average_price_change_percent": avg_change,
        "demand_indicator": demand,
    }
