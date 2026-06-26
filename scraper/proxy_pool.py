"""
Residential proxy pool with health tracking and block-aware rotation. [Phase 1 / S2]

A single static proxy is a single point of failure: when it gets banned every
fetch returns an empty/403 body and the whole crawl silently produces nothing.
This pool rotates across several proxies, quarantines any that return a block
(403/429/empty body) for a growing cooldown, and reports when every proxy is
quarantined ("exhausted") so callers can back off + alert instead of hammering a
banned egress and deepening the ban.

Pure in-memory + time-based; no external deps. Safe to unit-test in isolation.
"""
from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


def mask_proxy(url: str | None) -> str:
    """Hide credentials when logging a proxy URL (user:pass@host -> host)."""
    if not url:
        return "none"
    if "@" in url:
        return url.split("@", 1)[1]
    return url


@dataclass
class _ProxyState:
    url: str
    quarantined_until: float = 0.0
    failures: int = 0
    successes: int = 0


class ProxyPool:
    """
    Rotating pool of proxy URLs with per-proxy quarantine.

    - get(): returns a healthy proxy (round-robin over healthy ones) or None.
      None means EITHER the pool is empty (run direct) OR every proxy is
      quarantined (exhausted — check `.exhausted()` to tell them apart).
    - report_block(url, retry_after): quarantine a proxy after a block; cooldown
      grows with consecutive failures (honoring Retry-After when given).
    - report_success(url): clear a proxy's failure state.
    """

    def __init__(
        self,
        urls: list[str],
        base_cooldown: float = 300.0,
        max_failures: int = 6,
    ) -> None:
        # Dedup while preserving order.
        seen: set[str] = set()
        self._proxies: list[_ProxyState] = []
        for u in urls:
            if u and u not in seen:
                seen.add(u)
                self._proxies.append(_ProxyState(u))
        self._base_cooldown = base_cooldown
        self._max_failures = max_failures
        self._rr = 0

    def __bool__(self) -> bool:
        return bool(self._proxies)

    @property
    def size(self) -> int:
        return len(self._proxies)

    def _healthy(self, now: float) -> list[_ProxyState]:
        return [
            p
            for p in self._proxies
            if p.quarantined_until <= now and p.failures < self._max_failures
        ]

    def get(self) -> str | None:
        """Return a healthy proxy URL (round-robin), or None if none available."""
        if not self._proxies:
            return None
        healthy = self._healthy(time.time())
        if not healthy:
            return None
        self._rr = (self._rr + 1) % len(healthy)
        return healthy[self._rr].url

    def report_block(self, url: str | None, retry_after: float | None = None) -> None:
        if not url:
            return
        for p in self._proxies:
            if p.url == url:
                p.failures += 1
                cooldown = (
                    retry_after
                    if retry_after and retry_after > 0
                    else self._base_cooldown * min(p.failures, 6)
                )
                p.quarantined_until = time.time() + cooldown
                logger.warning(
                    "[proxy] quarantined %s for %.0fs (consecutive failures=%d)",
                    mask_proxy(url),
                    cooldown,
                    p.failures,
                )
                return

    def report_success(self, url: str | None) -> None:
        if not url:
            return
        for p in self._proxies:
            if p.url == url:
                p.successes += 1
                p.failures = 0
                p.quarantined_until = 0.0
                return

    def exhausted(self) -> bool:
        """True when proxies are configured but none are currently healthy."""
        return bool(self._proxies) and not self._healthy(time.time())

    def jittered_backoff(self, base: float, cap: float = 30.0) -> float:
        """Full-jitter backoff helper: random in [base, 2*base], capped."""
        return min(base + random.uniform(0, base), cap)


def build_proxy_pool() -> ProxyPool:
    """Construct the pool from settings (SCRAPER_PROXY_URLS / SCRAPER_PROXY_URL)."""
    from settings import SCRAPER_PROXY_URLS

    pool = ProxyPool(SCRAPER_PROXY_URLS)
    if pool.size:
        logger.info("[proxy] pool initialized with %d proxy(ies)", pool.size)
    return pool
