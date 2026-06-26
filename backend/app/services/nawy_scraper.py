"""
Nawy Scraper Service — Post-Processing + On-Demand Scraping
-------------------------------------------------------------
Provides:
  - run_nawy_scrape():  httpx-based __NEXT_DATA__ extraction → LLM normalize → upsert
  - mark_stale_properties():  flag properties missing from recent runs
  - flag_underpriced_properties():  flag outlier price/sqm
  - register_scrape_run_id():  push run_id into Redis 2-slot window

The scheduled scraping pipeline uses:
  - PRIMARY: nawy_scraper_v2.py (Railway Cron container, runs Sundays 03:00 UTC)
  - ADVANCED: backend/app/ingestion/worker.py (ARQ async worker, optional)
"""

import asyncio
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

import httpx

from app.services.cache import cache

logger = logging.getLogger(__name__)

# Nawy sitemap / compound URL patterns
_NAWY_BASE = "https://www.nawy.com"
_NAWY_SITEMAP = f"{_NAWY_BASE}/sitemap.xml"
_COMPOUND_RE = re.compile(r"https://www\.nawy\.com/compounds?/[^/\s]+$")
_NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__"[^>]*>(.+?)</script>', re.DOTALL
)

# Politeness / resilience knobs
_FETCH_DELAY_SECONDS = 1.0          # pause between compound fetches
_MAX_CONSECUTIVE_429 = 5            # abort the run if Nawy keeps throttling
_RETRY_AFTER_FALLBACK_SECONDS = 30  # backoff when 429 has no Retry-After header


def _extract_next_data(html: str) -> Optional[dict]:
    """
    Extract and parse the __NEXT_DATA__ SSR payload from page HTML.

    Prefers a real HTML parse (robust to attribute reordering / formatting
    changes) and falls back to the legacy regex. Validates the parsed JSON
    has the expected Next.js shape so structure drift fails loudly here
    instead of producing empty batches downstream.
    """
    raw: Optional[str] = None
    try:
        from bs4 import BeautifulSoup

        tag = BeautifulSoup(html, "html.parser").find("script", id="__NEXT_DATA__")
        if tag and tag.string:
            raw = tag.string
    except Exception as exc:
        logger.debug("[scrape] bs4 NEXT_DATA parse failed (%s); trying regex", exc)

    if raw is None:
        m = _NEXT_DATA_RE.search(html)
        if not m:
            return None
        raw = m.group(1)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("[scrape] __NEXT_DATA__ is not valid JSON: %s", exc)
        return None

    # Schema sanity check: Next.js always nests page data under props.pageProps
    if not isinstance(data, dict) or "props" not in data:
        logger.warning(
            "[scrape] __NEXT_DATA__ shape changed (missing 'props' key) — "
            "Nawy may have restructured their build; extraction needs review."
        )
        return None
    return data

_REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
}


# ═══════════════════════════════════════════════════════════════
# ON-DEMAND NAWY SCRAPE (httpx — no Playwright needed)
# ═══════════════════════════════════════════════════════════════

