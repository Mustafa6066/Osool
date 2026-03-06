"""
Osool Authentication Module
---------------------------
Handles JWT generation, password hashing, and user authentication.
Phase 2: Enhanced with Google OAuth, Email Verification, Password Reset.
Phase 4: Security hardening - no hardcoded fallbacks.
"""

import os
import httpx
import logging
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.database import get_db
from app.models import User

logger = logging.getLogger(__name__)

# Configuration - Phase 4: No fallback secrets (will raise error if not set)
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("❌ JWT_SECRET_KEY environment variable must be set for production")

# Validate secret key strength (minimum 32 characters)
if len(SECRET_KEY) < 32:
    raise ValueError(f"❌ JWT_SECRET_KEY must be at least 32 characters long for security (got {len(SECRET_KEY)} characters)")

# Security Fix H5: Reject weak dev-style secrets in production
import re as _re
if os.getenv("ENVIRONMENT") == "production" and _re.fullmatch(r'[a-z0-9\-]+', SECRET_KEY):
    raise ValueError("❌ JWT_SECRET_KEY looks like a weak dev secret. Generate with: openssl rand -hex 32")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 Hours (Phase 6: Reduced from 30 days)
REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30 Days for refresh tokens

# Token blacklist — Redis-backed for persistence across restarts
# Falls back to in-memory set if Redis is unavailable.
_token_blacklist_memory = set()

def _get_redis_client():
    """Get Redis client for token blacklist, if available."""
    try:
        from app.services.cache import cache
        if cache.redis and cache.redis.ping():
            return cache.redis
    except Exception:
        pass
    return None

# Use direct bcrypt instead of passlib for compatibility
import bcrypt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password using bcrypt directly. Handles 72-byte limit."""
    try:
        # Truncate password to 72 bytes (bcrypt limit)
        password_bytes = plain_password.encode('utf-8')[:72]
        return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))
    except Exception as e:
        logger.error(f"Password verification failed: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Hash password using bcrypt directly. Handles 72-byte limit."""
    # Truncate password to 72 bytes (bcrypt limit)
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')


async def get_current_user_optional(token: Optional[str] = Depends(oauth2_scheme_optional), db = Depends(get_db)) -> Optional[User]:
    """
    OPTIONAL authentication.
    Returns User object if token is valid, None if not provided or invalid.
    Does NOT raise 401.
    """
    if not token:
        return None
        
    try:
        from sqlalchemy import select
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        if jti and is_token_blacklisted(jti):
            return None
        username: str = payload.get("sub")
        
        if username is None:
            return None
            
        if username:
            result = await db.execute(select(User).filter(User.email == username))
            user = result.scalar_one_or_none()
        else:
            return None
            
        return user
    except JWTError:
        return None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create JWT access token with enhanced security.

    Includes:
    - Expiration time (exp)
    - Issued at time (iat)
    - JWT ID (jti) for blacklisting
    """
    import uuid

    to_encode = data.copy()
    now = datetime.utcnow()

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # Add security claims
    to_encode.update({
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4())  # Unique token ID for blacklisting
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def invalidate_token(token: str):
    """
    Add token to blacklist (logout functionality).
    Uses Redis with TTL if available, falls back to in-memory set.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")

        if jti:
            redis = _get_redis_client()
            if redis:
                # Store in Redis with 24h TTL (matching max token lifetime)
                redis.sadd("token_blacklist", jti)
                redis.expire("token_blacklist", 86400)
            else:
                _token_blacklist_memory.add(jti)
            logger.info(f"Token {jti[:8]}... invalidated")
            return True
        return False
    except JWTError as e:
        logger.warning(f"Failed to invalidate token: {e}")
        return False


def is_token_blacklisted(jti: str) -> bool:
    """
    Check if token is blacklisted.
    Checks Redis first, falls back to in-memory set.
    """
    redis = _get_redis_client()
    if redis:
        return redis.sismember("token_blacklist", jti)
    return jti in _token_blacklist_memory



