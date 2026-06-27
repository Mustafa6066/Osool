"""
Per-host circuit breaker for scraper HTTP (Phase 1 / S20).

Reuses the shared app.services.circuit_breaker.CircuitBreaker so every scraper
shares ONE resilience policy instead of each hand-rolling its own. Once a host
has failed `failure_threshold` times in a row the breaker OPENS and subsequent
fetches short-circuit (return fast) for `timeout` seconds — so a site-wide block
or outage halts the run instead of hammering a banned/down host across thousands
of URLs (and deepening the ban). After the timeout one probe is allowed
(HALF_OPEN); a success closes the circuit again.

Falls back to a no-op breaker when app.* isn't importable (standalone dev), so the
scraper still runs without it.
"""
from __future__ import annotations

import logging
import os
import time
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

try:
    from app.services.circuit_breaker import CircuitBreaker, CircuitState

    _HAVE = True
except Exception:  # standalone fallback — no app.* available
    _HAVE = False
    CircuitState = None  # type: ignore

    class CircuitBreaker:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass

        def on_success(self):
            pass

        def on_failure(self):
            pass


# Scraper-tuned: tolerate transient blips, open after sustained failure, retest
# after 5 minutes. Override via env for ops tuning.
_FAILURE_THRESHOLD = int(os.getenv("SCRAPER_BREAKER_THRESHOLD", "8"))
_TIMEOUT = int(os.getenv("SCRAPER_BREAKER_TIMEOUT", "300"))

_breakers: dict[str, CircuitBreaker] = {}


def _host(url: str) -> str:
    try:
        return urlparse(url).netloc or url
    except Exception:
        return url


def get_host_breaker(url: str) -> CircuitBreaker:
    """Return the shared circuit breaker for the URL's host (created on demand)."""
    host = _host(url)
    breaker = _breakers.get(host)
    if breaker is None:
        breaker = CircuitBreaker(failure_threshold=_FAILURE_THRESHOLD, timeout=_TIMEOUT)
        _breakers[host] = breaker
    return breaker


def should_block(breaker: CircuitBreaker) -> bool:
    """
    True if the breaker is OPEN and still within its cooldown (reject fast).
    Past the timeout it transitions OPEN→HALF_OPEN to allow one probe — mirroring
    the breaker's own gate using its public attributes (so we don't reach into a
    private method).
    """
    if not _HAVE or CircuitState is None:
        return False
    try:
        if breaker.state == CircuitState.OPEN:
            if (
                breaker.last_failure_time
                and (time.time() - breaker.last_failure_time) > breaker.timeout
            ):
                breaker.state = CircuitState.HALF_OPEN
                return False
            return True
        return False
    except Exception:
        return False
