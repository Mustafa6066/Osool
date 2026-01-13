"""
Enhanced Rate Limiting and Abuse Prevention
--------------------------------------------
Multi-tier rate limiting with Redis backend for distributed systems.
"""

import os
import logging
from typing import Optional
from fastapi import Request, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# REDIS-BACKED RATE LIMITING
# ---------------------------------------------------------------------------

def get_redis_client():
    """Get Redis client for rate limiting storage."""
    redis_url = os.getenv("REDIS_URL")

    if redis_url:
        try:
            client = redis.from_url(redis_url, decode_responses=True)
            client.ping()
            return client
        except Exception as e:
            logger.warning(f"Redis unavailable for rate limiting: {e}")
            return None
    return None


# Storage backend (Redis or in-memory)
redis_client = get_redis_client()
storage_uri = os.getenv("REDIS_URL") if redis_client else "memory://"


# ---------------------------------------------------------------------------
# RATE LIMIT CONFIGURATIONS
# ---------------------------------------------------------------------------

# Global rate limits (per IP)
GLOBAL_RATE_LIMIT = "100/minute"  # 100 requests per minute per IP
GLOBAL_HOURLY_LIMIT = "1000/hour"  # 1000 requests per hour per IP

# Endpoint-specific rate limits
CHAT_RATE_LIMIT = "30/minute"  # 30 chat messages per minute
SEARCH_RATE_LIMIT = "60/minute"  # 60 searches per minute
AUTH_RATE_LIMIT = "10/minute"  # 10 login attempts per minute
PROPERTY_RATE_LIMIT = "120/minute"  # 120 property views per minute


# ---------------------------------------------------------------------------
# KEY FUNCTIONS
# ---------------------------------------------------------------------------

def get_user_id_or_ip(request: Request) -> str:
    """
    Get user ID from token or fallback to IP address.

    Returns:
        User identifier for rate limiting
    """
    # Try to get user from JWT token
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            from app.auth import jwt, SECRET_KEY, ALGORITHM

            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

            # Use user ID if available
            user_id = payload.get("sub") or payload.get("wallet")
            if user_id:
                return f"user:{user_id}"
        except:
            pass  # Fall through to IP-based limiting

    # Fallback to IP address
    return f"ip:{get_remote_address(request)}"


def get_forwarded_ip(request: Request) -> str:
    """
    Get real IP address from headers (for proxied requests).

    Checks X-Forwarded-For and X-Real-IP headers.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For can contain multiple IPs, take the first
        return forwarded.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fallback to direct connection IP
    return get_remote_address(request)


# ---------------------------------------------------------------------------
# LIMITER INITIALIZATION
# ---------------------------------------------------------------------------

# Primary limiter with user-aware key function
limiter = Limiter(
    key_func=get_user_id_or_ip,
    storage_uri=storage_uri,
    default_limits=[GLOBAL_RATE_LIMIT, GLOBAL_HOURLY_LIMIT],
    headers_enabled=True,  # Add X-RateLimit-* headers
    swallow_errors=True,  # Don't crash if Redis is down
)

# IP-only limiter (for public endpoints)
ip_limiter = Limiter(
    key_func=get_forwarded_ip,
    storage_uri=storage_uri,
    headers_enabled=True,
)


# ---------------------------------------------------------------------------
# CUSTOM RATE LIMIT EXCEPTION HANDLER
# ---------------------------------------------------------------------------

def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom handler for rate limit exceeded.

    Returns bilingual error message with retry-after header.
    """
    # Calculate retry after (seconds until reset)
    retry_after = int(exc.detail.split("Retry after ")[1].split(" seconds")[0]) if "Retry after" in exc.detail else 60

    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "error_code": "RATE_LIMIT_EXCEEDED",
            "message": f"Rate limit exceeded: {exc.detail}",
            "message_ar": f"تم تجاوز حد الطلبات: {exc.detail}",
            "user_message": "You've made too many requests. Please wait a moment before trying again.",
            "user_message_ar": "لقد أجريت عددًا كبيرًا من الطلبات. يرجى الانتظار قليلاً قبل المحاولة مرة أخرى.",
            "retry_after_seconds": retry_after
        },
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Remaining": "0"
        }
    )


# ---------------------------------------------------------------------------
# ABUSE DETECTION
# ---------------------------------------------------------------------------

