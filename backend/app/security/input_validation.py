"""
Enhanced Input Validation and Sanitization
------------------------------------------
Comprehensive input validation for all API endpoints.

Security Features:
- Length limits on all string inputs
- HTML/SQL injection prevention
- XSS sanitization
- Allow-lists for enumerated values
- Phone number validation
- Email sanitization
- Path traversal prevention
"""

import re
import html
from typing import Optional, Any
from pydantic import BaseModel, validator, Field, EmailStr
from fastapi import HTTPException


# ═══════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════

MAX_NAME_LENGTH = 100
MAX_EMAIL_LENGTH = 255
MAX_MESSAGE_LENGTH = 5000
MAX_DESCRIPTION_LENGTH = 10000
MAX_PHONE_LENGTH = 20
MAX_ADDRESS_LENGTH = 500
MAX_NATIONAL_ID_LENGTH = 20

# Regex patterns
PHONE_PATTERN = re.compile(r'^\+?[1-9]\d{1,14}$')  # E.164 format
EGYPTIAN_PHONE_PATTERN = re.compile(r'^\+20\d{10}$')
NATIONAL_ID_PATTERN = re.compile(r'^\d{14}$')  # Egyptian NID
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# Dangerous patterns (XSS, SQL injection)
DANGEROUS_PATTERNS = [
    re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
    re.compile(r'javascript:', re.IGNORECASE),
    re.compile(r'on\w+\s*=', re.IGNORECASE),  # onclick, onerror, etc.
    re.compile(r'<iframe', re.IGNORECASE),
    re.compile(r'<object', re.IGNORECASE),
    re.compile(r'<embed', re.IGNORECASE),
    re.compile(r'<img[^>]+src\s*=\s*["\']?javascript:', re.IGNORECASE),
    # SQL injection patterns
    re.compile(r'(\';|\"--|\/\*|\*\/|xp_|sp_|exec|execute|SELECT|UNION|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)', re.IGNORECASE),
]

# Path traversal patterns
PATH_TRAVERSAL_PATTERNS = [
    re.compile(r'\.\.'),
    re.compile(r'[/\\]etc[/\\]'),
    re.compile(r'[/\\]proc[/\\]'),
    re.compile(r'[/\\]sys[/\\]'),
]


# ═══════════════════════════════════════════════════════════════
# SANITIZATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def sanitize_string(value: str, max_length: int = MAX_MESSAGE_LENGTH, allow_html: bool = False) -> str:
    """
    Sanitize string input to prevent XSS and injection attacks.
    
    Args:
        value: Input string
        max_length: Maximum allowed length
        allow_html: If False, HTML escape all content
    
    Returns:
        Sanitized string
    
    Raises:
        ValueError: If input contains dangerous patterns
    """
    if not value:
        return value
    
    # Length check
    if len(value) > max_length:
        raise ValueError(f"Input too long (max {max_length} characters)")
    
    # Check for dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(value):
            raise ValueError("Input contains potentially dangerous content")
    
    # HTML escape if not allowing HTML
    if not allow_html:
        value = html.escape(value)
    
    # Normalize whitespace
    value = ' '.join(value.split())
    
    return value.strip()


def sanitize_email(email: str) -> str:
    """
    Sanitize and validate email address.
    
    Returns:
        Lowercase, trimmed email
    
    Raises:
        ValueError: If email is invalid
    """
    if not email:
        raise ValueError("Email is required")
    
    email = email.strip().lower()
    
    if len(email) > MAX_EMAIL_LENGTH:
        raise ValueError(f"Email too long (max {MAX_EMAIL_LENGTH} characters)")
    
    if not EMAIL_PATTERN.match(email):
        raise ValueError("Invalid email format")
    
    # Check for dangerous characters
    if any(char in email for char in ['<', '>', '"', "'"]):
        raise ValueError("Email contains invalid characters")
    
    return email


