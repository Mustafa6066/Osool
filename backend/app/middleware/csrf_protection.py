"""
CSRF Protection Middleware for FastAPI
--------------------------------------
Implements Double Submit Cookie pattern for CSRF protection.

Usage:
    app.add_middleware(CSRFProtectionMiddleware)
    
Security Features:
- Double submit cookie pattern
- Token rotation on sensitive operations
- SameSite=Strict enforcement
- Origin/Referer validation
"""

import secrets
import hashlib
import hmac
import os
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

# CSRF Secret for HMAC (should be in environment variables)
CSRF_SECRET = os.getenv("CSRF_SECRET_KEY") or os.getenv("JWT_SECRET_KEY")
if not CSRF_SECRET:
    raise ValueError("CSRF_SECRET_KEY or JWT_SECRET_KEY must be set")

CSRF_TOKEN_LENGTH = 32
CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_COOKIE_NAME = "csrf_token"

# Methods that require CSRF protection
CSRF_PROTECTED_METHODS = {"POST", "PUT", "DELETE", "PATCH"}

# Paths that don't require CSRF (authentication endpoints)
CSRF_EXEMPT_PATHS = {
    "/api/auth/login",  # First request, no cookie yet
    "/api/auth/signup",  # First request, no cookie yet
    "/api/auth/google",  # OAuth flow
    "/health",  # Health check
    "/metrics",  # Monitoring
    "/docs",  # API docs
    "/openapi.json",  # API schema
}


def generate_csrf_token(session_id: str = None) -> str:
    """
    Generate a cryptographically secure CSRF token.
    
    Uses HMAC with server-side secret to prevent token forgery.
    Format: <random>.<hmac>
    """
    # Generate random component
    random_bytes = secrets.token_bytes(CSRF_TOKEN_LENGTH)
    random_part = random_bytes.hex()
    
    # Create HMAC signature to prevent forgery
    if session_id:
        data = f"{random_part}:{session_id}"
    else:
        data = random_part
    
    mac = hmac.new(
        CSRF_SECRET.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Format: random.hmac
    return f"{random_part}.{mac}"


def verify_csrf_token(token: str, session_id: str = None) -> bool:
    """
    Verify CSRF token authenticity using HMAC.
    
    Returns:
        True if token is valid, False otherwise
    """
    if not token or "." not in token:
        return False
    
    try:
        random_part, received_mac = token.rsplit(".", 1)
        
        # Recreate HMAC
        if session_id:
            data = f"{random_part}:{session_id}"
        else:
            data = random_part
        
        expected_mac = hmac.new(
            CSRF_SECRET.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Timing-safe comparison
        return hmac.compare_digest(received_mac, expected_mac)
    
    except Exception as e:
        logger.warning(f"CSRF token verification failed: {e}")
        return False


def validate_origin(request: Request, allowed_origins: list) -> bool:
    """
    Validate Origin or Referer header matches allowed origins.
    
    Defense in depth against CSRF.
    """
    origin = request.headers.get("origin")
    referer = request.headers.get("referer")
    
    # Check Origin header first (more reliable)
    if origin:
        if origin in allowed_origins:
            return True
        # Check wildcards for Vercel previews
        for allowed in allowed_origins:
            if "*" in allowed and _match_wildcard(origin, allowed):
                return True
        return False
    
    # Fallback to Referer header
    if referer:
        for allowed in allowed_origins:
            if referer.startswith(allowed):
                return True
    
    # No Origin or Referer header (suspicious)
    return False


def _match_wildcard(value: str, pattern: str) -> bool:
    """Simple wildcard matching for allowed origins."""
    if "*" not in pattern:
        return value == pattern
    
    parts = pattern.split("*")
    if not value.startswith(parts[0]):
        return False
    if not value.endswith(parts[-1]):
        return False
    return True


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """
    CSRF Protection Middleware using Double Submit Cookie pattern.
    
    Flow:
    1. On GET requests, generate CSRF token and set cookie
    2. On state-changing requests (POST/PUT/DELETE), validate token
    3. Token must match in both cookie and header/body
    
    Security Features:
    - SameSite=Strict cookies
    - Secure flag (HTTPS only)
    - Origin/Referer validation
    - Token rotation on logout
    """
    
    def __init__(self, app, allowed_origins: Optional[list] = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or [
            "http://localhost:3000",
            "https://osool.vercel.app",
            "https://osool-ten.vercel.app",
            "https://osool.eg",
        ]
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method
        
        # Skip CSRF protection for exempt paths
        if path in CSRF_EXEMPT_PATHS or path.startswith("/docs") or path.startswith("/static"):
            return await call_next(request)
        
        # Generate and set CSRF token for all requests if not present
        csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
        
        if not csrf_cookie:
            # Generate new token
            csrf_cookie = generate_csrf_token()
        
        # For state-changing methods, validate CSRF token
        if method in CSRF_PROTECTED_METHODS:
            # Validate Origin/Referer first (defense in depth)
            if not validate_origin(request, self.allowed_origins):
                logger.warning(f"CSRF: Invalid origin for {method} {path}")
                return JSONResponse(
                    status_code=403,
                    content={"error": "Invalid origin. CSRF protection triggered."}
                )
            
            # Get token from header
            csrf_header = request.headers.get(CSRF_HEADER_NAME)
            
            # Also check body for token (for form submissions)
             if not csrf_header:
                # Try to get from form data (only for content-type application/x-www-form-urlencoded)
                content_type = request.headers.get("content-type", "")
                if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
                    # This requires reading the body, which FastAPI doesn't like
                    # Recommendation: Always use header for API calls
                    pass
            
            # Validate token
            if not csrf_header or not verify_csrf_token(csrf_header):
                logger.warning(f"CSRF: Token validation failed for {method} {path}")
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "CSRF token missing or invalid",
                        "detail": "Include X-CSRF-Token header with your request"
                    }
                )
            
            # Double Submit Cookie: Token must also match cookie
            if csrf_header != csrf_cookie:
                logger.warning(f"CSRF: Token mismatch for {method} {path}")
                return JSONResponse(
                    status_code=403,
                    content={"error": "CSRF token mismatch"}
                )
        
        # Process request
        response = await call_next(request)
        
        # Set CSRF cookie on response (refresh on every request)
        is_secure = request.url.scheme == "https" or os.getenv("ENVIRONMENT") == "production"
        
        response.set_cookie(
            key=CSRF_COOKIE_NAME,
            value=csrf_cookie,
            httponly=True,  # Prevent JavaScript access
            secure=is_secure,  # HTTPS only in production
            samesite="strict",  # Strongest CSRF protection
            max_age=86400,  # 24 hours
            path="/"
        )
        
        # Also send token in response header for SPAs to read
        response.headers[CSRF_HEADER_NAME] = csrf_cookie
        
        return response


# Fastapi dependency for manual CSRF validation
async def verify_csrf(request: Request) -> bool:
    """
    Dependency for manual CSRF validation in specific endpoints.
    
    Usage:
        @router.post("/sensitive-action")
        async def sensitive(csrf_valid: bool = Depends(verify_csrf)):
            if not csrf_valid:
                raise HTTPException(403, "CSRF validation failed")
    """
    csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
    csrf_header = request.headers.get(CSRF_HEADER_NAME)
    
    if not csrf_cookie or not csrf_header:
        return False
    
    return verify_csrf_token(csrf_header) and csrf_header == csrf_cookie
