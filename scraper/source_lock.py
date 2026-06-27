"""
Shared per-site source lock for the scraper (S5 / S6 / S7).

Used by BOTH the cron / full-catalog entrypoint (main.py) and the on-demand Redis
worker (worker.py) so they cannot crawl the same site concurrently — concurrent
crawlers double the request rate and trip an IP ban.

- The lock stores a unique owner TOKEN and is released via a compare-and-delete
  Lua script, so a run whose lock expired mid-crawl can never delete a different
  run's freshly-acquired lock (the lock-stealing cascade). [S5]
- On Redis failure the default is FAIL-CLOSED (skip the run); set
  SCRAPER_LOCK_FAIL_OPEN=true to restore proceed-anyway. [S6]
"""
from __future__ import annotations

import logging
import uuid

logger = logging.getLogger(__name__)

# Lua: delete the lock only if we still own it (stored value == our token).
_RELEASE_LOCK_LUA = (
    "if redis.call('get', KEYS[1]) == ARGV[1] then "
    "return redis.call('del', KEYS[1]) else return 0 end"
)


async def acquire_source_lock(site: str) -> str | None:
    """
    Acquire the per-site lock with a unique owner token. Returns the token on
    success (pass it back to release_source_lock), or None to SKIP the run
    (another run holds it, or Redis is down and we are fail-closed).
    """
    token = uuid.uuid4().hex
    try:
        import redis.asyncio as aioredis

        from settings import REDIS_URL, SOURCE_LOCK_TTL_SECONDS

        client = aioredis.from_url(REDIS_URL, decode_responses=True)
        key = f"scraper:lock:{site}"
        async with client:
            got = await client.set(key, token, nx=True, ex=SOURCE_LOCK_TTL_SECONDS)
        return token if got else None
    except Exception as exc:
        from settings import SCRAPER_LOCK_FAIL_OPEN

        if SCRAPER_LOCK_FAIL_OPEN:
            logger.warning(
                "[lock] %s: Redis error, proceeding UNLOCKED (SCRAPER_LOCK_FAIL_OPEN): %s",
                site, exc,
            )
            return token
        logger.error(
            "[lock] %s: Redis error, SKIPPING run (fail-closed; set "
            "SCRAPER_LOCK_FAIL_OPEN=true to override): %s",
            site, exc,
        )
        return None


async def release_source_lock(site: str, token: str | None) -> None:
    """Compare-and-delete: release only if this run still owns the lock. [S5]"""
    if not token:
        return
    try:
        import redis.asyncio as aioredis

        from settings import REDIS_URL

        client = aioredis.from_url(REDIS_URL, decode_responses=True)
        key = f"scraper:lock:{site}"
        async with client:
            await client.eval(_RELEASE_LOCK_LUA, 1, key, token)
    except Exception:
        pass
