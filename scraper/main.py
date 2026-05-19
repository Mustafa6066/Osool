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
                    flush_res = await flush(res.raw_properties, site)
                    logger.info(
                        "[%s] upsert: ins=%d upd=%d skip=%d err=%d alert=%s",
                        site,
                        flush_res.upserted.inserted,
                        flush_res.upserted.updated,
                        flush_res.upserted.skipped,
                        flush_res.upserted.errors,
                        flush_res.alert_sent,
                    )

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
    p.add_argument("--mode", choices=["cron", "worker"], default="cron")
    p.add_argument("--site", choices=list(SPIDERS.keys()), default=None,
                   help="Restrict to one site (default: all)")
    p.add_argument("--area", default=None, help="Restrict to one Egyptian zone slug")
    p.add_argument("--compound", default=None,
                   help="Single compound/area slug (used by on-demand worker)")
    p.add_argument("--dry-run", action="store_true",
                   help="Print extracted properties without DB writes")
    return p.parse_args()


def main() -> int:
    _configure_logging()
    args = parse_args()

    if args.mode == "worker":
        from worker import run_worker

        asyncio.run(run_worker())
        return 0

    sites = [args.site] if args.site else list(SPIDERS.keys())
    areas = [args.area] if args.area else DEFAULT_AREAS
    return asyncio.run(run_cron(sites, areas, args.dry_run, args.compound))


if __name__ == "__main__":
    sys.exit(main())
