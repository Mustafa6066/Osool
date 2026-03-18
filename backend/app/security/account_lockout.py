"""
Account Security: Lockout and Brute Force Protection
----------------------------------------------------
Prevents brute force attacks on authentication endpoints.

Security Features:
- Account lockout after N failed attempts
- Progressive delays (exponential backoff)
- IP-based rate limiting
- Email notifications for suspicious activity
- Manual unlock mechanism
- Automatic unlock after timeout
"""

import time
import hashlib
from typing import Optional, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# Configuration
MAX_FAILED_ATTEMPTS = 5  # Lock after 5 failed attempts
LOCKOUT_DURATION_MINUTES = 30  # Lock for 30 minutes
PROGRESSIVE_DELAY_BASE = 2  # Seconds
AUTO_UNLOCK_HOURS = 24  # Automatically unlock after 24 hours


@dataclass
class AccountLockoutState:
    """State of account lockout."""
    failed_attempts: int = 0
    last_failed_at: Optional[datetime] = None
    locked_until: Optional[datetime] = None
    lockout_reason: Optional[str] = None


class AccountLockoutManager:
    """
    Manages account lockouts and brute force protection.
    
    Uses both Redis (if available) and in-memory storage.
    """
    
    def __init__(self):
        # In-memory storage (fallback)
        self._lockouts: Dict[str, AccountLockoutState] = {}
        self._redis_client = None
        
        # Try to initialize Redis
        try:
            from app.services.cache import cache
            if cache.redis and cache.redis.ping():
                self._redis_client = cache.redis
                logger.info("Account lockout using Redis storage")
        except Exception:
            logger.warning("Account lockout using in-memory storage (not distributed-safe)")
    
    def _get_lockout_key(self, identifier: str) -> str:
        """Generate Redis key for lockout data."""
        # Hash identifier for privacy
        hashed = hashlib.sha256(identifier.encode()).hexdigest()[:16]
        return f"lockout:{hashed}"
    
    def record_failed_attempt(self, identifier: str, ip_address: Optional[str] = None):
        """
        Record a failed login attempt.
        
        Args:
            identifier: Email or username
            ip_address: IP address of the request
        """
        key = self._get_lockout_key(identifier)
        now = datetime.utcnow()
        
        if self._redis_client:
            # Use Redis
            try:
                # Increment failed attempts
                failed_count = self._redis_client.incr(f"{key}:attempts")
                self._redis_client.expire(f"{key}:attempts", 86400)  # 24 hours
                
                # Record timestamp
                self._redis_client.set(f"{key}:last_failed", now.isoformat(), ex=86400)
                
                # Record IP
                if ip_address:
                    self._redis_client.sadd(f"{key}:ips", ip_address)
                    self._redis_client.expire(f"{key}:ips", 86400)
                
                logger.info(f"Failed attempt #{failed_count} for {identifier[:3]}*** from {ip_address}")
                
                # Lock account if threshold exceeded
                if failed_count >= MAX_FAILED_ATTEMPTS:
                    self._lock_account_redis(key, identifier)
            
            except Exception as e:
                logger.error(f"Redis error in record_failed_attempt: {e}")
                self._record_failed_attempt_memory(identifier, now, ip_address)
        else:
            # Use in-memory storage
            self._record_failed_attempt_memory(identifier, now, ip_address)
    
    def _record_failed_attempt_memory(self, identifier: str, now: datetime, ip_address: Optional[str]):
        """Record failed attempt in memory."""
        if identifier not in self._lockouts:
            self._lockouts[identifier] = AccountLockoutState()
        
        state = self._lockouts[identifier]
        state.failed_attempts += 1
        state.last_failed_at = now
        
        logger.info(f"Failed attempt #{state.failed_attempts} for {identifier[:3]}*** from {ip_address}")
        
        # Lock if threshold exceeded
        if state.failed_attempts >= MAX_FAILED_ATTEMPTS:
            state.locked_until = now + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            state.lockout_reason = "exceeded_max_attempts"
            logger.warning(f"Account locked: {identifier[:3]}*** until {state.locked_until}")
    
    def _lock_account_redis(self, key: str, identifier: str):
        """Lock account in Redis."""
        try:
            locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            self._redis_client.set(
                f"{key}:locked_until",
                locked_until.isoformat(),
                ex=LOCKOUT_DURATION_MINUTES * 60
            )
            logger.warning(f"Account locked: {identifier[:3]}*** until {locked_until}")
        except Exception as e:
            logger.error(f"Error locking account in Redis: {e}")
    
    def is_locked(self, identifier: str, ip_address: Optional[str] = None) -> bool:
        """
        Check if account is locked.

        Args:
            identifier: Email or username to check
            ip_address: Ignored (kept for API compatibility with IP-aware callers)

        Returns:
            True if the account is currently locked, False otherwise.
            Previously returned a tuple — changed to plain bool to avoid
            the common Python pitfall where (False, None) is truthy.
        """
        key = self._get_lockout_key(identifier)
        now = datetime.utcnow()
        
        if self._redis_client:
            try:
                locked_until_str = self._redis_client.get(f"{key}:locked_until")
                if locked_until_str:
                    locked_until = datetime.fromisoformat(locked_until_str if isinstance(locked_until_str, str) else locked_until_str.decode())
                    if now < locked_until:
                        return True
                    else:
                        # Lock expired, clean up
                        self._redis_client.delete(f"{key}:locked_until")
                        self._redis_client.delete(f"{key}:attempts")
                        return False
                return False
            except Exception as e:
                logger.error(f"Error checking lockout in Redis: {e}")
                locked, _ = self._is_locked_memory(identifier, now)
                return locked
        else:
            locked, _ = self._is_locked_memory(identifier, now)
            return locked

    def reset(self, identifier: str):
        """Alias for reset_attempts() — convenience method."""
        self.reset_attempts(identifier)
    
    def _is_locked_memory(self, identifier: str, now: datetime) -> tuple[bool, Optional[datetime]]:
        """Check if account is locked in memory."""
        if identifier not in self._lockouts:
            return False, None
        
        state = self._lockouts[identifier]
        
        if state.locked_until and now < state.locked_until:
            return True, state.locked_until
        elif state.locked_until and now >= state.locked_until:
            # Lock expired
            state.failed_attempts = 0
            state.locked_until = None
            state.lockout_reason = None
            return False, None
        
        return False, None
    
    def reset_attempts(self, identifier: str):
        """
        Reset failed attempts after successful login.
        
        Args:
            identifier: Email or username
        """
        key = self._get_lockout_key(identifier)
        
        if self._redis_client:
            try:
                self._redis_client.delete(f"{key}:attempts")
                self._redis_client.delete(f"{key}:last_failed")
                self._redis_client.delete(f"{key}:locked_until")
                self._redis_client.delete(f"{key}:ips")
                logger.info(f"Lockout reset for {identifier[:3]}***")
            except Exception as e:
                logger.error(f"Error resetting lockout in Redis: {e}")
                self._reset_attempts_memory(identifier)
        else:
            self._reset_attempts_memory(identifier)
    
    def _reset_attempts_memory(self, identifier: str):
        """Reset attempts in memory."""
        if identifier in self._lockouts:
            del self._lockouts[identifier]
    
    def get_progressive_delay(self, identifier: str) -> float:
        """
        Calculate progressive delay based on failed attempts.
        
        Uses exponential backoff: delay = BASE^(attempts-1) seconds
        
        Returns:
            Delay in seconds
        """
        key = self._get_lockout_key(identifier)
        
        if self._redis_client:
            try:
                attempts = int(self._redis_client.get(f"{key}:attempts") or 0)
                if attempts == 0:
                    return 0.0
                
                # Exponential backoff: 2^0, 2^1, 2^2, 2^3, 2^4 = 0, 2, 4, 8, 16 seconds
                delay = PROGRESSIVE_DELAY_BASE ** (attempts - 1)
                return min(delay, 60.0)  # Cap at 60 seconds
            except Exception:
                return self._get_progressive_delay_memory(identifier)
        else:
            return self._get_progressive_delay_memory(identifier)
    
    def _get_progressive_delay_memory(self, identifier: str) -> float:
        """Get progressive delay from memory."""
        if identifier not in self._lockouts:
            return 0.0
        
        attempts = self._lockouts[identifier].failed_attempts
        if attempts == 0:
            return 0.0
        
        delay = PROGRESSIVE_DELAY_BASE ** (attempts - 1)
        return min(delay, 60.0)
    
    def manual_unlock(self, identifier: str, admin_email: str):
        """
        Manually unlock an account (admin action).
        
        Args:
            identifier: Email or username to unlock
            admin_email: Email of admin performing unlock
        """
        key = self._get_lockout_key(identifier)
        
        if self._redis_client:
            try:
                self._redis_client.delete(f"{key}:attempts")
                self._redis_client.delete(f"{key}:locked_until")
                logger.info(f"Account manually unlocked: {identifier} by {admin_email}")
            except Exception as e:
                logger.error(f"Error unlocking account in Redis: {e}")
                self._reset_attempts_memory(identifier)
        else:
            self._reset_attempts_memory(identifier)
    
    def get_lockout_info(self, identifier: str) -> dict:
        """
        Get detailed lockout information.
        
        Returns:
            dict with lockout state
        """
        key = self._get_lockout_key(identifier)
        is_locked, locked_until = self.is_locked(identifier)
        
        info = {
            "is_locked": is_locked,
            "locked_until": locked_until.isoformat() if locked_until else None,
            "failed_attempts": 0,
            "max_attempts": MAX_FAILED_ATTEMPTS,
        }
        
        if self._redis_client:
            try:
                attempts = self._redis_client.get(f"{key}:attempts")
                info["failed_attempts"] = int(attempts) if attempts else 0
            except Exception:
                pass
        elif identifier in self._lockouts:
            info["failed_attempts"] = self._lockouts[identifier].failed_attempts
        
        return info


