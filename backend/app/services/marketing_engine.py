"""
Marketing Engine — Conversion Pixel & Retargeting
----------------------------------------------------
Handles server-side conversion events for Meta (CAPI),
Google Ads, and retargeting rule evaluation.
"""

import os
import hashlib
import logging
from datetime import datetime
from typing import Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RetargetingRule, LeadProfile, AdCampaign

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# META CONVERSIONS API (Server-Side)
# ═══════════════════════════════════════════════════════════════

async def send_meta_conversion(
    event_name: str,
    user_email: Optional[str] = None,
    user_phone: Optional[str] = None,
    custom_data: Optional[dict] = None,
):
    """
    Send a server-side conversion event to Meta CAPI.
    Event names: Lead, Search, ViewContent, InitiateCheckout, Purchase
    """
    pixel_id = os.getenv("META_PIXEL_ID")
    access_token = os.getenv("META_CAPI_TOKEN")

    if not pixel_id or not access_token:
        logger.debug("Meta CAPI not configured, skipping")
        return

    user_data = {}
    if user_email:
        user_data["em"] = [hashlib.sha256(user_email.lower().strip().encode()).hexdigest()]
    if user_phone:
        user_data["ph"] = [hashlib.sha256(user_phone.strip().encode()).hexdigest()]

    payload = {
        "data": [
            {
                "event_name": event_name,
                "event_time": int(datetime.utcnow().timestamp()),
                "action_source": "website",
                "user_data": user_data,
                "custom_data": custom_data or {},
            }
        ],
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"https://graph.facebook.com/v18.0/{pixel_id}/events",
                params={"access_token": access_token},
                json=payload,
                timeout=10.0,
            )
            resp.raise_for_status()
            logger.info("Meta CAPI event sent: %s", event_name)
    except Exception as e:
        logger.error("Meta CAPI error: %s", e)


# ═══════════════════════════════════════════════════════════════
# GOOGLE ADS OFFLINE CONVERSIONS
# ═══════════════════════════════════════════════════════════════

async def send_google_conversion(
    conversion_action: str,
    gclid: Optional[str] = None,
    value: Optional[float] = None,
    currency: str = "EGP",
):
    """
    Send an offline conversion to Google Ads.
    Requires GCLID from click tracking.
    """
    if not gclid:
        logger.debug("No GCLID, skipping Google conversion")
        return

    customer_id = os.getenv("GOOGLE_ADS_CUSTOMER_ID")
    if not customer_id:
        logger.debug("Google Ads not configured, skipping")
        return

    # In production, this would use the Google Ads API client
    logger.info("Google conversion: %s (gclid=%s, value=%s %s)",
                conversion_action, gclid[:10], value, currency)


# ═══════════════════════════════════════════════════════════════
# RETARGETING RULE ENGINE
# ═══════════════════════════════════════════════════════════════

async def evaluate_retargeting_rules(
    db: AsyncSession,
    event: str,
    user_id: Optional[int] = None,
    lead: Optional[LeadProfile] = None,
):
    """
    Evaluate all active retargeting rules against an event.
    Fires matching conversion pixels.
    """
    rules = (await db.execute(
        select(RetargetingRule).where(
            RetargetingRule.is_active == True,
            RetargetingRule.trigger_type == event,
        )
    )).scalars().all()

    for rule in rules:
        trigger_config = {}
        if rule.trigger_config:
            import json as _json
            try:
                trigger_config = _json.loads(rule.trigger_config)
            except (TypeError, _json.JSONDecodeError):
                pass

        # Check if lead matches filter
        if lead and trigger_config:
            min_score = trigger_config.get("min_score")
            if min_score and (lead.score or 0) < min_score:
                continue

            required_stage = trigger_config.get("stage")
            if required_stage and lead.stage != required_stage:
                continue

        # Execute action
        action = rule.ad_template
        if action == "meta_lead":
            await send_meta_conversion("Lead")
        elif action == "meta_search":
            await send_meta_conversion("Search")
        elif action == "meta_view_content":
            await send_meta_conversion("ViewContent")

        logger.info("Retargeting rule fired: %s → %s", rule.name, action)
