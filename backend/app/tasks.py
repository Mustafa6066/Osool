"""
Celery Tasks for Osool
----------------------
Background workers for long-running tasks.
"""

from app.celery_app import celery_app
import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=600)
def send_notification_task(self, user_id: int, message: str, notification_type: str = "info", 
                          delivery_methods: Optional[list] = None) -> Dict[str, Any]:
    """
    Background task to send notifications to users via multiple channels.
    
    Args:
        user_id: ID of the user to notify.
        message: Notification message.
        notification_type: Type of notification (info, payment, alert, marketing).
        delivery_methods: List of delivery methods ['email', 'sms', 'push']. Defaults to ['email'].
    
    Returns:
        Dict with delivery status per channel.
    
    Raises:
        Retries on failure with exponential backoff (max 3 attempts).
    """
    if delivery_methods is None:
        delivery_methods = ['email']
    
    logger.info(f"[Worker] Sending {notification_type} notification to user {user_id} via {delivery_methods}")
    
    results = {"user_id": user_id, "type": notification_type, "channels": {}}
    
    try:
        # Email delivery
        if 'email' in delivery_methods:
            try:
                from app.services.email_service import email_service
                # Get user email from database
                from app.database import AsyncSessionLocal
                from app.models import User
                from sqlalchemy import select
                import asyncio
                
                async def send_email():
                    async with AsyncSessionLocal() as session:
                        result = await session.execute(select(User).filter(User.id == user_id))
                        user = result.scalar_one_or_none()
                        if user and user.email:
                            # _send_email is sync (SendGrid SDK), call directly
                            sent = email_service._send_email(
                                to_email=user.email,
                                subject=f"Osool {notification_type.title()} Notification",
                                html_content=f"<p>{message}</p>"
                            )
                            return sent
                        else:
                            logger.warning(f"User {user_id} has no email, skipping email delivery")
                            return False
                
                # Run async function in sync context (needed for DB access)
                email_sent = asyncio.run(send_email())
                results["channels"]["email"] = "sent" if email_sent else "skipped_no_email"
                
            except Exception as email_err:
                logger.error(f"[Worker] Email delivery failed: {email_err}", exc_info=True)
                results["channels"]["email"] = f"failed: {str(email_err)}"
        
        # SMS delivery (if configured)
        if 'sms' in delivery_methods:
            try:
                from app.services.sms_service import sms_service
                from app.database import AsyncSessionLocal
                from app.models import User
                from sqlalchemy import select
                import asyncio
                
                async def send_sms():
                    async with AsyncSessionLocal() as session:
                        result = await session.execute(select(User).filter(User.id == user_id))
                        user = result.scalar_one_or_none()
                        if user and user.phone_number:
                            sent = sms_service.send_message(user.phone_number, message)
                            return sent
                        else:
                            logger.warning(f"User {user_id} has no phone, skipping SMS")
                            return False
                
                sms_sent = asyncio.run(send_sms())
                results["channels"]["sms"] = "sent" if sms_sent else "skipped_no_phone"
                
            except Exception as sms_err:
                logger.error(f"[Worker] SMS delivery failed: {sms_err}", exc_info=True)
                results["channels"]["sms"] = f"failed: {str(sms_err)}"
        
        # Push notification (placeholder for future Firebase/OneSignal integration)
        if 'push' in delivery_methods:
            logger.warning("[Worker] Push notifications not yet implemented")
            results["channels"]["push"] = "not_implemented"
        
        # Overall success if at least one channel succeeded
        success_count = sum(1 for status in results["channels"].values() if status == "sent")
        results["overall_status"] = "success" if success_count > 0 else "all_failed"
        
        logger.info(f"[Worker] Notification delivery complete: {results}")
        return results
        
    except Exception as e:
        logger.error(f"[Worker] Critical notification task failure: {e}", exc_info=True)
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=min(2 ** self.request.retries * 10, 600))


# ═══════════════════════════════════════════════════════════════
# DUAL-ENGINE TASKS
# ═══════════════════════════════════════════════════════════════

@celery_app.task(bind=True, max_retries=2)
def process_drip_emails_task(self):
    """Run the drip email engine — scheduled via beat."""
    import asyncio
    from app.database import AsyncSessionLocal
    from app.services.drip_engine import process_drip_queue

    async def _run():
        async with AsyncSessionLocal() as session:
            return await process_drip_queue(session)

    try:
        count = asyncio.run(_run())
        logger.info("[DripEngine] Processed %d drip emails", count)
        return {"sent": count}
    except Exception as e:
        logger.error("[DripEngine] Failed: %s", e)
        raise self.retry(exc=e, countdown=300)


@celery_app.task(bind=True, max_retries=1)
def generate_seo_content_task(self, page_id: int):
    """Generate AI content for a single SEO page."""
    import asyncio
    from app.database import AsyncSessionLocal
    from app.models import SEOPage, Developer, Area, SEOProject, PageStatus
    from app.ai_engine.seo_page_generator import (
        generate_comparison_content, generate_project_content
    )
    from sqlalchemy import select

    async def _run():
        async with AsyncSessionLocal() as session:
            page = (await session.execute(
                select(SEOPage).where(SEOPage.id == page_id)
            )).scalar_one_or_none()
            if not page:
                return {"error": "Page not found"}

            import json as _json
            content_meta = {}
            if page.content_json:
                try:
                    content_meta = _json.loads(page.content_json)
                except (_json.JSONDecodeError, TypeError):
                    pass

            if content_meta.get("type") == "developer_comparison":
                d1 = (await session.execute(
                    select(Developer).where(Developer.slug == content_meta["developer_1"])
                )).scalar_one_or_none()
                d2 = (await session.execute(
                    select(Developer).where(Developer.slug == content_meta["developer_2"])
                )).scalar_one_or_none()
                if d1 and d2:
                    content = await generate_comparison_content(
                        dev1={c.key: getattr(d1, c.key) for c in d1.__table__.columns},
                        dev2={c.key: getattr(d2, c.key) for c in d2.__table__.columns},
                    )
                    page.content_json = _json.dumps({**content_meta, "generated": content}, default=str)
                    page.status = PageStatus.PUBLISHED.value

            elif content_meta.get("type") == "area_comparison":
                a1 = (await session.execute(
                    select(Area).where(Area.slug == content_meta["area_1"])
                )).scalar_one_or_none()
                a2 = (await session.execute(
                    select(Area).where(Area.slug == content_meta["area_2"])
                )).scalar_one_or_none()
                if a1 and a2:
                    content = await generate_comparison_content(
                        area1={c.key: getattr(a1, c.key) for c in a1.__table__.columns},
                        area2={c.key: getattr(a2, c.key) for c in a2.__table__.columns},
                    )
                    page.content_json = _json.dumps({**content_meta, "generated": content}, default=str)
                    page.status = PageStatus.PUBLISHED.value

            await session.commit()
            return {"status": "generated", "page_id": page_id}

    try:
        return asyncio.run(_run())
    except Exception as e:
        logger.error("[SEOContent] Failed for page %d: %s", page_id, e)
        raise self.retry(exc=e, countdown=60)
