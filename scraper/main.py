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
    """Scrape only the Nawy Now (instant-delivery) slice."""
    return await _run_listing_api_mode(
        crawl_method="crawl_nawy_now", label="nawy-now",
        dry_run=dry_run, max_pages=max_pages,
    )


async def run_nawy_all(dry_run: bool, max_pages: int) -> int:
    """Scrape Nawy's full unit-level inventory via the public listing API."""
    return await _run_listing_api_mode(
        crawl_method="crawl_all_units", label="nawy-all",
        dry_run=dry_run, max_pages=max_pages,
    )


async def _run_listing_api_mode(crawl_method: str, label: str, dry_run: bool, max_pages: int) -> int:
    """
    Shared runner for any listing-api-backed Nawy crawl.

    Units come from the API already shaped with nested `compound`, `area`,
    `developer` *dicts* + `paymentPlan` dict. The deterministic_normalizer
    handles that shape natively, but the input-side validator expects flat
    strings — so we bypass the validator and feed units straight into
    normalize_unit_list → upsert_properties. Anomaly detector is bypassed
    for the same reason it is for Nawy Now (per-area medians legitimately
    diverge from broad-market baseline in narrow slices).
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
        crawl_fn = getattr(spider, crawl_method)
        res = await crawl_fn(max_pages=max_pages, dry_run=dry_run)
        logger.info(
            "[nawy] %s pages=%d/%d raw=%d",
            label, res.pages_fetched, res.pages_fetched + res.pages_failed, len(res.raw_properties),
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
        norm = normalize_unit_list(res.raw_properties, source_url=label)
        logger.info(
            "[nawy] %s normalized=%d skipped=%d (run_id=%s)",
            label, len(norm.properties), norm.skipped_count, run_id[:8],
        )
        if not norm.properties:
            return rc

        # Skip anomaly detector — narrow slices legitimately diverge from
        # the broad-market baseline (curated feeds, per-area, etc).
        upsert = await upsert_properties(
            norm.properties, run_id=run_id, skip_anomaly_check=True
        )
        logger.info(
            "[nawy] %s upsert: ins=%d upd=%d skip=%d err=%d",
            label, upsert.inserted, upsert.updated, upsert.skipped, upsert.errors,
        )
        # Stale-window publishing (Phase 0 / I29): ONLY a full-catalog crawl
        # (nawy-all) may publish the stale-safe run_id. Narrow slices such as
        # nawy-now cover a fraction of inventory, so registering them would let
        # mark_stale_properties() delist everything they did not touch.
        # Coverage/health gating of the full-catalog run is added in I4.
        if upsert.total > 0:
            if label == "nawy-all":
                await _register_scrape_run_id(run_id)
            else:
                logger.info(
                    "[nawy] %s is a narrow slice — not publishing stale-safe run_id",
                    label,
                )
    except Exception as exc:
        logger.exception("[nawy] %s crawl failed: %s", label, exc)
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
                    # Phase 0 / I29: per-area / per-site / per-compound cron
                    # scrapes do NOT publish the stale-safe run_id. Each covers
                    # only a slice of inventory, so letting them into the 2-slot
                    # window would let mark_stale_properties() delist every row
                    # they did not touch. Only the full-catalog nawy-all crawl
                    # publishes (see _run_listing_api_mode). Rows are still
                    # stamped with this run_id + source via the upsert itself.

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
    p.add_argument("--mode", choices=["cron", "worker", "nawynow", "nawy-all"], default="cron",
                   help="cron = HTML-SSR/Playwright crawl; worker = Redis poller; "
                        "nawynow = listing-api isNawyNow slice; "
                        "nawy-all = listing-api full unit-level walk (19k+ units, no Playwright)")
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

    if args.mode == "nawy-all":
        # No legacy cap — caller supplies --max-pages explicitly; default is
        # large enough to walk every page of /v1/search/properties at
        # pageSize=12 (≈1,588 pages for ~19k units).
        max_pages = args.max_pages if args.max_pages is not None else 2000
        return asyncio.run(run_nawy_all(args.dry_run, max_pages=max_pages))

    sites = [args.site] if args.site else list(SPIDERS.keys())
    areas = [args.area] if args.area else DEFAULT_AREAS
    return asyncio.run(run_cron(sites, areas, args.dry_run, args.compound))


if __name__ == "__main__":
    sys.exit(main())
