"""
Osool Scheduled Tasks
---------------------
APScheduler-based cron jobs for data ingestion and post-processing.

Jobs:
1. Post-Scrape Processing — Sundays at 04:30 UTC
   Stale property cleanup + price flagging + orchestrator notification.
   Runs AFTER the Railway Cron scraper container (which runs at 03:00 UTC).
   The actual property scraping is handled by nawy_scraper_v2.py via Railway Cron.

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

_scheduler_lock_fd = None
_scheduler_lock_owner = False
_scheduler_lock_path = os.getenv("SCHEDULER_LOCK_FILE", "/tmp/osool_apscheduler.lock")

ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")


def _acquire_scheduler_lock() -> bool:
    """
    Ensure only one process starts APScheduler.

    In production, Gunicorn runs multiple worker processes and each worker executes
    FastAPI startup events. Without an inter-process lock, all workers will start
    their own scheduler and each cron job runs multiple times.
    """
    global _scheduler_lock_fd, _scheduler_lock_owner

    if _scheduler_lock_owner:
        return True

    # fcntl is available on Linux (Railway) and unavailable on Windows.
    # Windows local dev usually runs a single process, so we allow startup.
    try:
        import fcntl
    except ImportError:
        logger.warning("APScheduler lock unavailable on this OS; continuing without inter-process lock")
        return True

    lock_dir = os.path.dirname(_scheduler_lock_path)
    if lock_dir:
        os.makedirs(lock_dir, exist_ok=True)

    fd = os.open(_scheduler_lock_path, os.O_CREAT | os.O_RDWR, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        return False

    os.ftruncate(fd, 0)
    os.write(fd, str(os.getpid()).encode("utf-8"))
    _scheduler_lock_fd = fd
    _scheduler_lock_owner = True
    return True


def _release_scheduler_lock() -> None:
    global _scheduler_lock_fd, _scheduler_lock_owner

    if _scheduler_lock_fd is None:
        _scheduler_lock_owner = False
        return

    try:
        import fcntl
        fcntl.flock(_scheduler_lock_fd, fcntl.LOCK_UN)
    except Exception:
        pass

    try:
        os.close(_scheduler_lock_fd)
    except Exception:
        pass

    _scheduler_lock_fd = None
    _scheduler_lock_owner = False


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
async def run_post_scrape_processing():
    """
    Post-scrape processing job — runs after the Railway Cron scraper completes.

    The Railway Cron container runs nawy_scraper_v2.py at Sunday 03:00 UTC and
    writes directly to the database. This job (04:30 UTC) runs the downstream
    processing steps that depend on the freshly-scraped data:
      1. Mark stale properties (not seen in current/previous scrape run)
      2. Flag under/over-priced properties per location zone
      3. Notify the Orchestrator to refresh SEO content
    """
    logger.info("[CRON] Starting post-scrape processing...")
    try:
        from app.services.nawy_scraper import mark_stale_properties, flag_underpriced_properties

        # Clean up stale properties not seen in last 2 runs
        stale_result = await mark_stale_properties()
        logger.info(f"[CRON] Stale cleanup: {stale_result.get('stale_marked', 0)} marked unavailable")

        # Cross-DB price validation
        price_result = await flag_underpriced_properties()
        logger.info(f"[CRON] Price validation: {price_result.get('flagged', 0)} flagged")

        # Invalidate cached price forecasts so the next request recomputes against
        # the freshly-scraped PropertyPriceSnapshot rows (bumps a cache version key).
        try:
            from app.api.forecast_router import invalidate_forecast_cache
            invalidate_forecast_cache()
            logger.info("[CRON] Forecast cache invalidated")
        except Exception as e:
            logger.warning(f"[CRON] Forecast cache invalidation skipped: {e}")

        # Notify Orchestrator for SEO content refresh
        await _notify_orchestrator("property_scrape_complete", {
            "significantChanges": stale_result.get("stale_marked", 0),
        })
        logger.info("[CRON] Post-scrape processing complete")
    except Exception as e:
        logger.error(f"[CRON] Post-scrape processing failed: {e}")
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
            result = await scrape_geopolitical_events(db)
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

@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=60, max=600), reraise=True)
async def run_nawy_scrape_scheduled():
    """
    Weekly Nawy property scraper job.
    Runs every Sunday at 03:00 UTC (post-scrape processing follows at 04:30).
    Writes directly to the database, then triggers post-scrape processing.
    """
    logger.info("[CRON] Starting scheduled weekly Nawy scrape...")
    try:
        from app.services.nawy_scraper import run_nawy_scrape
        result = await run_nawy_scrape()
        logger.info(
            f"[CRON] Nawy scrape completed: "
            f"scraped={result.get('scraped', 0)}, "
            f"upserted={result.get('upserted', 0)}, "
            f"errors={result.get('errors', 0)}"
        )
        # Trigger post-scrape cleanup immediately after scraping
        await run_post_scrape_processing()
        # Notify Orchestrator
        await _notify_orchestrator("property_scrape_complete", {
            "significantChanges": result.get("upserted", 0),
            "trigger": "scheduled_weekly",
        })
    except Exception as e:
        logger.error(f"[CRON] Scheduled Nawy scrape failed: {e}")
        raise


async def run_subscription_expiry():
    """
    Daily downgrade of expired Osool Pro subscriptions.
    Active subscriptions past current_period_end + grace are expired and the
    user's denormalized subscription_tier reverts to 'free' (admins exempt).
    """
    from datetime import datetime, timedelta, timezone as dt_timezone

    from sqlalchemy import select

    from app.config import config
    from app.database import AsyncSessionLocal
    from app.models import Subscription, User

    logger.info("[CRON] Starting subscription expiry sweep...")
    cutoff = datetime.now(dt_timezone.utc) - timedelta(days=config.SUBSCRIPTION_GRACE_DAYS)
    expired_count = 0

    async with AsyncSessionLocal() as db:
        subs = (
            await db.execute(
                select(Subscription).where(
                    Subscription.status == "active",
                    Subscription.current_period_end.isnot(None),
                    Subscription.current_period_end < cutoff,
                )
            )
        ).scalars().all()

        now_utc = datetime.now(dt_timezone.utc)
        for sub in subs:
            sub.status = "expired"
            user = (
                await db.execute(select(User).where(User.id == sub.user_id))
            ).scalar_one_or_none()
            if user and (user.subscription_tier or "free").lower() != "admin":
                # Keep premium if the user has another still-active subscription
                other = (
                    await db.execute(
                        select(Subscription.id).where(
                            Subscription.user_id == sub.user_id,
                            Subscription.status == "active",
                            Subscription.id != sub.id,
                        ).limit(1)
                    )
                ).scalar_one_or_none()
                # Renewals stack expiry on the User row (subscription_engine
                # grant_premium_monthly) — never downgrade while it's still live
                user_expiry = getattr(user, "subscription_expires_at", None)
                if user_expiry is not None and user_expiry.tzinfo is None:
                    user_expiry = user_expiry.replace(tzinfo=dt_timezone.utc)
                still_live = user_expiry is not None and user_expiry > now_utc
                if not other and not still_live:
                    user.subscription_tier = "free"
                    expired_count += 1
                    try:
                        from app.services.email_service import email_service
                        frontend = os.getenv("FRONTEND_URL", "https://osool-ten.vercel.app")
                        email_service.send_subscription_expired(
                            user.email, pricing_url=f"{frontend}/pricing"
                        )
                    except Exception as mail_err:
                        logger.warning("[CRON] Expiry email failed (non-fatal): %s", mail_err)

        await db.commit()

    logger.info("[CRON] Subscription expiry sweep done: %d downgraded", expired_count)


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=60, max=300), reraise=True)
async def run_saved_search_alerts_scheduled():
    """Daily Pro-only saved-search alert sweep (new matches + price drops)."""
    logger.info("[CRON] Starting saved-search alerts sweep...")
    try:
        from app.services.saved_search_alerts import run_saved_search_alerts
        result = await run_saved_search_alerts()
        logger.info(f"[CRON] Saved-search alerts completed: {result}")
    except Exception as e:
        logger.error(f"[CRON] Saved-search alerts failed: {e}")
        raise


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=60, max=300), reraise=True)
async def run_embedding_backfill_scheduled():
    """
    Nightly embedding backfill: the zero-token scraper leaves new/changed
    properties with embedding=NULL (invisible to vector search) — this job
    sweeps and re-embeds them so retrieval blind spots self-heal within a day.
    """
    logger.info("[CRON] Starting nightly embedding backfill...")
    try:
        from app.services.embedding_backfill import run_embedding_backfill
        result = await run_embedding_backfill()
        logger.info(f"[CRON] Embedding backfill completed: {result}")
    except Exception as e:
        logger.error(f"[CRON] Embedding backfill failed: {e}")
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


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=60, max=300), reraise=True)
async def run_portfolio_valuations():
    """Weekly portfolio valuation update job."""
    logger.info("[CRON] Starting portfolio valuation updates...")
    try:
        from app.database import AsyncSessionLocal
        from app.services.portfolio_engine import update_valuations
        async with AsyncSessionLocal() as db:
            result = await update_valuations(db)
            logger.info(f"[CRON] Portfolio valuations updated: {result.get('updated', 0)} entries")
    except Exception as e:
        logger.error(f"[CRON] Portfolio valuations failed: {e}")
        raise


def init_scheduler():
    """
    Initialize and start the APScheduler with weekly cron jobs.
    Called once during FastAPI startup.
    """
    if scheduler.running:
        logger.info("APScheduler already running in pid=%s; skipping re-init", os.getpid())
        return

    if not _acquire_scheduler_lock():
        logger.info("APScheduler already owned by another worker; skipping init in pid=%s", os.getpid())
        return

    # Post-scrape processing: Every Sunday at 04:30 UTC
    # Runs after the Railway Cron scraper container (03:00 UTC) completes.
    scheduler.add_job(
        run_post_scrape_processing,
        trigger=CronTrigger(day_of_week="sun", hour=4, minute=30),
        id="weekly_post_scrape_processing",
        name="Weekly Post-Scrape Processing (stale + price flags)",
        replace_existing=True,
        misfire_grace_time=3600,
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

    # Nawy Property Scraper: Weekly, Sundays at 03:00 UTC
    scheduler.add_job(
        run_nawy_scrape_scheduled,
        trigger=CronTrigger(day_of_week="sun", hour=3, minute=0),
        id="weekly_nawy_scraper",
        name="Weekly Nawy Property Scraper (Sundays 03:00 UTC)",
        replace_existing=True,
        misfire_grace_time=7200,  # 2h grace — scrape takes up to 60 min
    )

    # Subscription expiry: Daily at 02:00 UTC
    scheduler.add_job(
        run_subscription_expiry,
        trigger=CronTrigger(hour=2, minute=0),
        id="daily_subscription_expiry",
        name="Daily Osool Pro Subscription Expiry Sweep",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    # Saved-search alerts (Pro): Daily at 06:00 UTC (after scrape + backfill)
    scheduler.add_job(
        run_saved_search_alerts_scheduled,
        trigger=CronTrigger(hour=6, minute=0),
        id="daily_saved_search_alerts",
        name="Daily Saved-Search Alerts (price drops + new matches)",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    # Embedding backfill: Daily at 05:15 UTC (after scrapers/post-processing)
    scheduler.add_job(
        run_embedding_backfill_scheduled,
        trigger=CronTrigger(hour=5, minute=15),
        id="daily_embedding_backfill",
        name="Daily Embedding Backfill (NULL-embedding properties)",
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

    # V5: Portfolio valuations: Every Sunday at 05:30 UTC (after image mirror)
    scheduler.add_job(
        run_portfolio_valuations,
        trigger=CronTrigger(day_of_week="sun", hour=5, minute=30),
        id="weekly_portfolio_valuations",
        name="Weekly Portfolio Valuation Updates",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    # A5: Email drip — daily at 09:00 UTC (~11 Cairo). Single pass per day
    # is plenty given our 24h / 3d / 14d cadence; running more often just
    # burns DB cycles for no extra reach. Hard-capped to 50 sends/run inside
    # email_drip.send_due_drips so this can't flood SendGrid.
    from app.services.email_drip import send_due_drips
    scheduler.add_job(
        send_due_drips,
        trigger=CronTrigger(hour=9, minute=0),
        id="daily_email_drip",
        name="Daily Email Drip (welcome/primer/final-nudge)",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    scheduler.start()
    logger.info("✅ APScheduler started with cron jobs:")
    logger.info("   📅 Nawy Scraper: Sundays 03:00 UTC (weekly)")
    logger.info("   📅 Post-Scrape Processing: Sundays 04:30 UTC")
    logger.info("   📅 Economic Scraper: Sundays 03:30 UTC")
    logger.info("   📅 Geopolitical Scraper: Daily 04:00 UTC")
    logger.info("   📅 Image Mirror: Sundays 05:00 UTC")
    logger.info("   📅 Portfolio Valuations: Sundays 05:30 UTC")
    logger.info("   📅 Marketing Generator: 1st/15th 06:00 UTC")
    logger.info("   📅 Email Drip: Daily 09:00 UTC (welcome/primer/final-nudge)")

    # Log next run times
    for job in scheduler.get_jobs():
        logger.info(f"   Next run for '{job.name}': {job.next_run_time}")


def shutdown_scheduler():
    """Gracefully stop the scheduler."""
    if scheduler.running and _scheduler_lock_owner:
        scheduler.shutdown(wait=False)
        logger.info("⏹️ APScheduler shut down")
    _release_scheduler_lock()