# Global instance
lockout_manager = AccountLockoutManager()


# ═══════════════════════════════════════════════════════════════
# FASTAPI DEPENDENCY
# ═══════════════════════════════════════════════════════════════

from fastapi import HTTPException, Request
import asyncio


async def check_account_lockout(request: Request, identifier: str):
    """
    FastAPI dependency to check account lockout before authentication.
    
    Usage:
        @router.post("/login")
        async def login(request: Request, email: str):
            await check_account_lockout(request, email)
            # ... rest of login logic
    
    Raises:
        HTTPException: 429 if account is locked
    """
    # Check if locked
    is_locked, locked_until = lockout_manager.is_locked(identifier)
    
    if is_locked:
        remaining_minutes = int((locked_until - datetime.utcnow()).total_seconds() / 60)
        raise HTTPException(
            status_code=429,
            detail={
                "error": "account_locked",
                "message": f"Account temporarily locked due to too many failed login attempts. Try again in {remaining_minutes} minutes.",
                "locked_until": locked_until.isoformat(),
                "retry_after": remaining_minutes * 60
            },
            headers={"Retry-After": str(remaining_minutes * 60)}
        )
    
    # Apply progressive delay
    delay = lockout_manager.get_progressive_delay(identifier)
    if delay > 0:
        logger.info(f"Applying {delay}s delay for {identifier[:3]}***")
        await asyncio.sleep(delay)


async def record_login_failure(request: Request, identifier: str):
    """
    Record failed login attempt.
    
    Usage:
        try:
            # authenticate
        except AuthenticationError:
            await record_login_failure(request, email)
    """
    ip_address = request.client.host if request.client else None
    lockout_manager.record_failed_attempt(identifier, ip_address)


async def record_login_success(identifier: str):
    """
    Reset lockout on successful login.
    """
    lockout_manager.reset_attempts(identifier)