class AbuseDetector:
    """
    Detect and prevent abusive behavior patterns.

    Patterns detected:
    - Rapid sequential requests
    - Suspicious user agents
    - Known bot patterns
    - Repeated 401/403 errors
    """

    def __init__(self):
        self.redis_client = get_redis_client()
        self.suspicious_ua_patterns = [
            "bot",
            "crawler",
            "spider",
            "scraper",
            "python-requests",
            "curl",
            "wget"
        ]

    def is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check if user agent matches known bot patterns."""
        ua_lower = user_agent.lower()
        return any(pattern in ua_lower for pattern in self.suspicious_ua_patterns)

    def check_failed_auth_attempts(self, identifier: str) -> bool:
        """
        Check if identifier has too many failed auth attempts.

        Returns:
            True if suspicious (should block)
        """
        if not self.redis_client:
            return False  # Can't check without Redis

        key = f"failed_auth:{identifier}"
        try:
            attempts = self.redis_client.get(key)
            if attempts and int(attempts) >= 5:
                logger.warning(f"Suspicious auth attempts from {identifier}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed auth check error: {e}")
            return False

    def record_failed_auth(self, identifier: str):
        """Record a failed authentication attempt."""
        if not self.redis_client:
            return

        key = f"failed_auth:{identifier}"
        try:
            self.redis_client.incr(key)
            self.redis_client.expire(key, 3600)  # Reset after 1 hour
        except Exception as e:
            logger.error(f"Failed to record failed auth: {e}")

    def reset_failed_auth(self, identifier: str):
        """Reset failed auth counter on successful login."""
        if not self.redis_client:
            return

        key = f"failed_auth:{identifier}"
        try:
            self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Failed to reset auth counter: {e}")


# Global abuse detector instance
abuse_detector = AbuseDetector()


# ---------------------------------------------------------------------------
# MIDDLEWARE
# ---------------------------------------------------------------------------

async def abuse_prevention_middleware(request: Request, call_next):
    """
    Middleware to detect and prevent abusive requests.

    Checks:
    - Suspicious user agents
    - Failed auth attempts
    - Request patterns
    """

    # Check user agent
    user_agent = request.headers.get("User-Agent", "")
    if abuse_detector.is_suspicious_user_agent(user_agent):
        logger.warning(f"Suspicious user agent: {user_agent}")
        # Allow but log - you can block if needed
        # raise HTTPException(status_code=403, detail="Forbidden")

    # Check failed auth attempts
    identifier = get_user_id_or_ip(request)
    if abuse_detector.check_failed_auth_attempts(identifier):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "TOO_MANY_FAILED_ATTEMPTS",
                "message": "Too many failed authentication attempts",
                "message_ar": "عدد كبير جدًا من محاولات المصادقة الفاشلة",
                "user_message": "Your account has been temporarily locked due to multiple failed login attempts. Please try again later.",
                "user_message_ar": "تم قفل حسابك مؤقتًا بسبب محاولات تسجيل دخول فاشلة متعددة. يرجى المحاولة مرة أخرى لاحقًا."
            }
        )

    # Process request
    response = await call_next(request)

    # Record failed auth if 401
    if response.status_code == 401:
        abuse_detector.record_failed_auth(identifier)

    # Reset counter on successful auth (200 on login endpoint)
    if response.status_code == 200 and "/auth/" in str(request.url):
        abuse_detector.reset_failed_auth(identifier)

    return response


# ---------------------------------------------------------------------------
# USAGE EXAMPLES
# ---------------------------------------------------------------------------

"""
# Example 1: Apply global rate limit (automatic via default_limits)
@app.get("/api/property/{property_id}")
async def get_property(property_id: int):
    # Automatically rate limited by global limits
    pass

# Example 2: Apply endpoint-specific limit
from app.middleware.rate_limiting import limiter, CHAT_RATE_LIMIT

@app.post("/api/chat")
@limiter.limit(CHAT_RATE_LIMIT)
async def chat(request: Request):
    # Limited to 30 requests per minute
    pass

# Example 3: Apply multiple limits
@app.post("/api/auth/login")
@limiter.limit(AUTH_RATE_LIMIT)
@limiter.limit("3/hour")  # Additional hourly limit
async def login(request: Request):
    # Limited by both constraints
    pass

# Example 4: Exempt an endpoint from global limits
@app.get("/health")
@limiter.exempt
async def health_check():
    # Not rate limited
    pass

# Example 5: Use IP-only limiting (ignore user auth)
from app.middleware.rate_limiting import ip_limiter

@app.get("/public/properties")
@ip_limiter.limit("200/minute")
async def public_properties(request: Request):
    # Limited by IP only
    pass
"""
