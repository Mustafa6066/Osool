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
                            await email_service.send_email(
                                to_email=user.email,
                                subject=f"Osool {notification_type.title()} Notification",
                                html_body=f"<p>{message}</p>",
                                text_body=message
                            )
                            return True
                        else:
                            logger.warning(f"User {user_id} has no email, skipping email delivery")
                            return False
                
                # Run async function in sync context
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
                            await sms_service.send_sms(phone=user.phone_number, message=message)
                            return True
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
