"""
Osool Scheduled Tasks
---------------------
APScheduler-based cron jobs for data ingestion.

Jobs:
1. Property Scraper (Nawy) — Sundays at 03:00 UTC
2. Economic Indicators — Sundays at 03:30 UTC
3. Geopolitical Events — Daily at 04:00 UTC
4. Image Mirror — Sundays at 05:00 UTC

Runs in-process with the FastAPI app. No separate worker needed.
"""

import logging
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from tenacity import retry, stop_after_attempt, wait_exponential
import httpx

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="UTC")

ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")


async def _notify_orchestrator(event_type: str, payload: dict):
    """Fire-and-forget POST to the Orchestrator scraper-event webhook."""
    if not ORCHESTRATOR_URL:
        return
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                f"{ORCHESTRATOR_URL}/webhooks/scraper-event",
                json={"eventType": event_type, **payload},
                headers={"X-Webhook-Secret": WEBHOOK_SECRET, "Content-Type": "application/json"},
            )
        logger.info(f"[NOTIFY] Sent {event_type} to Orchestrator")
    except Exception as e:
        logger.warning(f"[NOTIFY] Failed to notify Orchestrator: {e}")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=60, max=600), reraise=True)
async def run_property_scraper():
    """Weekly property scraper job with retry + stale cleanup."""
    logger.info("[CRON] Starting weekly property scraper...")
    try:
        from app.services.nawy_scraper import ingest_nawy_data_async, mark_stale_properties, flag_underpriced_properties
        result = await ingest_nawy_data_async()
        logger.info(f"[CRON] Property scraper completed: {result}")

        # Clean up stale properties not seen in last 2 runs
        stale_result = await mark_stale_properties()
        logger.info(f"[CRON] Stale cleanup: {stale_result.get('stale_marked', 0)} marked unavailable")

        # Cross-DB price validation
        price_result = await flag_underpriced_properties()
        logger.info(f"[CRON] Price validation: {price_result.get('flagged', 0)} flagged")

        # Notify Orchestrator for SEO content refresh
        await _notify_orchestrator("property_scrape_complete", {
            "significantChanges": stale_result.get("stale_marked", 0),
        })
    except Exception as e:
        logger.error(f"[CRON] Property scraper failed: {e}")
        raise  # Let tenacity retry


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=60, max=600), reraise=True)
async def run_economic_scraper():
    """Weekly economic indicators scraper job with retry."""
    logger.info("[CRON] Starting weekly economic scraper...")
    try:
        from app.database import AsyncSessionLocal
        from app.services.economic_scraper import update_market_indicators

        async with AsyncSessionLocal() as db:
            result = await update_market_indicators(db)
            logger.info(f"[CRON] Economic scraper completed: {result.get('updated', 0)} indicators updated")

            # Notify Orchestrator for SEO content refresh
            await _notify_orchestrator("economic_update", {
                "indicators": result.get("indicators", {}),
            })
    except Exception as e:
        logger.error(f"[CRON] Economic scraper failed: {e}")
        raise


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=60, max=600), reraise=True)
async def run_geopolitical_scraper():
    """Daily geopolitical & macroeconomic event scraper job with retry."""
    logger.info("[CRON] Starting daily geopolitical scraper...")
    try:
        from app.database import AsyncSessionLocal
        from app.services.geopolitical_scraper import scrape_geopolitical_events

        async with AsyncSessionLocal() as db:
            result = await scrape_geopolitical_events(db, use_llm=True)
            logger.info(
                f"[CRON] Geopolitical scraper completed: "
                f"stored={result.get('stored', 0)}, relevant={result.get('relevant', 0)}"
            )

            # Notify Orchestrator if significant events were stored
            if result.get("stored", 0) > 0:
                await _notify_orchestrator("geopolitical_shift", {
                    "significantChanges": result.get("stored", 0),
                })
    except Exception as e:
        logger.error(f"[CRON] Geopolitical scraper failed: {e}")
        raise


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=60, max=300), reraise=True)
async def run_image_mirror():
    """Weekly image mirroring job — mirrors Nawy CDN images to S3."""
    logger.info("[CRON] Starting image mirror job...")
    try:
        from app.services.image_mirror import mirror_property_images
        result = await mirror_property_images(batch_size=100)
        logger.info(f"[CRON] Image mirror completed: {result}")
    except Exception as e:
        logger.error(f"[CRON] Image mirror failed: {e}")
        raise

@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=60, max=300), reraise=True)
async def run_marketing_generator():
    """Bi-weekly marketing material generation AI job."""
    logger.info("[CRON] Starting marketing materials generation job...")
    try:
        from app.database import AsyncSessionLocal
        from app.services.marketing_generator import generate_marketing_answers
        async with AsyncSessionLocal() as db:
            result = await generate_marketing_answers(db)
            logger.info(f"[CRON] Marketing materials generation completed: updated={result}")
    except Exception as e:
        logger.error(f"[CRON] Marketing materials generation failed: {e}")
        raise

def init_scheduler():
    """
    Initialize and start the APScheduler with weekly cron jobs.
    Called once during FastAPI startup.
    """
    # Property scraper: Every Sunday at 03:00 UTC
    scheduler.add_job(
        run_property_scraper,
        trigger=CronTrigger(day_of_week="sun", hour=3, minute=0),
        id="weekly_property_scraper",
        name="Weekly Nawy Property Scraper",
        replace_existing=True,
        misfire_grace_time=3600,  # Allow 1 hour grace period
    )

    # Economic scraper: Every Sunday at 03:30 UTC
    scheduler.add_job(
        run_economic_scraper,
        trigger=CronTrigger(day_of_week="sun", hour=3, minute=30),
        id="weekly_economic_scraper",
        name="Weekly Economic Indicators Scraper",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    # Geopolitical scraper: Daily at 04:00 UTC
    scheduler.add_job(
        run_geopolitical_scraper,
        trigger=CronTrigger(hour=4, minute=0),
        id="daily_geopolitical_scraper",
        name="Daily Geopolitical Events Scraper",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    # Image mirror: Every Sunday at 05:00 UTC (after property scraper)
    scheduler.add_job(
        run_image_mirror,
        trigger=CronTrigger(day_of_week="sun", hour=5, minute=0),
        id="weekly_image_mirror",
        name="Weekly Image Mirror to S3",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    # Marketing Material Generation: Bi-weekly (1st and 15th of the month) at 06:00 UTC
    scheduler.add_job(
        run_marketing_generator,
        trigger=CronTrigger(day="1,15", hour=6, minute=0),
        id="biweekly_marketing_generator",
        name="Bi-weekly AI Marketing Answers Generator",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    scheduler.start()
    logger.info("✅ APScheduler started with cron jobs:")
    logger.info("   📅 Property Scraper: Sundays 03:00 UTC")
    logger.info("   📅 Economic Scraper: Sundays 03:30 UTC")
    logger.info("   📅 Geopolitical Scraper: Daily 04:00 UTC")
    logger.info("   📅 Image Mirror: Sundays 05:00 UTC")
    logger.info("   📅 Marketing Generator: 1st/15th 06:00 UTC")

    # Log next run times
    for job in scheduler.get_jobs():
        logger.info(f"   Next run for '{job.name}': {job.next_run_time}")


def shutdown_scheduler():
    """Gracefully stop the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("⏹️ APScheduler shut down")
