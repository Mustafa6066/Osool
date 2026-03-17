"""
Nawy Scraper Service — Post-Processing Utilities
-------------------------------------------------
This module no longer handles property scraping.
The scraping pipeline is:
  - PRIMARY: nawy_scraper_v2.py (Railway Cron container, runs Sundays 03:00 UTC)
  - ADVANCED: backend/app/ingestion/worker.py (ARQ async worker, optional)

This module provides three post-processing utilities called by:
  1. APScheduler (scheduler.py — run_post_scrape_processing, Sundays 04:30 UTC)
  2. Admin API (admin_endpoints.py — manual trigger endpoints)
  3. ARQ worker (ingestion/worker.py — mark_stale_job, price_flag_job)
"""

import logging
from app.services.cache import cache

logger = logging.getLogger(__name__)


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
