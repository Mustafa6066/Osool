"""
Unified scraper entrypoint.

Usage:
    python main.py --mode=cron                          # crawl every site x every area
    python main.py --mode=cron --site=aqarmap           # one site, all areas
    python main.py --mode=cron --site=nawy --area=new-cairo
    python main.py --mode=cron --dry-run                # no DB writes
    python main.py --mode=worker                        # long-running Redis poller
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from adapters.ingestion import dry_run_print, flush
from settings import DEFAULT_AREAS, REQUEST_DELAY_SECONDS, SOURCE_LOCK_TTL_SECONDS
from sites.aqarmap import AqarmapSpider
from sites.base import SiteSpider
from sites.nawy import NawySpider

logger = logging.getLogger("osool.scraper")

SPIDERS: dict[str, type[SiteSpider]] = {
    "nawy": NawySpider,
    "aqarmap": AqarmapSpider,
}


def _configure_logging() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


async def _acquire_source_lock(site: str) -> bool:
    """Match the orchestrator's 10-min source lock contract."""
    try:
        import redis.asyncio as aioredis

        from settings import REDIS_URL

        client = aioredis.from_url(REDIS_URL, decode_responses=True)
        key = f"scraper:lock:{site}"
        async with client:
            got = await client.set(key, "1", nx=True, ex=SOURCE_LOCK_TTL_SECONDS)
        return bool(got)
    except Exception as exc:
        logger.warning("source lock check failed for %s (proceeding): %s", site, exc)
        return True


async def _release_source_lock(site: str) -> None:
    try:
        import redis.asyncio as aioredis

        from settings import REDIS_URL

        client = aioredis.from_url(REDIS_URL, decode_responses=True)
        async with client:
            await client.delete(f"scraper:lock:{site}")
    except Exception:
        pass


async def _register_scrape_run_id(run_id: str) -> None:
    """
    Push a successful scrape's run_id into the 2-slot Redis window read by
    app.services.nawy_scraper.mark_stale_properties (current + previous).

    Keys live for 7 days; previous is moved off before current is overwritten,
    matching the cache.set() pattern in app/services/nawy_scraper.py:252.
    Failures are non-fatal — stale cleanup is a best-effort safety net.
    """
    try:
        import redis.asyncio as aioredis

        from settings import REDIS_URL

        client = aioredis.from_url(REDIS_URL, decode_responses=True)
        async with client:
            existing = await client.get("scraper:run_id:current")
            if existing and existing != run_id:
                await client.set("scraper:run_id:previous", existing, ex=604800)
            await client.set("scraper:run_id:current", run_id, ex=604800)
        logger.info("[scraper] registered run_id=%s in Redis (current; previous archived)", run_id[:8])
    except Exception as exc:
        logger.warning("[scraper] failed to register run_id in Redis: %s", exc)


async def run_nawy_now(dry_run: bool, max_pages: int) -> int:
    """
    Scrape /nawy-now (instant-delivery feed).

    The units come back from Nawy's __NEXT_DATA__ already shaped with nested
    `compound`, `area`, `developer` *dicts* + a `paymentPlan` dict. The
    deterministic_normalizer handles that shape natively, but the input-side
    validator in app.ingestion.scraper_schemas expects flat strings — so we
    bypass that validator here and feed the units straight into
    normalize_unit_list → upsert_properties.
    """
    spider_cls = SPIDERS.get("nawy")
    if not spider_cls:
        logger.error("nawy spider not registered")
        return 1

    got_lock = await _acquire_source_lock("nawy")
    if not got_lock:
        logger.warning("[nawy] another run holds the source lock — skipping")
        return 0

    spider = spider_cls()
    rc = 0
    try:
        res = await spider.crawl_nawy_now(max_pages=max_pages, dry_run=dry_run)
        logger.info(
            "[nawy] nawy-now pages=%d/%d raw=%d",
            res.pages_fetched, res.pages_fetched + res.pages_failed, len(res.raw_properties),
        )
        if not res.raw_properties:
            return rc

        if dry_run:
            await dry_run_print(res.raw_properties, "nawy")
            return rc

        # Live path: normalize + upsert, skip the flat-string validator.
        import uuid

        from app.ingestion.deterministic_normalizer import normalize_unit_list
        from app.ingestion.repository import upsert_properties

        run_id = str(uuid.uuid4())
        norm = normalize_unit_list(res.raw_properties, source_url="nawy-now")
        logger.info(
            "[nawy] nawy-now normalized=%d skipped=%d (run_id=%s)",
            len(norm.properties), norm.skipped_count, run_id[:8],
        )
        if not norm.properties:
            return rc

        # Skip anomaly detector — Nawy Now is a curated instant-delivery slice
        # whose per-area medians diverge from the broad-market baseline by
        # design (premium segment, ready-to-move bias, etc.).
        upsert = await upsert_properties(
            norm.properties, run_id=run_id, skip_anomaly_check=True
        )
        logger.info(
            "[nawy] nawy-now upsert: ins=%d upd=%d skip=%d err=%d",
            upsert.inserted, upsert.updated, upsert.skipped, upsert.errors,
        )
        # Register the run so mark_stale_properties() can use it as the
        # "safe" run when flagging sold/withdrawn listings.
        if upsert.total > 0:
            await _register_scrape_run_id(run_id)
    except Exception as exc:
        logger.exception("[nawy] nawy-now crawl failed: %s", exc)
        rc = 1
    finally:
        if hasattr(spider, "aclose"):
            await spider.aclose()
        await _release_source_lock("nawy")
    return rc