async def _discover_compound_urls_httpx(client: httpx.AsyncClient) -> list[str]:
    """Discover compound URLs from Nawy sitemap + search pagination."""
    from xml.etree import ElementTree

    urls: list[str] = []
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    # --- Sitemap ---
    try:
        resp = await client.get(_NAWY_SITEMAP)
        resp.raise_for_status()
        root = ElementTree.fromstring(resp.content)

        sub_sitemaps = root.findall("sm:sitemap/sm:loc", ns)
        if sub_sitemaps:
            for loc_el in sub_sitemaps:
                sub_url = (loc_el.text or "").strip()
                if not sub_url:
                    continue
                try:
                    sub_resp = await client.get(sub_url)
                    sub_resp.raise_for_status()
                    sub_root = ElementTree.fromstring(sub_resp.content)
                    for url_el in sub_root.findall("sm:url/sm:loc", ns):
                        loc = (url_el.text or "").strip()
                        if _COMPOUND_RE.match(loc):
                            urls.append(loc)
                except Exception:
                    pass
        else:
            for url_el in root.findall("sm:url/sm:loc", ns):
                loc = (url_el.text or "").strip()
                if _COMPOUND_RE.match(loc):
                    urls.append(loc)
    except Exception as exc:
        logger.warning("[scrape] Sitemap fetch failed: %s", exc)

    # --- Search pagination fallback ---
    if len(set(urls)) < 100:
        for page_num in range(1, 50):
            try:
                resp = await client.get(
                    f"{_NAWY_BASE}/compounds", params={"page": page_num}
                )
                if resp.status_code == 404:
                    break
                page_data = _extract_next_data(resp.text)
                if not page_data:
                    break
                raw_text = json.dumps(page_data.get("props", {}).get("pageProps", {}))
                found = [
                    f"{_NAWY_BASE}/{slug.lstrip('/')}"
                    for slug in re.findall(r'/compounds?/[^"\'>\\s]+', raw_text)
                    if not slug.endswith((".jpg", ".png"))
                ]
                found = [u for u in found if _COMPOUND_RE.match(u)]
                if not found:
                    break
                urls.extend(found)
            except Exception:
                break

    unique = list(set(urls))
    logger.info("[scrape] Discovered %d compound URLs", len(unique))
    return unique


async def run_nawy_scrape() -> dict:
    """
    Run a full Nawy property scrape using httpx (no Playwright/Chromium needed).

    For each compound URL:
      1. HTTP GET → extract __NEXT_DATA__ JSON from server-rendered HTML
      2. LLM normalizer → structured NormalizedProperty list
      3. Hash-differential upsert into PostgreSQL

    Returns summary dict with counts.
    """
    from app.ingestion.llm_normalizer import normalize_properties
    from app.ingestion.repository import upsert_properties

    run_id = str(uuid.uuid4())
    register_scrape_run_id(run_id)

    stats = {
        "run_id": run_id,
        "compounds_found": 0,
        "compounds_scraped": 0,
        "properties_normalized": 0,
        "upserted": 0,
        "skipped": 0,
        "errors": 0,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(30.0, connect=10.0),
        headers=_REQUEST_HEADERS,
        follow_redirects=True,
    ) as client:
        compound_urls = await _discover_compound_urls_httpx(client)
        stats["compounds_found"] = len(compound_urls)

        consecutive_429 = 0
        for i, url in enumerate(compound_urls):
            await asyncio.sleep(_FETCH_DELAY_SECONDS)
            try:
                resp = await client.get(url)

                # Honor throttling: back off on 429 instead of hammering on
                if resp.status_code == 429:
                    consecutive_429 += 1
                    if consecutive_429 >= _MAX_CONSECUTIVE_429:
                        logger.error(
                            "[scrape] %d consecutive 429s — aborting run to avoid IP block",
                            consecutive_429,
                        )
                        stats["errors"] += len(compound_urls) - i
                        break
                    retry_after = resp.headers.get("Retry-After")
                    wait = (
                        int(retry_after)
                        if retry_after and retry_after.isdigit()
                        else _RETRY_AFTER_FALLBACK_SECONDS * consecutive_429
                    )
                    logger.warning(
                        "[scrape] 429 from Nawy (streak=%d) — backing off %ds",
                        consecutive_429, wait,
                    )
                    await asyncio.sleep(wait)
                    stats["errors"] += 1
                    continue
                consecutive_429 = 0

                if resp.status_code != 200:
                    stats["errors"] += 1
                    continue

                raw_json = _extract_next_data(resp.text)
                if not raw_json:
                    stats["errors"] += 1
                    continue
                raw_json["_meta"] = {
                    "source_url": url,
                    "strategy": "httpx_next_data",
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                }

                norm_result = await normalize_properties(raw_json)
                if not norm_result.properties:
                    stats["errors"] += 1
                    continue

                upsert_result = await upsert_properties(norm_result.properties, run_id)

                stats["compounds_scraped"] += 1
                stats["properties_normalized"] += len(norm_result.properties)
                stats["upserted"] += upsert_result.inserted + upsert_result.updated
                stats["skipped"] += upsert_result.skipped

                if (i + 1) % 20 == 0:
                    logger.info(
                        "[scrape] Progress: %d/%d compounds — %d properties so far",
                        i + 1, len(compound_urls), stats["properties_normalized"],
                    )

            except Exception as exc:
                logger.warning("[scrape] Error on %s: %s", url, exc)
                stats["errors"] += 1

    # Post-processing
    stale = await mark_stale_properties()
    price = await flag_underpriced_properties()
    stats["stale_marked"] = stale.get("stale_marked", 0)
    stats["price_flagged"] = price.get("flagged", 0)
    stats["finished_at"] = datetime.now(timezone.utc).isoformat()

    logger.info("[scrape] Scrape complete: %s", stats)

    # Alert operators when the run looks unhealthy (high failure share means
    # Nawy structure drift or throttling — needs a human before data goes stale)
    attempted = stats["compounds_found"]
    if attempted and stats["errors"] / attempted > 0.5:
        try:
            from app.ingestion.anomaly_detector import send_alert
            await send_alert(
                title=f"Nawy Scrape Unhealthy (run {run_id[:8]})",
                message=(
                    f"{stats['errors']}/{attempted} compounds failed "
                    f"({stats['errors'] / attempted:.0%}). "
                    f"Scraped={stats['compounds_scraped']}, "
                    f"upserted={stats['upserted']}. Check for Nawy structure "
                    f"changes or IP throttling."
                ),
                severity="warning",
            )
        except Exception as alert_err:
            logger.warning("[scrape] Health alert failed (non-fatal): %s", alert_err)

    return stats


