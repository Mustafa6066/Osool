"""
Free-tier conversion gate utilities.

Extracts exactly one high-signal anomaly to create a give-to-get teaser.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Property


class FreeTierConversionGate:
    @staticmethod
    async def extract_one_anomaly(
        db: AsyncSession,
        *,
        location_filter: Optional[str] = None,
        compound_filter: Optional[str] = None,
    ) -> dict:
        query = (
            select(Property)
            .where(
                Property.is_available.is_(True),
                Property.osool_score.is_not(None),
                Property.bargain_percentage.is_not(None),
                Property.osool_score >= 80,
                Property.bargain_percentage > 0,
            )
            .order_by(Property.osool_score.desc(), Property.bargain_percentage.desc())
        )

        if location_filter:
            query = query.where(Property.location.ilike(f"%{location_filter}%"))
        if compound_filter:
            query = query.where(Property.compound.ilike(f"%{compound_filter}%"))

        row = (await db.execute(query.limit(1))).scalar_one_or_none()
        if not row:
            return {
                "error": "No high-signal anomaly found for the current filters."
            }

        market_avg_price = (
            await db.execute(
                select(func.avg(Property.price))
                .where(
                    Property.is_available.is_(True),
                    Property.location == row.location,
                )
            )
        ).scalar()

        return {
            "property_id": row.id,
            "location": row.location,
            "compound": row.compound,
            "asking_price": float(row.price),
            "market_avg_price": float(market_avg_price) if market_avg_price else None,
            "osool_score": float(row.osool_score),
            "bargain_percentage": float(row.bargain_percentage),
            "why_this_is_a_hook": (
                f"Top anomaly: score={row.osool_score:.1f} with +{row.bargain_percentage:.1f}% potential edge"
            ),
        }


def build_value_sandwich(hook: dict, language: str = "ar") -> str:
    if hook.get("error"):
        return hook["error"]

    if language.lower().startswith("ar"):
        return (
            f"هذه الوحدة في {hook.get('location') or 'المنطقة المحددة'} تبدو أقل من متوسط السوق بنمط غير عادي. "
            f"متوسطنا الإحصائي يشير إلى فرصة محتملة (+{hook['bargain_percentage']:.1f}%). "
            "لو تريد كامل المقارنة وخطة التفاوض وخيارات أقوى بديلة، كمل إلى الاستشارة الموجهة."
        )

    return (
        f"This unit in {hook.get('location') or 'the selected area'} is an outlier versus market norms. "
        f"Our model estimates a potential edge of +{hook['bargain_percentage']:.1f}%. "
        "To unlock full comparables, negotiation plan, and broker-ready alternatives, continue to guided consultation."
    )