async def run_cron(
    sites: list[str],
    areas: list[str],
    dry_run: bool,
    compound_slug: str | None = None,
) -> int:
    rc = 0
    for site in sites:
        spider_cls = SPIDERS.get(site)
        if not spider_cls:
            logger.error("unknown site: %s", site)
            rc = 1
            continue

        got_lock = await _acquire_source_lock(site)
        if not got_lock:
            logger.warning("[%s] another run holds the source lock — skipping", site)
            continue

        spider = spider_cls()
        try:
            for area in areas:
                if compound_slug:
                    res = await spider.crawl_compound(compound_slug, dry_run=dry_run)
                else:
                    res = await spider.crawl_area(area, dry_run=dry_run)

                logger.info(
                    "[%s] area=%s pages=%d/%d raw=%d",
                    site, area, res.pages_fetched, res.pages_fetched + res.pages_failed,
                    len(res.raw_properties),
                )

                if not res.raw_properties:
                    continue

                if dry_run:
                    await dry_run_print(res.raw_properties, site)
                else:
                    # Per-area / per-site scrapes legitimately diverge from
                    # the broad-market anomaly-detector baseline. The
                    # detector is designed for whole-market refreshes; for
                    # narrow scrapes (per-area, single-compound, single-
                    # site) the per-area median is structurally different
                    # from history. Bypass so the upsert can proceed.
                    flush_res = await flush(
                        res.raw_properties, site, skip_anomaly_check=True
                    )
                    logger.info(
                        "[%s] upsert: ins=%d upd=%d skip=%d err=%d alert=%s",
                        site,
                        flush_res.upserted.inserted,
                        flush_res.upserted.updated,
                        flush_res.upserted.skipped,
                        flush_res.upserted.errors,
                        flush_res.alert_sent,
                    )
                    # Register the run so mark_stale_properties() can mark
                    # withdrawn listings unavailable.
                    if flush_res.upserted.total > 0:
                        await _register_scrape_run_id(flush_res.run_id)

                await asyncio.sleep(REQUEST_DELAY_SECONDS)

                if compound_slug:
                    break  # compound_slug = single-shot, ignore further areas
        except Exception as exc:
            logger.exception("[%s] crawl failed: %s", site, exc)
            rc = 1
        finally:
            if hasattr(spider, "aclose"):
                await spider.aclose()
            await _release_source_lock(site)

    return rc


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["cron", "worker", "nawynow"], default="cron",
                   help="cron = full crawl; worker = Redis poller; nawynow = paginate /nawy-now feed")
    p.add_argument("--site", choices=list(SPIDERS.keys()), default=None,
                   help="Restrict to one site (default: all)")
    p.add_argument("--area", default=None, help="Restrict to one Egyptian zone slug")
    p.add_argument("--compound", default=None,
                   help="Single compound/area slug (used by on-demand worker)")
    p.add_argument("--dry-run", action="store_true",
                   help="Print extracted properties without DB writes")
    p.add_argument("--max-pages", type=int, default=None,
                   help="Override SCRAPER_MAX_PAGES for nawynow pagination")
    return p.parse_args()


def main() -> int:
    _configure_logging()
    args = parse_args()

    if args.mode == "worker":
        from worker import run_worker

        asyncio.run(run_worker())
        return 0

    if args.mode == "nawynow":
        from settings import MAX_PAGES_PER_AREA
        max_pages = args.max_pages if args.max_pages is not None else MAX_PAGES_PER_AREA
        return asyncio.run(run_nawy_now(args.dry_run, max_pages=max_pages))

    sites = [args.site] if args.site else list(SPIDERS.keys())
    areas = [args.area] if args.area else DEFAULT_AREAS
    return asyncio.run(run_cron(sites, areas, args.dry_run, args.compound))


if __name__ == "__main__":
    sys.exit(main())
