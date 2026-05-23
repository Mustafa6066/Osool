"""
Company Brain Kernel
--------------------
Builds deterministic, company-level strategic truth payload for orchestration.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MarketIndicator, Property
from app.services.market_statistics import compute_detailed_qa_statistics


class CompanyBrainKernel:
    @staticmethod
    async def synthesize_skills_payload(db: AsyncSession) -> dict[str, Any]:
        """Structured company-brain payload for orchestrators and chat routing."""
        qa_stats = await compute_detailed_qa_statistics(db)

        indicators = (
            await db.execute(select(MarketIndicator.key, MarketIndicator.value))
        ).all()

        top_anomalies = (
            await db.execute(
                select(
                    Property.id,
                    Property.location,
                    Property.compound,
                    Property.price,
                    Property.osool_score,
                    Property.bargain_percentage,
                )
                .where(
                    Property.is_available.is_(True),
                    Property.osool_score.is_not(None),
                )
                .order_by(Property.osool_score.desc())
                .limit(3)
            )
        ).all()

        return {
            "qa_statistics": qa_stats,
            "market_indicators": {k: float(v) for k, v in indicators},
            "top_anomalies": [
                {
                    "property_id": r.id,
                    "location": r.location,
                    "compound": r.compound,
                    "price": float(r.price) if r.price is not None else None,
                    "osool_score": float(r.osool_score) if r.osool_score is not None else None,
                    "bargain_percentage": float(r.bargain_percentage) if r.bargain_percentage is not None else None,
                }
                for r in top_anomalies
            ],
        }

    @staticmethod
    async def synthesize_definitive_truth(db: AsyncSession) -> str:
        payload = await CompanyBrainKernel.synthesize_skills_payload(db)

        return "[SYSTEM_BRAIN_DEFINITIVE_TRUTH]" + json.dumps(payload, ensure_ascii=False)
