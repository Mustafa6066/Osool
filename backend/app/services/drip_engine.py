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
    # V5: Post-purchase portfolio nurture
    ("purchased", 1): {
        "email_type": "purchase_congrats",
        "delay_hours": 1,
        "subject_en": "Congratulations on Your Investment! 🎉 Here's What's Next",
        "subject_ar": "مبروك على استثمارك! 🎉 إيه اللي بعد كده",
        "template": "purchase_congrats",
    },
    ("purchased", 2): {
        "email_type": "appreciation_alert",
        "delay_hours": 168,  # 1 week
        "subject_en": "Your Property Has Already Appreciated — Portfolio Update",
        "subject_ar": "عقارك ارتفع بالفعل — تحديث المحفظة",
        "template": "appreciation_alert",
    },
}


def _build_email_html(template_name: str, user: "User") -> str:
    """Return a full HTML email body for the given drip template."""
    first_name = (user.full_name or "").split()[0] if user.full_name else "عزيزي العميل"
    base_style = (
        "font-family:Cairo,Arial,sans-serif;max-width:640px;margin:0 auto;"
        "background:#fff;border-radius:8px;overflow:hidden;border:1px solid #e5e7eb;"
    )
    header = (
        '<div style="background:#1a3c5e;padding:24px 32px;">'
        '<img src="https://osool.eg/logo-light.png" alt="Osool" height="36" '
        'style="display:block;" onerror="this.style.display=\'none\'">'
        '<p style="color:#fff;margin:8px 0 0;font-size:13px;opacity:.8;">'
        'مستشارك العقاري الذكي</p>'
        '</div>'
    )
    footer = (
        '<div style="background:#f9fafb;padding:16px 32px;text-align:center;">'
        '<p style="color:#9ca3af;font-size:12px;margin:0;">'
        'أصول للعقارات · القاهرة، مصر<br>'
        '<a href="{{unsubscribe_url}}" style="color:#6b7280;">إلغاء الاشتراك</a>'
        '</p></div>'
    )

    bodies: dict[str, str] = {
        "welcome": (
            f'<div style="padding:32px;">'
            f'<h2 style="color:#1a3c5e;margin-top:0;">أهلاً بيك يا {first_name}! 👋</h2>'
            f'<p style="color:#374151;line-height:1.7;">'
            f'شكراً لانضمامك لـ <strong>أصول</strong> — أول مستشار عقاري مدعوم بالذكاء الاصطناعي في مصر.</p>'
            f'<p style="color:#374151;line-height:1.7;">'
            f'بنقدر نساعدك في:</p>'
            f'<ul style="color:#374151;line-height:2;">'
            f'<li>🔍 البحث بين آلاف الوحدات في أكبر مجمعات القاهرة</li>'
            f'<li>💰 تقييم أسعار السوق الحالية بالذكاء الاصطناعي</li>'
            f'<li>📋 تحليل العقود واكتشاف البنود المخفية</li>'
            f'</ul>'
            f'<div style="text-align:center;margin:32px 0;">'
            f'<a href="https://osool.eg/chat" '
            f'style="background:#1a3c5e;color:#fff;padding:14px 32px;border-radius:6px;'
            f'text-decoration:none;font-weight:bold;display:inline-block;">'
            f'ابدأ المحادثة الآن ←</a></div>'
            f'</div>'
        ),
        "drip_tips": (
            f'<div style="padding:32px;">'
            f'<h2 style="color:#1a3c5e;margin-top:0;">3 نصائح ذهبية للاستثمار العقاري في 2025 🏆</h2>'
            f'<p style="color:#6b7280;font-size:13px;">مرحباً {first_name}،</p>'
            f'<div style="border-right:4px solid #1a3c5e;padding:12px 16px;margin:16px 0;background:#f0f4f8;">'
            f'<strong style="color:#1a3c5e;">1. اشتري بالتشطيب الكامل</strong>'
            f'<p style="margin:6px 0 0;color:#374151;font-size:14px;">'
            f'الوحدات المشطبة تحقق عائد إيجاري أعلى بـ 30٪ وتُباع أسرع بكثير من الوحدات نصف التشطيب.</p>'
            f'</div>'
            f'<div style="border-right:4px solid #10b981;padding:12px 16px;margin:16px 0;background:#f0fdf4;">'
            f'<strong style="color:#065f46;">2. القاهرة الجديدة هي النمو الأسرع</strong>'
            f'<p style="margin:6px 0 0;color:#374151;font-size:14px;">'
            f'ارتفعت الأسعار في القاهرة الجديدة 42٪ خلال 18 شهراً. المرحلة القادمة للعاصمة الإدارية تبدأ قريباً.</p>'
            f'</div>'
            f'<div style="border-right:4px solid #f59e0b;padding:12px 16px;margin:16px 0;background:#fffbeb;">'
            f'<strong style="color:#92400e;">3. التمويل العقاري = نفوذ ذكي</strong>'
            f'<p style="margin:6px 0 0;color:#374151;font-size:14px;">'
            f'بمقدمة 20٪ تقدر تتحكم في عقار بقيمة 5 أضعاف رأس مالك. استشر خبير أصول قبل الحجز.</p>'
            f'</div>'
            f'<div style="text-align:center;margin:24px 0;">'
            f'<a href="https://osool.eg/chat" '
            f'style="background:#1a3c5e;color:#fff;padding:12px 28px;border-radius:6px;'
            f'text-decoration:none;font-weight:bold;display:inline-block;">'
            f'اسأل أصول عن استثمارك ←</a></div>'
            f'</div>'
        ),
        "drip_report": (
            f'<div style="padding:32px;">'
            f'<h2 style="color:#1a3c5e;margin-top:0;">تقريرك الاستثماري الشخصي 📊</h2>'
            f'<p style="color:#6b7280;font-size:13px;">مرحباً {first_name}،</p>'
            f'<p style="color:#374151;line-height:1.7;">'
            f'بناءً على محادثاتك مع أصول، جهزنا لك ملخص السوق الذي يهمك:</p>'
            f'<table style="width:100%;border-collapse:collapse;margin:20px 0;font-size:14px;">'
            f'<tr style="background:#1a3c5e;color:#fff;">'
            f'<th style="padding:10px;text-align:right;">المنطقة</th>'
            f'<th style="padding:10px;text-align:center;">متوسط السعر/م²</th>'
            f'<th style="padding:10px;text-align:center;">التغير (سنوي)</th>'
            f'</tr>'
            f'<tr style="background:#f9fafb;">'
            f'<td style="padding:10px;border:1px solid #e5e7eb;">القاهرة الجديدة</td>'
            f'<td style="padding:10px;border:1px solid #e5e7eb;text-align:center;">75,000 ج.م</td>'
            f'<td style="padding:10px;border:1px solid #e5e7eb;text-align:center;color:#10b981;">↑ 42٪</td>'
            f'</tr>'
            f'<tr>'
            f'<td style="padding:10px;border:1px solid #e5e7eb;">الشيخ زايد</td>'
            f'<td style="padding:10px;border:1px solid #e5e7eb;text-align:center;">58,000 ج.م</td>'
            f'<td style="padding:10px;border:1px solid #e5e7eb;text-align:center;color:#10b981;">↑ 31٪</td>'
            f'</tr>'
            f'<tr style="background:#f9fafb;">'
            f'<td style="padding:10px;border:1px solid #e5e7eb;">6 أكتوبر</td>'
            f'<td style="padding:10px;border:1px solid #e5e7eb;text-align:center;">42,000 ج.م</td>'
            f'<td style="padding:10px;border:1px solid #e5e7eb;text-align:center;color:#f59e0b;">↑ 18٪</td>'
            f'</tr>'
            f'</table>'
            f'<p style="color:#374151;font-size:13px;">'
            f'* الأسعار تقديرية بناءً على بيانات السوق الحالية. للحصول على تقييم دقيق لعقار بعينه، تحدث مع أصول.</p>'
            f'<div style="text-align:center;margin:24px 0;">'
            f'<a href="https://osool.eg/chat" '
            f'style="background:#1a3c5e;color:#fff;padding:12px 28px;border-radius:6px;'
            f'text-decoration:none;font-weight:bold;display:inline-block;">'
            f'احصل على تقييم مجاني ←</a></div>'
            f'</div>'
        ),
        "drip_urgency": (
            f'<div style="padding:32px;">'
            f'<div style="background:#fef2f2;border:1px solid #fecaca;border-radius:6px;'
            f'padding:12px 16px;margin-bottom:24px;">'
            f'<strong style="color:#991b1b;">⚡ عرض محدود الوقت</strong>'
            f'</div>'
            f'<h2 style="color:#1a3c5e;margin-top:0;">{first_name}، وحدات في نطاق ميزانيتك تُحجز الآن</h2>'
            f'<p style="color:#374151;line-height:1.7;">'
            f'سوق العقارات المصري يشهد حركة شراء غير معتادة هذا الشهر. '
            f'الوحدات في المجمعات الكبرى تُباع أسرع من أي وقت مضى.</p>'
            f'<div style="background:#1a3c5e;border-radius:8px;padding:20px;margin:20px 0;color:#fff;">'
            f'<p style="margin:0;font-size:15px;font-weight:bold;">لماذا الآن؟</p>'
            f'<ul style="margin:10px 0 0;padding-right:18px;line-height:2;">'
            f'<li>أسعار المطورين قبل رفع الربع القادم</li>'
            f'<li>فوائد التمويل الحالية لن تستمر طويلاً</li>'
            f'<li>الوحدات الجاهزة للتسليم تنفد أولاً</li>'
            f'</ul>'
            f'</div>'
            f'<div style="text-align:center;margin:24px 0;">'
            f'<a href="https://osool.eg/chat" '
            f'style="background:#dc2626;color:#fff;padding:14px 32px;border-radius:6px;'
            f'text-decoration:none;font-weight:bold;display:inline-block;font-size:16px;">'
            f'احجز استشارة مجانية الآن ←</a>'
            f'<p style="color:#9ca3af;font-size:12px;margin:8px 0 0;">بدون أي التزام</p>'
            f'</div>'
            f'</div>'
        ),
    }

    body_html = bodies.get(template_name, f"<p>مرحباً {first_name}،<br>شكراً لتواصلك مع أصول.</p>")
    return f'<div dir="rtl" style="{base_style}">{header}{body_html}{footer}</div>'


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
                    "html": _build_email_html(template["template"], user),
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
