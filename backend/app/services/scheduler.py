"""
Osool Scheduled Tasks
---------------------
APScheduler-based weekly cron jobs for data ingestion.

Jobs:
1. Property Scraper (Nawy) — Sundays at 03:00 UTC
2. Economic Indicators — Sundays at 03:30 UTC

Runs in-process with the FastAPI app. No separate worker needed.
"""

import logging
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="UTC")


async def run_property_scraper():
    """Weekly property scraper job."""
    logger.info("⏰ [CRON] Starting weekly property scraper...")
    try:
        from app.services.nawy_scraper import ingest_nawy_data_async
        result = await ingest_nawy_data_async()
        logger.info(f"✅ [CRON] Property scraper completed: {result}")
    except Exception as e:
        logger.error(f"❌ [CRON] Property scraper failed: {e}")


async def run_economic_scraper():
    """Weekly economic indicators scraper job."""
    logger.info("⏰ [CRON] Starting weekly economic scraper...")
    try:
        from app.database import AsyncSessionLocal
        from app.services.economic_scraper import update_market_indicators

        async with AsyncSessionLocal() as db:
            result = await update_market_indicators(db)
            logger.info(f"✅ [CRON] Economic scraper completed: {result.get('updated', 0)} indicators updated")
    except Exception as e:
        logger.error(f"❌ [CRON] Economic scraper failed: {e}")


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

    scheduler.start()
    logger.info("✅ APScheduler started with weekly cron jobs:")
    logger.info("   📅 Property Scraper: Sundays 03:00 UTC")
    logger.info("   📅 Economic Scraper: Sundays 03:30 UTC")

    # Log next run times
    for job in scheduler.get_jobs():
        logger.info(f"   Next run for '{job.name}': {job.next_run_time}")


def shutdown_scheduler():
    """Gracefully stop the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("⏹️ APScheduler shut down")
