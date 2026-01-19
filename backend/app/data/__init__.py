"""
Osool Data Module
-----------------
Contains real property data from data.js for the AI agent.
NO MOCK DATA - Only real market data from nawy.com scraping.
"""

# Primary data source - real property data from data.js
from .property_data_loader import (
    load_property_data,
    get_all_properties,
    get_metadata,
    search_properties,
    get_properties_by_location,
    get_properties_by_budget,
    get_market_stats,
    format_property_for_ai
)

# Legacy imports for backward compatibility
from .new_cairo_properties import (
    CLASS_A_DEVELOPERS,
)

__all__ = [
    # Primary data functions (use these)
    "load_property_data",
    "get_all_properties",
    "get_metadata",
    "search_properties",
    "get_properties_by_location",
    "get_properties_by_budget",
    "get_market_stats",
    "format_property_for_ai",
    # Developer classification
    "CLASS_A_DEVELOPERS",
]