# ═══════════════════════════════════════════════════════════════
# STALE PROPERTY CLEANUP
# ═══════════════════════════════════════════════════════════════

async def mark_stale_properties():
    """
    Mark properties as unavailable if they weren't seen in the last two scrape runs.

    Reads the current/previous scrape_run_id from Redis (set by nawy_scraper_v2.py
    after each successful run). Any property whose last_scrape_run_id is not in
    {current, previous} gets marked is_available=False.

    The 2-run window prevents one failed scrape from mass-delisting properties.

    WRITE GATE (Phase 0 / catalog-wipe guard): unless
    config.SCRAPER_STALE_CLEANUP_ENABLED is true, this runs in DRY-RUN mode — it
    logs how many rows it WOULD delist but does not write. This prevents a
    misconfigured run_id window (partial crawl, per-area registration, empty ARQ
    run, serialization mismatch) from silently wiping the served catalog. Flip
    SCRAPER_STALE_CLEANUP_ENABLED=true only after reviewing dry-run counts AND
    landing the rest of the Phase-0 entrypoint gates.
    """
    from app.database import AsyncSessionLocal
    from sqlalchemy import text, bindparam
    from app.config import config

    current_run = cache.get("scraper:run_id:current")
    previous_run = cache.get("scraper:run_id:previous")

    if not current_run:
        logger.warning("[STALE] No current scrape_run_id found in Redis — skipping cleanup")
        return {"stale_marked": 0}

    safe_runs = [current_run]
    if previous_run:
        safe_runs.append(previous_run)

    enabled = config.SCRAPER_STALE_CLEANUP_ENABLED
    logger.info(
        "[STALE] %s mode. Keeping runs: %s",
        "WRITE" if enabled else "DRY-RUN",
        safe_runs,
    )

    # A tuple bound to `NOT IN :safe_runs` renders as a single ROW(...) under
    # asyncpg and errors / mis-targets; use an expanding bindparam + list so the
    # dry-run count is trustworthy and the gated write targets the right rows.
    where_clause = (
        "is_available = true "
        "AND last_scrape_run_id IS NOT NULL "
        "AND last_scrape_run_id NOT IN :safe_runs"
    )

    async with AsyncSessionLocal() as db:
        count_stmt = text(
            f"SELECT count(*) FROM properties WHERE {where_clause}"
        ).bindparams(bindparam("safe_runs", expanding=True))
        would_mark = (
            await db.execute(count_stmt, {"safe_runs": safe_runs})
        ).scalar() or 0

        if not enabled:
            logger.warning(
                "[STALE] DRY-RUN: would mark %d properties unavailable. "
                "Set SCRAPER_STALE_CLEANUP_ENABLED=true to enable writes once the "
                "Phase-0 run_id gates are in place. Keeping runs: %s",
                would_mark,
                safe_runs,
            )
            return {"stale_marked": 0, "would_mark": would_mark, "dry_run": True}

        update_stmt = text(
            f"UPDATE properties SET is_available = false WHERE {where_clause}"
        ).bindparams(bindparam("safe_runs", expanding=True))
        result = await db.execute(update_stmt, {"safe_runs": safe_runs})
        await db.commit()
        count = result.rowcount
        logger.info(
            "[STALE] Marked %d properties as unavailable (would_mark=%d)",
            count,
            would_mark,
        )
        return {"stale_marked": count, "would_mark": would_mark, "dry_run": False}


