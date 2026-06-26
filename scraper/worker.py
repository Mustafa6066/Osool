"""
Long-running Redis worker.

Consumes the `scraper:pending` queue published by the orchestrator
([Osool-orchestrator/apps/api/src/jobs/handlers/scraper-refresh.job.ts]) and
runs the matching spider for one site / area / compound. Writes a status
entry to `scraper:refresh:log` so the orchestrator can show recent activity.

Job payload shape (mirrors ScraperRefreshJobData):
    {
      "source": "nawy" | "aqarmap",
      "mode":   "compound" | "area" | "full",
      "targetArea": "new-cairo",
      "targetCompoundSlug": "mountain-view-icity"
    }
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

import redis.asyncio as aioredis

from adapters.ingestion import flush
from settings import (
    PENDING_QUEUE_KEY,
    REDIS_URL,
    REFRESH_LOG_KEEP,
    REFRESH_LOG_KEY,
)
from sites.aqarmap import AqarmapSpider
from sites.nawy import NawySpider

logger = logging.getLogger("osool.scraper.worker")

SPIDERS = {"nawy": NawySpider, "aqarmap": AqarmapSpider}


async def run_worker() -> None:
    client = aioredis.from_url(REDIS_URL, decode_responses=True)
    logger.info("worker listening on %s", PENDING_QUEUE_KEY)
    async with client:
        while True:
            try:
                # BLPOP returns (key, value) or None on timeout
                popped = await client.blpop(PENDING_QUEUE_KEY, timeout=30)
                if not popped:
                    continue
                _, payload = popped
                await _handle_job(client, payload)
            except asyncio.CancelledError:
                logger.info("worker cancelled — exiting")
                return
            except Exception as exc:
                logger.exception("worker loop error: %s", exc)
                await asyncio.sleep(2)


async def _handle_job(client, raw_payload: str) -> None:
    started = datetime.now(timezone.utc)
    try:
        job = json.loads(raw_payload)
    except json.JSONDecodeError:
        logger.error("bad job payload: %r", raw_payload[:200])
        return

    source = job.get("source")
    mode = job.get("mode", "area")
    target_area = job.get("targetArea")
    target_compound = job.get("targetCompoundSlug")

    spider_cls = SPIDERS.get(source)
    if not spider_cls:
        await _log_status(client, source, mode, "error", "unknown source", started)
        return

    # S7: take the SAME per-site source lock the cron uses, so an on-demand
    # refresh can't crawl concurrently with the scheduled crawl (double request
    # rate → ban). Skip if the lock is held (or Redis is down + fail-closed).
    from source_lock import acquire_source_lock, release_source_lock

    lock_token = await acquire_source_lock(source)
    if not lock_token:
        # Either another run holds the lock, or Redis is down + fail-closed (S6);
        # source_lock logs the specific reason.
        logger.warning("[worker] %s source busy or lock unavailable — skipping job", source)
        await _log_status(client, source, mode, "skipped", "source lock unavailable", started)
        return

    # Bind spider before the try so a constructor failure still reaches the finally
    # and RELEASES the lock — otherwise the per-source lock leaks until TTL (~1h).
    spider = None
    try:
        spider = spider_cls()
        if mode == "compound" and target_compound:
            res = await spider.crawl_compound(target_compound)
        elif target_area:
            res = await spider.crawl_area(target_area)
        else:
            await _log_status(client, source, mode, "error", "missing area/compound", started)
            return

        if not res.raw_properties:
            await _log_status(client, source, mode, "empty",
                              f"no properties (pages={res.pages_fetched})", started)
            return

        # I5: stamp refreshed rows with the source's current stale-safe run_id so
        # the next mark_stale sweep does not delist what we just refreshed. If no
        # full-catalog run has published yet, flush mints its own and no sweep runs.
        from app.services.cache import cache
        safe_run_id = cache.get(f"scraper:run_id:current:{source}")
        # S7: narrow per-area/compound scrapes legitimately diverge from the
        # broad-market anomaly baseline (same reason the cron passes this).
        flush_res = await flush(
            res.raw_properties, site=source, run_id=safe_run_id, skip_anomaly_check=True
        )
        summary = (
            f"ins={flush_res.upserted.inserted} upd={flush_res.upserted.updated} "
            f"skip={flush_res.upserted.skipped} err={flush_res.upserted.errors}"
        )
        await _log_status(client, source, mode, "ok", summary, started,
                          extra={"area": target_area, "compound": target_compound})
    except Exception as exc:
        logger.exception("job failed: %s", exc)
        await _log_status(client, source, mode, "error", str(exc)[:300], started)
    finally:
        if spider is not None and hasattr(spider, "aclose"):
            await spider.aclose()
        await release_source_lock(source, lock_token)


async def _log_status(client, source, mode, status, message, started, extra=None) -> None:
    entry = {
        "source": source,
        "mode": mode,
        "status": status,
        "message": message,
        "startedAt": started.isoformat(),
        "finishedAt": datetime.now(timezone.utc).isoformat(),
    }
    if extra:
        entry.update({k: v for k, v in extra.items() if v is not None})
    try:
        await client.lpush(REFRESH_LOG_KEY, json.dumps(entry))
        await client.ltrim(REFRESH_LOG_KEY, 0, REFRESH_LOG_KEEP - 1)
    except Exception as exc:
        logger.warning("failed to log refresh status: %s", exc)
