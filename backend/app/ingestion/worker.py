"""
ARQ Worker — Task Queue + Dynamic URL Discovery
------------------------------------------------
Pillar 2 + 4: Autonomous Dynamic Discovery + Distributed Task Queue.

This module is the entry point for the ARQ worker process. Run with:

    python -m arq app.ingestion.worker.WorkerSettings

Design choices:
  - ARQ (Async Redis Queue) instead of Celery: tasks are native async coroutines,
    no asyncio.run() anti-pattern, no synchronization overhead.
  - Celery is retained for notification/drip-email tasks (see celery_app.py).
  - APScheduler continues running inside FastAPI for economic/geo/image/marketing jobs.
    Only the property scraper job is superseded by ARQ.

Worker topology:
  master_discovery_job (cron: Sunday 02:00 UTC)
    └── Discovers compound URLs from sitemap.xml + /compounds pagination
    └── Filters against DB (only new or >7-day-old records)
    └── Enqueues scrape_compound_task per URL

  scrape_compound_task (individual job per compound)
    └── core_scraper.scrape_compound() → raw JSON
    └── llm_normalizer.normalize_properties() → NormalizedProperty list
    └── repository.upsert_properties() → UpsertResult (hash-differential)

  mark_stale_job (cron: Sunday 06:00 UTC)
    └── Marks properties not seen in current/previous run as unavailable

  price_flag_job (cron: Sunday 06:30 UTC)
    └── Flags above/below-average-priced properties per zone

  geopolitical_scraper_job (cron: daily 04:00 UTC)
    └── Delegates to existing geopolitical_scraper service
"""

from __future__ import annotations

import logging
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from xml.etree import ElementTree

import httpx
from arq import cron
from arq.connections import RedisSettings
from sqlalchemy import select, text

