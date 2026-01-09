"""
Circuit Breaker - Phase 4: API Resilience
------------------------------------------
Implements the Circuit Breaker pattern to prevent cascading failures
when external APIs (OpenAI, Paymob, Blockchain RPC) become unavailable.
"""

import time
import logging
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

    Example:
        breaker = CircuitBreaker(failure_threshold=5, timeout=60)
        result = breaker.call(some_api_function, arg1, arg2)
    """

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before attempting recovery (HALF_OPEN)
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None
        self.last_attempt_time = None

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is OPEN or function fails
        """
        # Check if circuit should transition from OPEN to HALF_OPEN
        if self.state == CircuitState.OPEN:
            if self.last_failure_time and (time.time() - self.last_failure_time) > self.timeout:
                logger.info(f"🔄 Circuit breaker transitioning to HALF_OPEN (testing recovery)")
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception(f"Circuit breaker is OPEN - service unavailable (retry in {self._time_until_retry()}s)")

        # Attempt to execute function
        try:
            self.last_attempt_time = time.time()
            result = func(*args, **kwargs)
            self.on_success()
            return result

        except Exception as e:
            self.on_failure()
            raise e

    def on_success(self):
        """Handle successful execution - reset failure count"""
        if self.state == CircuitState.HALF_OPEN:
            logger.info("✅ Circuit breaker: Service recovered - transitioning to CLOSED")

        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None

    def on_failure(self):
        """Handle failed execution - increment counter and potentially open circuit"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            # Failed while testing recovery - go back to OPEN
            logger.warning(f"❌ Circuit breaker: Recovery test failed - back to OPEN")
            self.state = CircuitState.OPEN

        elif self.failure_count >= self.failure_threshold:
            # Threshold exceeded - open the circuit
            logger.error(
                f"🚨 Circuit breaker OPENED - {self.failure_count} failures exceeded threshold"
            )
            self.state = CircuitState.OPEN

        else:
            logger.warning(
                f"⚠️ Circuit breaker: Failure {self.failure_count}/{self.failure_threshold}"
            )

    def _time_until_retry(self) -> int:
        """Calculate seconds until retry is allowed"""
        if not self.last_failure_time:
            return 0
        elapsed = time.time() - self.last_failure_time
        return max(0, int(self.timeout - elapsed))

    def reset(self):
        """Manually reset circuit breaker (for testing or admin override)"""
        logger.info("🔄 Circuit breaker manually reset")
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None


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
paymob_breaker = CircuitBreaker(failure_threshold=5, timeout=60)
blockchain_breaker = CircuitBreaker(failure_threshold=5, timeout=120)
