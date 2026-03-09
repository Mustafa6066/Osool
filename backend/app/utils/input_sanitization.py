"""
Input Sanitization Utilities
-----------------------------
SECURITY FIX V5: Prevent XSS and injection attacks.

Provides HTML sanitization, email validation, phone validation.
"""

import re
import bleach
from typing import Optional


def sanitize_html(text: str) -> str:
    """
    Remove all HTML tags from user input to prevent XSS attacks.
    
    SECURITY: Strip ALL tags - users should not be able to inject HTML.
    
    Args:
        text: User-provided text that may contain HTML
        
    Returns:
        Cleaned text with all HTML tags removed
        
    Example:
        >>> sanitize_html("<script>alert(1)</script>Hello")
        "Hello"
    """
    return bleach.clean(
        text,
        tags=[],  # Allow NO tags
        strip=True  # Strip tags instead of escaping
    )


def sanitize_user_message(message: str) -> str:
    """
    Sanitize chat messages from users.
    
    - Removes HTML tags
    - Preserves Arabic, English, numbers, common punctuation
    - Removes dangerous characters
    
    Args:
        message: User chat message
        
    Returns:
        Sanitized message safe for storage and display
    """
    # Step 1: Remove HTML tags
    cleaned = sanitize_html(message)
    
    # Step 2: Remove null bytes and control characters (except newline/tab)
    cleaned = ''.join(char for char in cleaned if ord(char) >= 32 or char in '\n\t')
    
    return cleaned.strip()


def validate_egyptian_phone(phone: str) -> bool:
    """
    SECURITY FIX V10: Validate Egyptian phone numbers in E.164 format.
    
    Valid formats:
    - +201XXXXXXXXX (mobile: 01x + 8 digits)
    
    Operators:
    - 010: Vodafone
    - 011: Etisalat
    - 012: Orange
    - 015: WE (We)
    
    Args:
        phone: Phone number string
        
    Returns:
        True if valid Egyptian mobile number
        
    Example:
        >>> validate_egyptian_phone("+201012345678")
        True
        >>> validate_egyptian_phone("+20")
        False
    """
    # +20 followed by (10|11|12|15) followed by exactly 8 digits
    pattern = r'^\+20(1[0125])\d{8}$'
    return bool(re.match(pattern, phone))


def validate_email_format(email: str) -> bool:
    """
    Basic email format validation.
    
    Args:
        email: Email address string
        
    Returns:
        True if email format is valid
    """
    # Simple regex for basic email validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def sanitize_property_data(title: str, description: Optional[str] = None) -> tuple[str, Optional[str]]:
    """
    Sanitize property listing data.
    
    Args:
        title: Property title
        description: Optional property description
        
    Returns:
        Tuple of (sanitized_title, sanitized_description)
    """
    clean_title = sanitize_html(title)
    clean_description = sanitize_html(description) if description else None
    
    return (clean_title, clean_description)


def redact_email_for_logging(email: str) -> str:
    """
    SECURITY FIX V13: Redact email addresses in logs to protect PII.
    
    Args:
        email: Email address
        
    Returns:
        Redacted email (e.g., "u***@e***.com")
        
    Example:
        >>> redact_email_for_logging("mustafa@osool.eg")
        "m*****@o***.eg"
    """
    if '@' not in email:
        return "***"
    
    user, domain = email.split('@', 1)
    
    # Redact username: show first char only
    redacted_user = f"{user[0]}{'*' * (len(user) - 1)}" if len(user) > 0 else "***"
    
    # Redact domain: show first char of each part
    domain_parts = domain.split('.')
    redacted_domain = '.'.join(
        f"{part[0]}{'*' * (len(part) - 1)}" if len(part) > 0 else "***"
        for part in domain_parts
    )
    
    return f"{redacted_user}@{redacted_domain}"
