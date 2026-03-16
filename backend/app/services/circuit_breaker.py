"""
Circuit Breaker - Phase 4: API Resilience
------------------------------------------
Implements the Circuit Breaker pattern to prevent cascading failures
when external APIs (OpenAI, Paymob) become unavailable.
"""

import time
import logging
import asyncio
from enum import Enum
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"        # Normal operation - requests pass through
    OPEN = "open"            # Failing - reject requests immediately
    HALF_OPEN = "half_open"  # Testing recovery - allow limited requests


class CircuitBreaker:
    """
    Circuit breaker to protect against cascading failures.

    States:
    - CLOSED: Normal operation, all requests pass through
    - OPEN: Too many failures, reject all requests
    - HALF_OPEN: Testing if service recovered, allow one request
    """

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None
        self.last_attempt_time = None
        self._lock = asyncio.Lock()

    def _maybe_transition_to_half_open(self) -> bool:
        """Check if circuit should transition from OPEN to HALF_OPEN. Returns True if still OPEN."""
        if self.state == CircuitState.OPEN:
            if self.last_failure_time and (time.time() - self.last_failure_time) > self.timeout:
                logger.info("Circuit breaker transitioning to HALF_OPEN (testing recovery)")
                self.state = CircuitState.HALF_OPEN
            else:
                return True
        return False

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function through circuit breaker (sync)."""
        if self._maybe_transition_to_half_open():
            raise Exception(f"Circuit breaker is OPEN - service unavailable (retry in {self._time_until_retry()}s)")

        try:
            self.last_attempt_time = time.time()
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise e

    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Execute async function through circuit breaker with lock protection."""
        async with self._lock:
            if self._maybe_transition_to_half_open():
                raise Exception(f"Circuit breaker is OPEN - service unavailable (retry in {self._time_until_retry()}s)")

        try:
            self.last_attempt_time = time.time()
            result = await func(*args, **kwargs)
            async with self._lock:
                self.on_success()
            return result
        except Exception as e:
            async with self._lock:
                self.on_failure()
            raise e

    def on_success(self):
        """Handle successful execution - reset failure count."""
        if self.state == CircuitState.HALF_OPEN:
            logger.info("Circuit breaker: Service recovered - transitioning to CLOSED")
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None

    def on_failure(self):
        """Handle failed execution - increment counter and potentially open circuit."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            logger.warning("Circuit breaker: Recovery test failed - back to OPEN")
            self.state = CircuitState.OPEN
        elif self.failure_count >= self.failure_threshold:
            logger.error(
                "Circuit breaker OPENED - %d failures exceeded threshold of %d",
                self.failure_count, self.failure_threshold,
            )
            self.state = CircuitState.OPEN
        else:
            logger.warning(
                "Circuit breaker: Failure %d/%d",
                self.failure_count, self.failure_threshold,
            )

    def _time_until_retry(self) -> int:
        """Calculate seconds until retry is allowed"""
        if not self.last_failure_time:
            return 0
        elapsed = time.time() - self.last_failure_time
        return max(0, int(self.timeout - elapsed))

    def reset(self):
        """Manually reset circuit breaker."""
        logger.info("Circuit breaker manually reset")
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None

    @property
    def status(self) -> dict:
        """Return current circuit breaker status for monitoring."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "timeout": self.timeout,
            "time_until_retry": self._time_until_retry() if self.state == CircuitState.OPEN else 0,
        }


def circuit(failure_threshold: int = 5, timeout: int = 60):
    """
    Decorator to wrap functions with circuit breaker.

    Usage:
        @circuit(failure_threshold=3, timeout=30)
        def call_external_api():
            ...
    """
    breaker = CircuitBreaker(failure_threshold, timeout)

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        wrapper.breaker = breaker  # Expose breaker for testing/monitoring
        return wrapper
    return decorator


# Pre-configured circuit breakers for common external services
openai_breaker = CircuitBreaker(failure_threshold=3, timeout=30)
claude_breaker = CircuitBreaker(failure_threshold=3, timeout=30)
paymob_breaker = CircuitBreaker(failure_threshold=5, timeout=60)
database_breaker = CircuitBreaker(failure_threshold=5, timeout=10)
blockchain_breaker = CircuitBreaker(failure_threshold=3, timeout=60)
