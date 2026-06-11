"""
Saved-Search Alerts (Osool Pro)
--------------------------------
Daily job: for every active SavedSearch owned by a premium user, find
 (a) newly scraped properties matching the saved filters since the last
     check, and
 (b) meaningful price drops (property_price_events, ≥5% down) on matching
     properties — the "La2ta" signal buyers pay for.

Sends one digest email per saved search with a WhatsApp share deep link,
then advances last_checked_at / match_count. Free users' searches are
skipped (their dashboard shows the Pro teaser instead).
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from sqlalchemy import and_, select

from app.database import AsyncSessionLocal
from app.models import Property, PropertyPriceEvent, SavedSearch, User

logger = logging.getLogger(__name__)

_FRONTEND_URL = os.getenv("FRONTEND_URL", "https://osool-ten.vercel.app")
_PRICE_DROP_THRESHOLD = -0.05  # alert on drops of 5%+
_MAX_ITEMS_PER_ALERT = 5
_PREMIUM_TIERS = {"premium", "admin"}


def _property_filters(filters: dict):
    """Translate saved-search filters_json into SQLAlchemy conditions."""
    conditions = [Property.is_available.is_(True)]
    if filters.get("location"):
        conditions.append(Property.location.ilike(f"%{filters['location']}%"))
    if filters.get("budget_min"):
        conditions.append(Property.price >= float(filters["budget_min"]))
    if filters.get("budget_max"):
        conditions.append(Property.price <= float(filters["budget_max"]))
    if filters.get("bedrooms"):
        conditions.append(Property.bedrooms >= int(filters["bedrooms"]))
    if filters.get("property_type"):
        conditions.append(Property.type.ilike(f"%{filters['property_type']}%"))
    return conditions


async def _new_matches(db, filters: dict, since: datetime) -> list[Property]:
    stmt = (
        select(Property)
        .where(and_(*_property_filters(filters), Property.scraped_at >= since))
        .order_by(Property.price_per_sqm.asc().nullslast())
        .limit(_MAX_ITEMS_PER_ALERT)
    )
    return (await db.execute(stmt)).scalars().all()


async def _price_drops(db, filters: dict, since: datetime) -> list[tuple[Property, PropertyPriceEvent]]:
    stmt = (
        select(Property, PropertyPriceEvent)
        .join(PropertyPriceEvent, PropertyPriceEvent.property_id == Property.id)
        .where(
            and_(
                *_property_filters(filters),
                PropertyPriceEvent.created_at >= since,
                PropertyPriceEvent.pct_change <= _PRICE_DROP_THRESHOLD,
            )
        )
        .order_by(PropertyPriceEvent.pct_change.asc())
        .limit(_MAX_ITEMS_PER_ALERT)
    )
    return [(row.Property, row.PropertyPriceEvent) for row in (await db.execute(stmt)).all()]


def _build_alert_email(
    search_name: str, new_props: list, drops: list, language_hint: str = "ar"
) -> tuple[str, str]:
    """Returns (subject, html). Bilingual with Arabic leading."""
    lines = []
    for prop, event in drops:
        pct = abs(event.pct_change) * 100
        lines.append(
            f"<li>🔥 <strong>{prop.title}</strong> — {prop.compound or prop.location}: "
            f"انخفض السعر {pct:.0f}٪ إلى {event.new_price:,.0f} جنيه "
            f"(كان {event.old_price:,.0f})</li>"
        )
    for prop in new_props:
        lines.append(
            f"<li>🆕 <strong>{prop.title}</strong> — {prop.compound or prop.location}: "
            f"{prop.price:,.0f} جنيه ({prop.size_sqm or '؟'} م²)</li>"
        )

    explore_url = f"{_FRONTEND_URL}/explore"
    wa_text = quote(
        f"لقيت فرص عقارية جديدة على أصول مطابقة لبحثي «{search_name}» — {explore_url}"
    )
    whatsapp_url = f"https://wa.me/?text={wa_text}"

    subject = f"🔔 فرص جديدة لبحثك «{search_name}» | New matches on Osool"
    html = f"""
    <html dir="rtl">
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #1e293b; padding: 24px; border-radius: 12px; color: #ffffff;">
            <h2 style="margin-top: 0;">🔔 بحثك «{search_name}» لقى حاجات جديدة</h2>
            <ul style="line-height: 1.9; padding-inline-start: 18px;">{''.join(lines)}</ul>
            <p style="text-align: center; margin: 24px 0;">
                <a href="{explore_url}" style="background: #10b981; color: #fff;
                   padding: 12px 28px; border-radius: 8px; text-decoration: none;">
                    شوف التفاصيل على أصول
                </a>
            </p>
            <p style="text-align: center;">
                <a href="{whatsapp_url}" style="color: #34d399; text-decoration: none;">
                    📲 شارك على واتساب
                </a>
            </p>
            <p dir="ltr" style="color: #cbd5e1; font-size: 13px;">
                Your saved search "{search_name}" found new matches and price drops.
                Open Osool to see the details.
            </p>
        </div>
    </body>
    </html>
    """
    return subject, html


async def run_saved_search_alerts() -> dict:
    """Sweep all premium users' active saved searches. Returns a summary."""
    summary = {"searches_checked": 0, "alerts_sent": 0, "skipped_free": 0}
    now = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as db:
        rows = (
            await db.execute(
                select(SavedSearch, User)
                .join(User, SavedSearch.user_id == User.id)
                .where(SavedSearch.is_active.is_(True))
            )
        ).all()

        for search, user in rows:
            tier = (getattr(user, "subscription_tier", "free") or "free").lower()
            if tier not in _PREMIUM_TIERS:
                summary["skipped_free"] += 1
                continue

            summary["searches_checked"] += 1
            since = search.last_checked_at or (now - timedelta(days=7))

            try:
                filters = json.loads(search.filters_json or "{}")
                new_props = await _new_matches(db, filters, since)
                drops = await _price_drops(db, filters, since)

                # Don't re-announce a new property that also appears as a drop
                drop_ids = {p.id for p, _ in drops}
                new_props = [p for p in new_props if p.id not in drop_ids]

                if new_props or drops:
                    subject, html = _build_alert_email(search.name, new_props, drops)
                    try:
                        from app.services.email_service import email_service
                        email_service._send_email(user.email, subject, html)
                        summary["alerts_sent"] += 1
                    except Exception as mail_err:
                        logger.warning(
                            "[alerts] Email failed for search %s (non-fatal): %s",
                            search.id, mail_err,
                        )
                    search.match_count = (search.match_count or 0) + len(new_props) + len(drops)

                search.last_checked_at = now
            except Exception as exc:
                logger.error("[alerts] Saved search %s failed: %s", search.id, exc)

        await db.commit()

    logger.info("[alerts] Sweep done: %s", summary)
    return summary
