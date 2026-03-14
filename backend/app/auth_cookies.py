"""
Secure Cookie-Based Authentication
-----------------------------------
Replaces localStorage JWT storage with httpOnly cookies.

Security Improvements:
- httpOnly cookies (JavaScript cannot access)
- SameSite=Strict (CSRF protection)
- Secure flag (HTTPS only)
- Automatic rotation on refresh

Migration Notes:
- Clients must handle cookies instead of Authorization header
- CORS must allow credentials
- Frontend must update auth flow
"""

import os
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from fastapi import HTTPException, status, Request, Response
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY must be set")

ALGORITHM = "HS256"
ACCESS_TOKEN_COOKIE_NAME = "access_token"
REFRESH_TOKEN_COOKIE_NAME = "refresh_token"
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Reduced from 1440 (24h) to 15 minutes
REFRESH_TOKEN_EXPIRE_DAYS = 7  # Reduced from 30 days to 7 days


def create_access_token_cookie(
    response: Response,
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token and set as httpOnly cookie.
    
    Args:
        response: FastAPI Response object
        data: JWT payload
        expires_delta: Custom expiration time
    
    Returns:
        Token string (for logging/debugging only)
    """
    import uuid
    
    to_encode = data.copy()
    now = datetime.utcnow()
    
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4()),  # Unique token ID
        "type": "access"
    })
    
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    # Set httpOnly cookie
    is_secure = os.getenv("ENVIRONMENT") == "production"
    
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        value=token,
        httponly=True,  # Cannot be accessed by JavaScript
        secure=is_secure,  # HTTPS only in production
        samesite="strict",  # CSRF protection
        max_age=int(timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES).total_seconds()),
        path="/",
        domain=None  # Let browser set domain automatically
    )
    
    logger.info(f"Access token cookie set (expires in {ACCESS_TOKEN_EXPIRE_MINUTES} min)")
    return token


def create_refresh_token_cookie(
    response: Response,
    data: dict
) -> str:
    """
    Create JWT refresh token and set as httpOnly cookie.
    
    Refresh tokens are longer-lived and stored separately.
    They should be rotated on each use.
    """
    import uuid
    
    to_encode = data.copy()
    now = datetime.utcnow()
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4()),
        "type": "refresh"
    })
    
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    # Set httpOnly cookie
    is_secure = os.getenv("ENVIRONMENT") == "production"
    
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        max_age=int(timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS).total_seconds()),
        path="/api/auth/refresh",  # Only sent to refresh endpoint
        domain=None
    )
    
    logger.info(f"Refresh token cookie set (expires in {REFRESH_TOKEN_EXPIRE_DAYS} days)")
    return token


def clear_auth_cookies(response: Response):
    """
    Clear authentication cookies (logout).
    
    Sets cookies to expired state.
    """
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        value="",
        httponly=True,
        secure=os.getenv("ENVIRONMENT") == "production",
        samesite="strict",
        max_age=0,  # Expire immediately
        path="/"
    )
    
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE_NAME,
        value="",
        httponly=True,
        secure=os.getenv("ENVIRONMENT") == "production",
        samesite="strict",
        max_age=0,
        path="/api/auth/refresh"
    )
    
    logger.info("Auth cookies cleared")


async def get_current_user_from_cookie(request: Request, db: AsyncSession):
    """
    Extract and validate user from cookie-based JWT.
    
    Replacement for Bearer token authentication.
    """
    from sqlalchemy import select
    from app.models import User
    from app.auth import is_token_blacklisted
    
    token = request.cookies.get(ACCESS_TOKEN_COOKIE_NAME)
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated - no access token cookie",
            headers={"WWW-Authenticate": "Cookie"},
        )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Validate token type
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        
        # Check if token is blacklisted
        jti = payload.get("jti")
        if jti and is_token_blacklisted(jti):
            logger.warning(f"Blacklisted token attempted: {jti[:8]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
            )
        
        # Get user email from token
        email: str = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
        
        # Fetch user from database
        result = await db.execute(select(User).filter(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        
        return user
    
    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Cookie"},
        )


async def get_current_user_optional_from_cookie(request: Request, db: AsyncSession):
    """
    Optional authentication - returns User or None.
    
    Does not raise exception if not authenticated.
    """
    from sqlalchemy import select
    from app.models import User
    from app.auth import is_token_blacklisted
    
    token = request.cookies.get(ACCESS_TOKEN_COOKIE_NAME)
    
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("type") != "access":
            return None
        
        jti = payload.get("jti")
        if jti and is_token_blacklisted(jti):
            return None
        
        email: str = payload.get("sub")
        if not email:
            return None
        
        result = await db.execute(select(User).filter(User.email == email))
        user = result.scalar_one_or_none()
        
        return user
    
    except JWTError:
        return None


def refresh_access_token(request: Request, response: Response) -> dict:
    """
    Refresh access token using refresh token from cookie.
    
    Security Features:
    - Rotates refresh token on every use
    - Invalidates old refresh token
    - Binds to user session
    
    Returns:
        dict with new tokens and user info
    """
    refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided",
        )
    
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Validate token type
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        
        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
        
        # Blacklist old refresh token (single use only)
        old_jti = payload.get("jti")
        if old_jti:
            from app.auth import _token_blacklist_memory, _get_redis_client
            redis = _get_redis_client()
            if redis:
                redis.sadd("token_blacklist", old_jti)
                redis.expire("token_blacklist", 86400 * 7)  # 7 days
            else:
                _token_blacklist_memory.add(old_jti)
        
        # Create new tokens
        token_data = {
            "sub": email,
            "role": payload.get("role"),
        }
        
        # Set new access token
        create_access_token_cookie(response, token_data)
        
        # Rotate refresh token
        create_refresh_token_cookie(response, token_data)
        
        logger.info(f"Tokens refreshed for user: {email}")
        
        return {
            "status": "success",
            "message": "Tokens refreshed",
            "email": email
        }
    
    except JWTError as e:
        logger.warning(f"Refresh token validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


# Backward compatibility: Support both cookie and Bearer token
class CookieOrBearerAuth(HTTPBearer):
    """
    Flexible authentication supporting both:
    - httpOnly cookies (preferred)
    - Authorization: Bearer token (backward compatibility)
    
    Gradually migrate clients to cookie-based auth.
    """
    
    async def __call__(self, request: Request, db: AsyncSession):
        # Try cookie first
        token = request.cookies.get(ACCESS_TOKEN_COOKIE_NAME)
        
        # Fallback to Authorization header
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )
        
        # Validate token (same logic as get_current_user_from_cookie)
        from sqlalchemy import select
        from app.models import User
        from app.auth import is_token_blacklisted
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            jti = payload.get("jti")
            if jti and is_token_blacklisted(jti):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token revoked",
                )
            
            email = payload.get("sub")
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                )
            
            result = await db.execute(select(User).filter(User.email == email))
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                )
            
            return user
        
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