async def get_current_user(token: str = Depends(oauth2_scheme), db = Depends(get_db)):
    from sqlalchemy import select
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Check if token is blacklisted
        jti = payload.get("jti")
        if jti and is_token_blacklisted(jti):
            logger.warning(f"Blacklisted token attempted: {jti[:8]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

        username: str = payload.get("sub")

        if username is None:
            raise credentials_exception

        token_data = {"sub": username}
    except JWTError:
        raise credentials_exception
        
    # Find user by email
    result = await db.execute(select(User).filter(User.email == token_data["sub"]))
    user = result.scalar_one_or_none()
        
    if user is None:
        raise credentials_exception
    return user



# ═══════════════════════════════════════════════════════════════
# GOOGLE OAUTH (Phase 2)
# ═══════════════════════════════════════════════════════════════

async def verify_google_token(id_token: str) -> dict:
    """
    Verify Google ID token and extract user info.

    Args:
        id_token: Google ID token from OAuth flow

    Returns:
        Dictionary with user info: {email, name, picture}

    Raises:
        HTTPException if token is invalid
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Google token"
                )

            user_info = response.json()

            # Security Fix L2: Require GOOGLE_CLIENT_ID (fail if not configured)
            expected_client_id = os.getenv('GOOGLE_CLIENT_ID')
            if not expected_client_id:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Google OAuth is not properly configured"
                )
            if user_info.get('aud') != expected_client_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Token not issued for this application"
                )

            return {
                'email': user_info.get('email'),
                'name': user_info.get('name', 'Google User'),
                'picture': user_info.get('picture'),
                'email_verified': user_info.get('email_verified', False)
            }

    except httpx.RequestError as e:
        logger.error(f"Google token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not verify Google token"
        )


def get_or_create_user_by_email(db: Session, email: str, full_name: str) -> User:
    """
    Get existing user by email or create new one.
    Used for Google OAuth and email signup.

    Args:
        db: Database session
        email: User email address
        full_name: User's full name

    Returns:
        User object
    """
    user = db.query(User).filter(User.email == email).first()

    if not user:
        user = User(
            email=email,
            full_name=full_name,
            email_verified=True,  # Google/OAuth users are pre-verified
            is_verified=True,
            role='investor'
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info(f"Created new user via email: {email}")

    return user


async def get_or_create_user_by_email_async(db: AsyncSession, email: str, full_name: str) -> User:
    """
    Async version of get_or_create_user_by_email for AsyncSession.
    """
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            email=email,
            full_name=full_name,
            email_verified=True,
            is_verified=True,
            role='investor'
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info(f"Created new user via email (async): {email}")

    return user


# ═══════════════════════════════════════════════════════════════
# REFRESH TOKEN SYSTEM (Phase 6)
# ═══════════════════════════════════════════════════════════════

import secrets
import hashlib
from datetime import datetime, timedelta
from app.models import RefreshToken

def create_refresh_token(db: Session, user_id: int) -> str:
    """
    Create a new refresh token for a user.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        Raw refresh token (only time it's available unhashed)
    """
    # Generate secure random token
    raw_token = secrets.token_urlsafe(32)

    # Hash token for storage (like passwords)
    hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()

    # Calculate expiration
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    # Store hashed token in database
    refresh_token = RefreshToken(
        user_id=user_id,
        token=hashed_token,
        expires_at=expires_at
    )
    db.add(refresh_token)
    db.commit()

    logger.info(f"✅ Created refresh token for user {user_id}")
    return raw_token


def verify_refresh_token(db: Session, raw_token: str) -> Optional[int]:
    """
    Verify a refresh token and return the user ID if valid.

    Args:
        db: Database session
        raw_token: The raw refresh token from client

    Returns:
        User ID if token is valid, None otherwise
    """
    # Hash the provided token
    hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()

    # Find token in database
    token_record = db.query(RefreshToken).filter(
        RefreshToken.token == hashed_token,
        RefreshToken.is_revoked == False,
        RefreshToken.expires_at > datetime.utcnow()
    ).first()

    if token_record:
        return token_record.user_id
    return None


def revoke_refresh_token(db: Session, raw_token: str) -> bool:
    """
    Revoke a refresh token (logout).

    Args:
        db: Database session
        raw_token: The raw refresh token from client

    Returns:
        True if token was revoked, False if not found
    """
    hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()

    token_record = db.query(RefreshToken).filter(
        RefreshToken.token == hashed_token
    ).first()

    if token_record:
        token_record.is_revoked = True
        db.commit()
        logger.info(f"🔒 Revoked refresh token for user {token_record.user_id}")
        return True
    return False


def revoke_all_user_tokens(db: Session, user_id: int):
    """
    Revoke all refresh tokens for a user (e.g., password change, security incident).

    Args:
        db: Database session
        user_id: User ID
    """
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.is_revoked == False
    ).update({"is_revoked": True})
    db.commit()
    logger.info(f"🔒 Revoked all refresh tokens for user {user_id}")


# ═══════════════════════════════════════════════════════════════
# ASYNC REFRESH TOKEN HELPERS (for AsyncSession)
# ═══════════════════════════════════════════════════════════════

async def create_refresh_token_async(db: AsyncSession, user_id: int) -> str:
    """
    Create a new refresh token for a user using AsyncSession.

    Returns:
        Raw refresh token (only time it's available unhashed)
    """
    raw_token = secrets.token_urlsafe(32)
    hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    refresh_token = RefreshToken(
        user_id=user_id,
        token=hashed_token,
        expires_at=expires_at,
    )
    db.add(refresh_token)
    await db.commit()
    await db.refresh(refresh_token)

    logger.info(f"✅ Created refresh token (async) for user {user_id}")
    return raw_token


async def verify_refresh_token_async(db: AsyncSession, raw_token: str) -> Optional[int]:
    """
    Verify a refresh token and return the user ID if valid (AsyncSession).
    """
    hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()
    result = await db.execute(
        select(RefreshToken).filter(
            RefreshToken.token == hashed_token,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > datetime.utcnow(),
        )
    )
    token_record = result.scalar_one_or_none()
    return token_record.user_id if token_record else None


async def revoke_refresh_token_async(db: AsyncSession, raw_token: str) -> bool:
    """
    Revoke a refresh token (AsyncSession).
    """
    hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()
    result = await db.execute(
        select(RefreshToken).filter(RefreshToken.token == hashed_token)
    )
    token_record = result.scalar_one_or_none()
    if token_record:
        token_record.is_revoked = True
        await db.commit()
        logger.info(f"🔒 Revoked refresh token (async) for user {token_record.user_id}")
        return True
    return False

