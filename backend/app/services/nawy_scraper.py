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

import json
import logging
import re
import uuid
from datetime import datetime, timezone

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
                m = _NEXT_DATA_RE.search(resp.text)
                if not m:
                    break
                page_data = json.loads(m.group(1))
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

        for i, url in enumerate(compound_urls):
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    stats["errors"] += 1
                    continue

                m = _NEXT_DATA_RE.search(resp.text)
                if not m:
                    stats["errors"] += 1
                    continue

                raw_json = json.loads(m.group(1))
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
    """
    from app.database import AsyncSessionLocal
    from sqlalchemy import text

    current_run = cache.get("scraper:run_id:current")
    previous_run = cache.get("scraper:run_id:previous")

    if not current_run:
        logger.warning("[STALE] No current scrape_run_id found in Redis — skipping cleanup")
        return {"stale_marked": 0}

    safe_runs = [current_run]
    if previous_run:
        safe_runs.append(previous_run)

    logger.info(f"[STALE] Marking properties stale. Keeping runs: {safe_runs}")

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("""
                UPDATE properties
                SET is_available = false
                WHERE is_available = true
                  AND last_scrape_run_id IS NOT NULL
                  AND last_scrape_run_id NOT IN :safe_runs
            """),
            {"safe_runs": tuple(safe_runs)},
        )
        await db.commit()
        count = result.rowcount
        logger.info(f"[STALE] Marked {count} properties as unavailable")
        return {"stale_marked": count}


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
