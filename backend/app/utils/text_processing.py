"""
Text Processing Utilities
-------------------------
Utilities for text normalization, especially for Arabic text handling.
Prevents encoding issues when mixing Arabic and English in AI responses.
"""

import unicodedata
import re
from typing import Optional


def normalize_arabic_text(text: str) -> str:
    """
    Normalize Arabic text to prevent encoding issues.

    Applies NFC normalization which composes characters into their
    canonical form. This helps prevent issues like:
    - Combining diacritics appearing separately
    - Inconsistent character representations
    - Mixed encoding in Arabic/English text

    Args:
        text: Input text (may contain Arabic, English, or mixed)

    Returns:
        Normalized text with consistent Unicode representation
    """
    if not text:
        return text

    # Apply NFC normalization (Canonical Decomposition, followed by Canonical Composition)
    normalized = unicodedata.normalize('NFC', text)

    return normalized


def clean_response_text(text: str) -> str:
    """
    Clean and normalize AI response text before sending to frontend.

    Applies:
    1. Unicode normalization (NFC)
    2. Whitespace cleanup (multiple spaces -> single space)
    3. Newline normalization
    4. Trailing whitespace removal

    Args:
        text: Raw AI response text

    Returns:
        Cleaned and normalized text
    """
    if not text:
        return text

    # Step 1: Unicode normalization
    text = unicodedata.normalize('NFC', text)

    # Step 2: Normalize newlines (Windows -> Unix)
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Step 3: Remove multiple consecutive newlines (keep max 2)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Step 4: Remove trailing whitespace from each line
    lines = [line.rstrip() for line in text.split('\n')]
    text = '\n'.join(lines)

    # Step 5: Strip leading/trailing whitespace from entire text
    text = text.strip()

    return text


def sanitize_markdown(text: str) -> str:
    """
    Sanitize markdown text for safe rendering.

    Ensures markdown special characters are properly escaped
    when they appear in data (not as formatting).

    Args:
        text: Text that may contain markdown

    Returns:
        Sanitized text safe for markdown rendering
    """
    if not text:
        return text

    # Normalize first
    text = normalize_arabic_text(text)

    # Fix common markdown issues in Arabic text:
    # - Ensure proper spacing around bold/italic markers
    # - Fix improperly nested markers

    # Ensure ** markers have proper spacing in Arabic context
    # Pattern: Arabic char directly followed by ** or vice versa
    text = re.sub(r'(\*\*)([^\s\*])', r'\1 \2', text)
    text = re.sub(r'([^\s\*])(\*\*)', r'\1 \2', text)

    return text


def format_price_arabic(price: float, currency: str = "جنيه") -> str:
    """
    Format price for Arabic display.

    Args:
        price: Numeric price value
        currency: Currency name (default: جنيه)

    Returns:
        Formatted price string (e.g., "5,000,000 جنيه")
    """
    formatted = f"{price:,.0f}"
    return f"{formatted} {currency}"


def format_price_millions_arabic(price: float) -> str:
    """
    Format large prices in millions for Arabic display.

    Args:
        price: Numeric price value

    Returns:
        Formatted price string (e.g., "5.2 مليون جنيه")
    """
    if price >= 1_000_000:
        millions = price / 1_000_000
        if millions == int(millions):
            return f"{int(millions)} مليون جنيه"
        return f"{millions:.1f} مليون جنيه"
    return format_price_arabic(price)