from app.database import AsyncSessionLocal
from app.ingestion.core_scraper import ScraperError, scrape_compound
from app.ingestion.llm_normalizer import normalize_properties
from app.ingestion.repository import upsert_properties
from app.models import Property
from app.services.nawy_scraper import (
    flag_underpriced_properties,
    mark_stale_properties,
    register_scrape_run_id,
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

NAWY_BASE_URL = "https://www.nawy.com"
NAWY_SITEMAP_URL = f"{NAWY_BASE_URL}/sitemap.xml"
NAWY_COMPOUND_PATTERN = re.compile(r"https://www\.nawy\.com/compounds?/[^/\s]+$")

RESCRAPE_DAYS = int(os.getenv("NAWY_RESCRAPE_DAYS", "7"))
MAX_DISCOVERY_PAGES = int(os.getenv("NAWY_DISCOVERY_MAX_PAGES", "50"))

# Sitemap XML namespace
_SM_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"


# ─────────────────────────────────────────────────────────────────────────────
# Worker Lifecycle
# ─────────────────────────────────────────────────────────────────────────────

async def startup(ctx: dict) -> None:
    """
    Called once when the ARQ worker process starts.
    Initializes shared async resources stored in the context dict.
    """
    ctx["http"] = httpx.AsyncClient(
        timeout=httpx.Timeout(30.0, connect=10.0),
        headers={
            "User-Agent": (
                "Mozilla/5.0 (compatible; OsoolBot/1.0; "
                "+https://osool.eg/bot)"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
        follow_redirects=True,
    )
    logger.info("[worker] ARQ worker started — run_id will be generated per discovery job")


async def shutdown(ctx: dict) -> None:
    """
    Called once on graceful shutdown (SIGTERM/SIGINT).
    Closes shared resources.
    """
    http: httpx.AsyncClient = ctx.get("http")
    if http:
        await http.aclose()
    logger.info("[worker] ARQ worker shut down cleanly")


# ─────────────────────────────────────────────────────────────────────────────
# URL Discovery
# ─────────────────────────────────────────────────────────────────────────────

async def _fetch_sitemap_urls(http: httpx.AsyncClient) -> list[str]:
    """
    Fetches and parses Nawy's sitemap.xml.

    Handles nested sitemaps (sitemap index → sub-sitemaps → <loc> entries).
    Filters to compound-detail URLs only via NAWY_COMPOUND_PATTERN.

    Returns:
        List of unique compound URLs from sitemaps. May be empty.
    """
    urls: list[str] = []

    try:
        resp = await http.get(NAWY_SITEMAP_URL)
        resp.raise_for_status()
        root = ElementTree.fromstring(resp.content)
    except Exception as exc:
        logger.warning("[discovery] Sitemap fetch/parse failed: %s", exc)
        return urls

    # Check if this is a sitemap index (contains <sitemap> elements)
    ns = {"sm": _SM_NS}
    sub_sitemaps = root.findall("sm:sitemap/sm:loc", ns)

    if sub_sitemaps:
        # Nawy uses a sitemap index — fetch each sub-sitemap
        for loc_el in sub_sitemaps:
            sub_url = (loc_el.text or "").strip()
            if not sub_url:
                continue
            try:
                sub_resp = await http.get(sub_url)
                sub_resp.raise_for_status()
                sub_root = ElementTree.fromstring(sub_resp.content)
                for url_el in sub_root.findall("sm:url/sm:loc", ns):
                    loc = (url_el.text or "").strip()
                    if NAWY_COMPOUND_PATTERN.match(loc):
                        urls.append(loc)
            except Exception as sub_exc:
                logger.warning("[discovery] Sub-sitemap %s fetch failed: %s", sub_url, sub_exc)
    else:
        # Flat sitemap
        for url_el in root.findall("sm:url/sm:loc", ns):
            loc = (url_el.text or "").strip()
            if NAWY_COMPOUND_PATTERN.match(loc):
                urls.append(loc)

    logger.info("[discovery] Sitemap yielded %d compound URLs", len(urls))
    return list(set(urls))


async def _fetch_search_api_urls(http: httpx.AsyncClient) -> list[str]:
    """
    Augments sitemap discovery by paginating Nawy's /compounds search pages.

    Strategy: GET /compounds?page=N, extract __NEXT_DATA__ JSON from the page
    source (no browser needed — server-side rendered), collect compound hrefs.

    This catches compounds not yet in the sitemap (new listings).

    Returns:
        List of compound URLs discovered via search pagination.
    """
    urls: list[str] = []
    compound_url_pattern = re.compile(r'/compounds?/[^"\'>\s]+')

    for page_num in range(1, MAX_DISCOVERY_PAGES + 1):
        try:
            resp = await http.get(
                f"{NAWY_BASE_URL}/compounds",
                params={"page": page_num},
            )
            if resp.status_code == 404:
                break

            # Extract __NEXT_DATA__ via regex (faster than a full HTML parser)
            match = re.search(
                r'<script id="__NEXT_DATA__"[^>]*>(.+?)</script>',
                resp.text,
                re.DOTALL,
            )
            if not match:
                logger.debug("[discovery] No __NEXT_DATA__ on /compounds page %d", page_num)
                break

            import json as _json
            page_data = _json.loads(match.group(1))
            page_props = page_data.get("props", {}).get("pageProps", {})

            # Collect compound slugs/URLs from the pageProps
            found_on_page: list[str] = []
            raw_text = _json.dumps(page_props)
            for m in compound_url_pattern.finditer(raw_text):
                slug = m.group(0).strip('/"\'')
                if slug and not slug.endswith(".jpg") and not slug.endswith(".png"):
                    full_url = f"{NAWY_BASE_URL}/{slug.lstrip('/')}"
                    if NAWY_COMPOUND_PATTERN.match(full_url):
                        found_on_page.append(full_url)

            if not found_on_page:
                logger.info("[discovery] No new compounds on page %d — stopping pagination", page_num)
                break

            urls.extend(found_on_page)
            logger.debug("[discovery] Page %d: %d URLs", page_num, len(found_on_page))

        except Exception as exc:
            logger.warning("[discovery] Error on /compounds page %d: %s", page_num, exc)
            break

    logger.info("[discovery] Search pagination yielded %d compound URLs", len(urls))
    return list(set(urls))


async def discover_compound_urls(http: httpx.AsyncClient) -> list[str]:
    """
    Master URL discovery: sitemap + search pagination fallback.

    Returns deduplicated list of Nawy compound detail URLs.
    """
    sitemap_urls = await _fetch_sitemap_urls(http)
    all_urls = list(set(sitemap_urls))

    if len(all_urls) < 100:
        logger.info(
            "[discovery] Sitemap only yielded %d URLs — augmenting with search pagination",
            len(all_urls),
        )
        search_urls = await _fetch_search_api_urls(http)
        all_urls = list(set(all_urls + search_urls))

    logger.info("[discovery] Total unique compound URLs discovered: %d", len(all_urls))
    return all_urls


async def filter_new_urls(all_urls: list[str]) -> list[str]:
    """
    Filters discovered URLs to only those that need scraping:
      - URLs not yet in the DB (never scraped), OR
      - URLs whose scraped_at is older than RESCRAPE_DAYS

    Runs a single DB query to avoid N+1 performance issues.

    Args:
        all_urls: Full list of discovered compound URLs.

    Returns:
        Filtered list of URLs to enqueue for scraping.
    """
    if not all_urls:
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=RESCRAPE_DAYS)

    async with AsyncSessionLocal() as db:
        # Get nawy_url + scraped_at for all URLs in the discovered set
        rows = await db.execute(
            select(Property.nawy_url, Property.scraped_at).where(
                Property.nawy_url.in_(all_urls)
            )
        )
        existing: dict[str, Any] = {row.nawy_url: row.scraped_at for row in rows}

    to_scrape: list[str] = []
    for url in all_urls:
        if url not in existing:
            to_scrape.append(url)  # Never scraped
        elif existing[url] is None or existing[url] < cutoff:
            to_scrape.append(url)  # Stale

    logger.info(
        "[discovery] %d URLs to scrape (%d new, %d stale) out of %d total",
        len(to_scrape),
        sum(1 for u in to_scrape if u not in existing),
        sum(1 for u in to_scrape if u in existing),
        len(all_urls),
    )
    return to_scrape


# ─────────────────────────────────────────────────────────────────────────────
# ARQ Tasks
# ─────────────────────────────────────────────────────────────────────────────

async def master_discovery_job(ctx: dict) -> dict:
    """
    ARQ cron task: Discovers new/stale compound URLs and enqueues scrape tasks.

    Schedule: Every Sunday at 02:00 UTC (see WorkerSettings.cron_jobs).

    Flow:
      1. Discover all compound URLs (sitemap + pagination)
      2. Filter against DB to find new/stale entries
      3. Register a new scrape_run_id in Redis (for stale cleanup)
      4. Enqueue one scrape_compound_task per URL

    Returns:
        {"discovered": N, "queued": M, "run_id": "..."}
    """
    http: httpx.AsyncClient = ctx["http"]
    run_id = str(uuid.uuid4())

    logger.info("[master] Starting discovery job — run_id=%s", run_id)

    all_urls = await discover_compound_urls(http)
    urls_to_scrape = await filter_new_urls(all_urls)

    # Register run_id before queuing (stale cleanup uses this)
    register_scrape_run_id(run_id)

    # Enqueue individual scrape tasks via ARQ Redis pool
    redis = ctx["redis"]
    queued = 0
    for url in urls_to_scrape:
        await redis.enqueue_job(
            "scrape_compound_task",
            compound_url=url,
            run_id=run_id,
            _job_id=f"scrape:{url}",  # Deduplicate in case of double-queue
        )
        queued += 1

    result = {
        "discovered": len(all_urls),
        "queued": queued,
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    logger.info("[master] Discovery complete: %s", result)
    return result


async def scrape_compound_task(
    ctx: dict,
    compound_url: str,
    run_id: str,
) -> dict:
    """
    ARQ task: End-to-end pipeline for one compound URL.

    Pipeline:
      1. core_scraper.scrape_compound()      → raw JSON dict
      2. llm_normalizer.normalize_properties() → NormalizationResult
      3. repository.upsert_properties()       → UpsertResult (hash-differential)

    Retry policy: ARQ retries on exception up to job_timeout (300s).
    ScraperError after 3 internal Tenacity retries propagates here and marks
    the ARQ job as failed (visible in result store for debugging).

    Args:
        compound_url: Full Nawy.com compound URL.
        run_id:       UUID from the master discovery job (for stale tracking).

    Returns:
        {
          "url": ...,
          "scraped": N,    # Units extracted by scraper
          "normalized": M, # Units successfully LLM-normalized
          "upserted": K,   # DB insertions + updates
          "skipped": J,    # Hash-unchanged, no DB write
          "errors": E
        }
    """
    logger.info("[task] Starting scrape_compound_task for %s (run=%s)", compound_url, run_id)

    try:
        # Step 1: Scrape
        raw_json = await scrape_compound(compound_url)
        logger.debug("[task] Scrape complete for %s", compound_url)

    except ScraperError as exc:
        logger.error("[task] Scraper failed for %s: %s", compound_url, exc)
        return {
            "url": compound_url,
            "scraped": 0,
            "normalized": 0,
            "upserted": 0,
            "skipped": 0,
            "errors": 1,
            "error": str(exc),
        }

    # Step 2: Normalize
    norm_result = await normalize_properties(raw_json)
    logger.info(
        "[task] Normalized %d properties for %s (skipped=%d)",
        len(norm_result.properties),
        compound_url,
        norm_result.skipped_count,
    )

    if not norm_result.properties:
        return {
            "url": compound_url,
            "scraped": 1,
            "normalized": 0,
            "upserted": 0,
            "skipped": 0,
            "errors": norm_result.skipped_count,
            "error": "; ".join(norm_result.errors[:3]),
        }

    # Step 3: Upsert with differential hash
    upsert_result = await upsert_properties(norm_result.properties, run_id)

    result = {
        "url": compound_url,
        "scraped": 1,
        "normalized": len(norm_result.properties),
        "upserted": upsert_result.inserted + upsert_result.updated,
        "skipped": upsert_result.skipped,
        "errors": upsert_result.errors + norm_result.skipped_count,
    }
    logger.info("[task] Complete for %s: %s", compound_url, result)
    return result


async def mark_stale_job(ctx: dict) -> dict:
    """
    ARQ cron task: Marks properties absent from the latest scrape as unavailable.
    Schedule: Every Sunday at 06:00 UTC.

    Delegates to the existing mark_stale_properties() in nawy_scraper.py.
    """
    logger.info("[cron] Running mark_stale_job")
    result = await mark_stale_properties()
    logger.info("[cron] mark_stale_job complete: %s", result)
    return result


async def price_flag_job(ctx: dict) -> dict:
    """
    ARQ cron task: Flags properties priced significantly above/below zone average.
    Schedule: Every Sunday at 06:30 UTC.

    Delegates to the existing flag_underpriced_properties() in nawy_scraper.py.
    """
    logger.info("[cron] Running price_flag_job")
    result = await flag_underpriced_properties()
    logger.info("[cron] price_flag_job complete: %s", result)
    return result


async def geopolitical_scraper_job(ctx: dict) -> dict:
    """
    ARQ cron task: Scrapes geopolitical/macro events affecting Egyptian real estate.
    Schedule: Daily at 04:00 UTC.

    Delegates to the existing geopolitical_scraper service.
    """
    logger.info("[cron] Running geopolitical_scraper_job")
    try:
        from app.services.geopolitical_scraper import run_geopolitical_scraper
        result = await run_geopolitical_scraper()
        logger.info("[cron] geopolitical_scraper_job complete: %s", result)
        return result if isinstance(result, dict) else {"status": "complete"}
    except Exception as exc:
        logger.error("[cron] geopolitical_scraper_job failed: %s", exc)
        return {"status": "error", "error": str(exc)}


# ─────────────────────────────────────────────────────────────────────────────
# ARQ WorkerSettings
# ─────────────────────────────────────────────────────────────────────────────

class WorkerSettings:
    """
    ARQ reads this class to configure the worker process.

    Start the worker:
        python -m arq app.ingestion.worker.WorkerSettings

    Docker Compose (alongside the FastAPI 'web' service):
        arq-worker:
          command: python -m arq app.ingestion.worker.WorkerSettings
          env_file: .env
          restart: unless-stopped
          depends_on:
            - redis
            - db

    Environment variables:
        REDIS_URL              — Redis connection string (default: redis://localhost:6379/0)
        NAWY_RESCRAPE_DAYS     — Days before re-scraping existing compounds (default: 7)
        MAX_UNITS_PER_COMPOUND — LLM cost cap per compound (default: 30)
        INGESTION_MAX_JOBS     — Concurrent ARQ tasks (default: 10)
        PROXY_LIST             — Comma-separated proxy URLs for Playwright rotation
    """

    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_URL", "redis://localhost:6379/0")
    )

    functions = [
        scrape_compound_task,
        master_discovery_job,
        mark_stale_job,
        price_flag_job,
        geopolitical_scraper_job,
    ]

    on_startup = startup
    on_shutdown = shutdown

    # ── Concurrency & Timeouts ────────────────────────────────────────────────
    max_jobs = int(os.getenv("INGESTION_MAX_JOBS", "10"))
    # Per-task timeout: Playwright navigation + LLM calls can take up to 5 min
    job_timeout = 300   # seconds
    # How long to keep task results in Redis (for debugging)
    keep_result = 3600  # 1 hour
    # Poll interval for checking new jobs in queue
    poll_delay = 0.5    # seconds

    # ── Cron Schedule ─────────────────────────────────────────────────────────
    cron_jobs = [
        # Sunday 02:00 UTC — discover + enqueue all compound scrape tasks
        cron(master_discovery_job, weekday=6, hour=2, minute=0, unique=True),
        # Sunday 06:00 UTC — mark properties absent from latest run as unavailable
        cron(mark_stale_job, weekday=6, hour=6, minute=0, unique=True),
        # Sunday 06:30 UTC — flag above/below-average priced properties
        cron(price_flag_job, weekday=6, hour=6, minute=30, unique=True),
        # Daily 04:00 UTC — geopolitical/macro events scraping
        cron(geopolitical_scraper_job, hour=4, minute=0, unique=True),
    ]
