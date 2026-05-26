"""
Portfolio Expansion Engine (V5)
-------------------------------
Automated ownership tracking + appreciation monitoring + expansion nudges.

After payment confirmation, a Portfolio row is created.
A weekly scheduler job updates valuations using AREA_GROWTH rates.
When equity reaches ≥20% of a target second property, a leverage alert fires.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models import Portfolio, Transaction, Property
from app.ai_engine.fear_clock import AREA_GROWTH

logger = logging.getLogger(__name__)

# Minimum equity fraction of target property price to qualify for leverage
LEVERAGE_THRESHOLD = 0.20


async def create_portfolio_entry(
    session: AsyncSession,
    user_id: int,
    property_id: int,
    transaction_id: int,
    purchase_price: float,
    equity_paid: float = 0.0,
    monthly_installment: float = None,
    installments_remaining: int = None,
    location_zone: str = None,
) -> Portfolio:
    """Create a portfolio entry after a confirmed payment."""
    entry = Portfolio(
        user_id=user_id,
        property_id=property_id,
        transaction_id=transaction_id,
        purchase_price=purchase_price,
        current_estimated_value=purchase_price,
        appreciation_pct=0.0,
        equity_paid=equity_paid,
        monthly_installment=monthly_installment,
        installments_remaining=installments_remaining,
        status="active",
        location_zone=location_zone,
        last_valuation_at=datetime.now(timezone.utc),
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    logger.info(f"📦 Portfolio entry created: user={user_id}, property={property_id}, price={purchase_price}")
    return entry


async def update_valuations(session: AsyncSession) -> Dict[str, int]:
    """
    Weekly job: update current_estimated_value for all active portfolio entries.
    Uses AREA_GROWTH rates with weekly pro-rating (rate / 52).
    """
    result = await session.execute(
        select(Portfolio).filter(Portfolio.status.in_(["active", "leverageable"]))
    )
    entries = result.scalars().all()

    updated = 0
    for entry in entries:
        rate = _get_area_growth_rate(entry.location_zone)
        weekly_rate = rate / 52  # pro-rate annual → weekly
        new_value = entry.current_estimated_value * (1 + weekly_rate)
        appreciation = ((new_value - entry.purchase_price) / entry.purchase_price) * 100

        entry.current_estimated_value = round(new_value, 2)
        entry.appreciation_pct = round(appreciation, 2)
        entry.last_valuation_at = datetime.now(timezone.utc)

        # Check leverage readiness
        if entry.status == "active" and check_leverage_readiness(entry):
            entry.status = "leverageable"
            logger.info(f"🔓 Portfolio {entry.id} is now leverageable (appreciation={appreciation:.1f}%)")

        updated += 1

    await session.commit()
    logger.info(f"📈 Updated {updated} portfolio valuations")
    return {"updated": updated}


def check_leverage_readiness(entry: Portfolio) -> bool:
    """
    True if equity (appreciation + paid) ≥ 20% of a typical second property.
    Uses the entry's current value as a proxy for target property price.
    """
    equity = entry.equity_paid + (entry.current_estimated_value - entry.purchase_price)
    target_price = entry.current_estimated_value  # same-tier proxy
    return equity >= target_price * LEVERAGE_THRESHOLD


async def get_portfolio_summary(session: AsyncSession, user_id: int) -> Dict[str, Any]:
    """Get all portfolio entries with ROI and leverage status."""
    result = await session.execute(
        select(Portfolio).filter(Portfolio.user_id == user_id).order_by(Portfolio.created_at.desc())
    )
    entries = result.scalars().all()

    items = []
    total_invested = 0.0
    total_current = 0.0

    for e in entries:
        roi = ((e.current_estimated_value - e.purchase_price) / e.purchase_price * 100) if e.purchase_price > 0 else 0
        equity = e.equity_paid + (e.current_estimated_value - e.purchase_price)
        items.append({
            "id": e.id,
            "property_id": e.property_id,
            "purchase_price": e.purchase_price,
            "current_value": e.current_estimated_value,
            "appreciation_pct": round(e.appreciation_pct, 2),
            "roi_pct": round(roi, 2),
            "equity": round(equity, 2),
            "status": e.status,
            "location_zone": e.location_zone,
            "monthly_installment": e.monthly_installment,
            "installments_remaining": e.installments_remaining,
            "last_valuation": e.last_valuation_at.isoformat() if e.last_valuation_at else None,
        })
        total_invested += e.purchase_price
        total_current += e.current_estimated_value

    return {
        "count": len(items),
        "total_invested": round(total_invested, 2),
        "total_current_value": round(total_current, 2),
        "portfolio_roi_pct": round(((total_current - total_invested) / total_invested * 100) if total_invested > 0 else 0, 2),
        "items": items,
    }


async def generate_expansion_alert(session: AsyncSession, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Generate an expansion opportunity alert for leverageable portfolio entries.
    Returns alert dict or None if no opportunity.
    """
    result = await session.execute(
        select(Portfolio).filter(
            Portfolio.user_id == user_id,
            Portfolio.status == "leverageable",
        )
    )
    entry = result.scalars().first()
    if not entry:
        return None

    equity = entry.equity_paid + (entry.current_estimated_value - entry.purchase_price)
    return {
        "type": "expansion_opportunity",
        "portfolio_id": entry.id,
        "property_id": entry.property_id,
        "current_equity": round(equity, 2),
        "appreciation_pct": round(entry.appreciation_pct, 2),
        "message_ar": f"عقارك ارتفع {entry.appreciation_pct:.0f}%! الإيكويتي بتاعتك ({equity:,.0f} جنيه) تقدر تستخدمها كمقدم لعقار تاني.",
        "message_en": f"Your property appreciated {entry.appreciation_pct:.0f}%! Your equity (EGP {equity:,.0f}) can serve as down payment for a second property.",
        "location_zone": entry.location_zone,
    }


def _get_area_growth_rate(location_zone: str) -> float:
    """Get annual growth rate for a location zone from AREA_GROWTH."""
    if not location_zone:
        return 0.15  # conservative default

    loc_lower = location_zone.lower()
    for area, rate in AREA_GROWTH.items():
        if area.lower() in loc_lower or loc_lower in area.lower():
            # Cap to [5%, 30%] forward projection (same logic as fear_clock)
            return max(0.05, min(rate if rate <= 0.30 else rate * 0.15, 0.30))
    return 0.15  # market average