def sanitize_phone(phone: str, country_code: str = "EG") -> str:
    """
    Sanitize and validate phone number.
    
    Args:
        phone: Phone number
        country_code: Country code (default: Egypt)
    
    Returns:
        Standardized phone number in E.164 format
    
    Raises:
        ValueError: If phone number is invalid
    """
    if not phone:
        raise ValueError("Phone number is required")
    
    # Remove all non-digit characters except +
    phone = re.sub(r'[^\d+]', '', phone)
    
    if len(phone) > MAX_PHONE_LENGTH:
        raise ValueError(f"Phone number too long")
    
    # Country-specific validation
    if country_code == "EG":
        # Egyptian phone: +20xxxxxxxxxx (10 digits after +20)
        if not phone.startswith('+20'):
            # Try to add +20 if starts with 0
            if phone.startswith('0'):
                phone = '+20' + phone[1:]
            else:
                phone = '+20' + phone
        
        if not EGYPTIAN_PHONE_PATTERN.match(phone):
            raise ValueError("Invalid Egyptian phone number (expected: +20xxxxxxxxxx)")
    else:
        # Generic E.164 validation
        if not PHONE_PATTERN.match(phone):
            raise ValueError("Invalid phone number format")
    
    return phone


def sanitize_national_id(nid: str, country_code: str = "EG") -> str:
    """
    Sanitize and validate national ID.
    
    Args:
        nid: National ID number
        country_code: Country code
    
    Returns:
        Validated NID
    
    Raises:
        ValueError: If NID is invalid
    """
    if not nid:
        raise ValueError("National ID is required")
    
    # Remove all non-digit characters
    nid = re.sub(r'\D', '', nid)
    
    if country_code == "EG":
        # Egyptian NID: 14 digits
        if not NATIONAL_ID_PATTERN.match(nid):
            raise ValueError("Invalid Egyptian National ID (must be 14 digits)")
    
    return nid


def check_path_traversal(path: str) -> str:
    """
    Check for path traversal attempts.
    
    Raises:
        ValueError: If path contains traversal patterns
    """
    for pattern in PATH_TRAVERSAL_PATTERNS:
        if pattern.search(path):
            raise ValueError("Invalid path - path traversal detected")
    
    return path


# ═══════════════════════════════════════════════════════════════
# ENHANCED PYDANTIC MODELS WITH VALIDATION
# ═══════════════════════════════════════════════════════════════

class SecureChatRequest(BaseModel):
    """Secure chat request with validation."""
    message: str = Field(..., min_length=1, max_length=MAX_MESSAGE_LENGTH)
    session_id: str = Field(default="default", max_length=100)
    language: str = Field(default="auto", regex="^(ar|en|auto)$")
    
    @validator('message')
    def sanitize_message(cls, v):
        return sanitize_string(v, MAX_MESSAGE_LENGTH, allow_html=False)
    
    @validator('session_id')
    def sanitize_session_id(cls, v):
        # Session IDs should be alphanumeric + hyphens only
        if not re.match(r'^[a-zA-Z0-9\-_]+$', v):
            raise ValueError("Invalid session ID format")
        return v


class SecureSignupRequest(BaseModel):
    """Secure signup with comprehensive validation."""
    full_name: str = Field(..., min_length=2, max_length=MAX_NAME_LENGTH)
    email: EmailStr
    password: str = Field(..., min_length=12, max_length=128)  # Increased from 8 to 12
    phone_number: str = Field(..., min_length=10, max_length=MAX_PHONE_LENGTH)
    national_id: str = Field(..., min_length=14, max_length=MAX_NATIONAL_ID_LENGTH)
    
    @validator('full_name')
    def sanitize_name(cls, v):
        v = sanitize_string(v, MAX_NAME_LENGTH, allow_html=False)
        # Names should only contain letters, spaces, hyphens, and apostrophes
        if not re.match(r"^[a-zA-Z\s\-']+$", v):
            raise ValueError("Name contains invalid characters")
        return v
    
    @validator('email')
    def sanitize_email_field(cls, v):
        return sanitize_email(str(v))
    
    @validator('password')
    def validate_password_strength(cls, v):
        """
        Enforce strong password policy:
        - Minimum 12 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        - No common passwords
        """
        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters")
        
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not re.search(r'[0-9]', v):
            raise ValueError("Password must contain at least one digit")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")
        
        # Check against common passwords
        common_passwords = {
            'password123', '123456789', 'qwerty123', 'admin123456',
            'welcome123', 'password12345', 'letmein123'
        }
        if v.lower() in common_passwords:
            raise ValueError("Password is too common")
        
        return v
    
    @validator('phone_number')
    def sanitize_phone_field(cls, v):
        return sanitize_phone(v, country_code="EG")
    
    @validator('national_id')
    def sanitize_nid_field(cls, v):
        return sanitize_national_id(v, country_code="EG")


