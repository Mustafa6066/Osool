"""
Safe Parsers — Null-tolerant type coercions for raw market feed data.

Commercial and specialized property segments (Offices, Retail, Clinics) routinely
carry NaN for residential fields (beds, baths) and blank payment columns.
These helpers prevent pipeline crashes from implicit int/float casts on NaN.
"""

import math
from typing import Any, Optional


def clean_int(value: Any) -> Optional[int]:
    """Safely coerces mixed pandas text or float types to integer structures."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def clean_float(value: Any) -> Optional[float]:
    """Converts unstructured payload text fields safely into floats."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def clean_str(value: Any, default: Optional[str] = None) -> Optional[str]:
    """Normalizes missing spatial references or text values."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return default
    text = str(value).strip()
    return text if text else default
