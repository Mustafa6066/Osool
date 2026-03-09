"""
Email Drip Engine — Automated Email Sequences
------------------------------------------------
Manages drip campaigns based on lead stage transitions.
Triggered by Celery tasks on schedule.
"""

import os
import logging
from datetime import datetime, timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, LeadProfile, EmailEvent, EmailStatus

logger = logging.getLogger(__name__)


# Drip templates keyed by (stage, sequence_number)
DRIP_TEMPLATES = {
    ("new", 1): {
        "email_type": "welcome",
        "delay_hours": 0,
        "subject_en": "Welcome to Osool — Your AI Real Estate Advisor 🏠",
        "subject_ar": "أهلاً بيك في أصول — مستشارك العقاري الذكي 🏠",
        "template": "welcome",
    },
    ("new", 2): {
        "email_type": "drip_1",
        "delay_hours": 24,
        "subject_en": "3 Insider Tips for Egyptian Real Estate in 2025",
        "subject_ar": "3 نصائح من الداخل عن سوق العقارات المصري 2025",
        "template": "drip_tips",
    },
    ("engaged", 1): {
        "email_type": "drip_2",
        "delay_hours": 48,
        "subject_en": "Your Personalized Investment Report Is Ready",
        "subject_ar": "تقريرك الاستثماري الشخصي جاهز",
        "template": "drip_report",
    },
    ("hot", 1): {
        "email_type": "drip_3",
        "delay_hours": 12,
        "subject_en": "Limited Availability — Projects Matching Your Budget",
        "subject_ar": "توافر محدود — مشاريع في نطاق ميزانيتك",
        "template": "drip_urgency",
    },
}


async def send_drip_email(
    db: AsyncSession,
    user: User,
    template_key: tuple,
) -> bool:
    """Send a single drip email and log the event."""
    template = DRIP_TEMPLATES.get(template_key)
    if not template:
        return False

    resend_key = os.getenv("RESEND_API_KEY")
    if not resend_key:
        logger.warning("RESEND_API_KEY not set, skipping drip email")
        return False

    if not user.email:
        return False

    # Use Arabic subject if user preferred language is Arabic
    subject = template["subject_en"]

    # Check if this drip was already sent
    existing = await db.execute(
        select(EmailEvent).where(
            EmailEvent.user_id == user.id,
            EmailEvent.template_id == template["email_type"],
        )
    )
    if existing.scalar_one_or_none():
        return False  # Already sent

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {resend_key}"},
                json={
                    "from": os.getenv("EMAIL_FROM", "Osool <noreply@osool.eg>"),
                    "to": [user.email],
                    "subject": subject,
                    "html": f"<p>Template: {template['template']}</p>",
                },
                timeout=15.0,
            )
            resp.raise_for_status()
            resend_data = resp.json()
    except Exception as e:
        logger.error("Drip email failed for user %s: %s", user.id, e)
        return False

    event = EmailEvent(
        user_id=user.id,
        template_id=template["email_type"],
        email_type=template["email_type"],
        subject=subject,
        status=EmailStatus.SENT,
        resend_id=resend_data.get("id"),
        sent_at=datetime.utcnow(),
    )
    db.add(event)
    await db.commit()
    logger.info("Drip email sent: %s → %s", template["email_type"], user.email)
    return True


async def process_drip_queue(db: AsyncSession):
    """
    Process all users eligible for drip emails.
    Called by the Celery beat schedule.
    """
    leads = (await db.execute(
        select(LeadProfile).where(LeadProfile.stage.in_(["new", "engaged", "hot"]))
    )).scalars().all()

    sent_count = 0
    for lead in leads:
        user_q = await db.execute(select(User).where(User.id == lead.user_id))
        user = user_q.scalar_one_or_none()
        if not user:
            continue

        # Find next drip to send
        for seq in range(1, 4):
            key = (lead.stage, seq)
            if key in DRIP_TEMPLATES:
                if await send_drip_email(db, user, key):
                    sent_count += 1
                    break  # Only send one email per user per cycle

    logger.info("Drip engine processed: %d emails sent", sent_count)
    return sent_count