class SecurePropertySearch(BaseModel):
    """Secure property search request."""
    location: Optional[str] = Field(None, max_length=200)
    min_price: Optional[int] = Field(None, ge=0, le=1000000000)  # 1 billion max
    max_price: Optional[int] = Field(None, ge=0, le=1000000000)
    bedrooms: Optional[int] = Field(None, ge=0, le=20)
    property_type: Optional[str] = Field(None, regex="^(Apartment|Villa|Townhouse|Duplex|Penthouse|Studio)$")
    
    @validator('location')
    def sanitize_location(cls, v):
        if v:
            return sanitize_string(v, 200, allow_html=False)
        return v
    
    @validator('max_price')
    def validate_price_range(cls, v, values):
        if v and 'min_price' in values and values['min_price']:
            if v < values['min_price']:
                raise ValueError("max_price must be greater than min_price")
        return v


class SecureValuationRequest(BaseModel):
    """Secure valuation request."""
    location: str = Field(..., min_length=2, max_length=200)
    size_sqm: int = Field(..., ge=10, le=10000)  # 10 to 10,000 sqm
    bedrooms: int = Field(default=3, ge=0, le=20)
    finishing: str = Field(default="Fully Finished", regex="^(Core & Shell|Semi Finished|Fully Finished|Ultra Lux)$")
    property_type: str = Field(default="Apartment", regex="^(Apartment|Villa|Townhouse|Duplex|Penthouse|Studio)$")
    
    @validator('location')
    def sanitize_location_field(cls, v):
        return sanitize_string(v, 200, allow_html=False)


class SecureContractAnalysisRequest(BaseModel):
    """Secure contract analysis request."""
    text: str = Field(..., min_length=50, max_length=MAX_DESCRIPTION_LENGTH)
    language: str = Field(default="auto", regex="^(ar|en|auto)$")
    
    @validator('text')
    def sanitize_contract_text(cls, v):
        # Contract text can contain some formatting, but still sanitize
        return sanitize_string(v, MAX_DESCRIPTION_LENGTH, allow_html=False)


# ═══════════════════════════════════════════════════════════════
# VALIDATION HELPERS
# ═══════════════════════════════════════════════════════════════

def validate_pagination(page: int = 1, page_size: int = 50) -> tuple:
    """
    Validate pagination parameters.
    
    Returns:
        (offset, limit) tuple
    
    Raises:
        HTTPException: If parameters are invalid
    """
    if page < 1:
        raise HTTPException(status_code=400, detail="Page must be >= 1")
    
    if page_size < 1 or page_size > 100:
        raise HTTPException(status_code=400, detail="Page size must be between 1 and 100")
    
    offset = (page - 1) * page_size
    return offset, page_size


def validate_property_id(property_id: int) -> int:
    """
    Validate property ID.
    
    Raises:
        HTTPException: If ID is invalid
    """
    if property_id < 1 or property_id > 2147483647:  # Max int32
        raise HTTPException(status_code=400, detail="Invalid property ID")
    
    return property_id


def validate_user_id(user_id: int) -> int:
    """
    Validate user ID.
    
    Raises:
        HTTPException: If ID is invalid
    """
    if user_id < 1 or user_id > 2147483647:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    return user_id


# ═══════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════

__all__ = [
    'sanitize_string',
    'sanitize_email',
    'sanitize_phone',
    'sanitize_national_id',
    'check_path_traversal',
    'SecureChatRequest',
    'SecureSignupRequest',
    'SecurePropertySearch',
    'SecureValuationRequest',
    'SecureContractAnalysisRequest',
    'validate_pagination',
    'validate_property_id',
    'validate_user_id',
]