def register_scrape_run_id(run_id: str):
    """
    Push a new scrape_run_id into the 2-slot Redis window.
    Called by nawy_scraper_v2.py (via direct Redis write) and
    by the ARQ worker's master_discovery_job.
    """
    previous = cache.get("scraper:run_id:current")
    if previous:
        cache.set("scraper:run_id:previous", previous, ttl=604800)  # 7 days
    cache.set("scraper:run_id:current", run_id, ttl=604800)


# ═══════════════════════════════════════════════════════════════
# CROSS-DB PRICE VALIDATION
# ═══════════════════════════════════════════════════════════════

async def flag_underpriced_properties(threshold_pct: float = 0.40):
    """
    Compare each available property's price_per_sqm against its location average.

    Sets price_flag:
      - 'below_area_avg': > threshold_pct below the location mean (potential bargain or data error)
      - 'above_area_avg': > threshold_pct above the location mean
      - None: within normal range

    This powers the proactive_alerts.py la2ta (bargain) detector.
    """
    from app.database import AsyncSessionLocal
    from sqlalchemy import text

    async with AsyncSessionLocal() as db:
        # 1. Compute location averages
        avgs = await db.execute(text("""
            SELECT location, AVG(price / NULLIF(size_sqm, 0)) AS avg_psm
            FROM properties
            WHERE is_available = true
              AND price > 0
              AND size_sqm > 0
            GROUP BY location
        """))
        location_avgs = {row[0]: row[1] for row in avgs.fetchall() if row[1]}

        if not location_avgs:
            logger.info("[PRICE] No location averages — skipping")
            return {"flagged": 0}

        # 2. Flag properties
        flagged = 0
        props = await db.execute(text("""
            SELECT id, location, price, size_sqm
            FROM properties
            WHERE is_available = true
              AND price > 0
              AND size_sqm > 0
        """))
        for prop_id, location, price, size in props.fetchall():
            avg = location_avgs.get(location)
            if not avg:
                continue
            psm = price / size
            ratio = psm / avg

            if ratio < (1 - threshold_pct):
                flag = "below_area_avg"
            elif ratio > (1 + threshold_pct):
                flag = "above_area_avg"
            else:
                flag = None

            await db.execute(
                text("UPDATE properties SET price_flag = :flag WHERE id = :id"),
                {"flag": flag, "id": prop_id},
            )
            if flag:
                flagged += 1

        await db.commit()
        logger.info(f"[PRICE] Flagged {flagged} properties")
        return {"flagged": flagged}
