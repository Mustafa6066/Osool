"""
Geopolitical & Macroeconomic Awareness Layer
---------------------------------------------
The "Intelligence Analyst" of the AI Engine.

Fetches the most recent high-impact geopolitical/macro events from the
database and transforms them into actionable real-estate investment context
that gets injected into the Wolf Brain's narrative generation.

This layer makes the AI sound like a shrewd, plugged-in co-investor who
reads The Economist before breakfast and Reuters before bed.

Usage in Wolf Orchestrator:
    geo_layer = GeopoliticalLayer(session)
    geo_prompt = await geo_layer.get_geopolitical_context()
    # → Inject geo_prompt into Claude's system/user message

Output Example:
    "[GEOPOLITICAL INTELLIGENCE BRIEFING]
    🔴 HIGH: Red Sea shipping disruptions (Houthi attacks on cargo vessels)
       → Construction material costs rising 15-20% next quarter.
       → STRATEGY: Off-plan at today's prices locks in pre-inflation value.
    🟡 MEDIUM: CBE holds interest rates at 27.75%
       → Bank CDs still competitive vs rental yields.
       → STRATEGY: Position RE as inflation hedge (30% appreciation > 27% CD).
    Current USD/EGP: 51.50 | Oil: $82/barrel | Inflation: 13.6%
    OVERALL ADVISORY: Favor off-plan with long payment plans (currency devaluation leverage)."
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GeopoliticalEvent
from app.services.cache import cache

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# IMPACT TAG → REAL ESTATE STRATEGY MAPPING
# Maps event impact tags to actionable investment strategies
# ═══════════════════════════════════════════════════════════════

STRATEGY_MAP: Dict[str, Dict[str, str]] = {
    "construction_costs": {
        "strategy_ar": "شراء أوف بلان دلوقتي بيحميك من رفع الأسعار الجاي — المطور بيتحمل فرق التكلفة.",
        "strategy_en": "Buying off-plan NOW locks in current pricing before developers adjust for rising material costs.",
        "angle": "off_plan_advantage",
    },
    "currency_devaluation": {
        "strategy_ar": "مع ضعف الجنيه، العقار هو أفضل مخزن للقيمة — أقساط المستقبل بتتدفع بجنيه أضعف.",
        "strategy_en": "With EGP pressure, real estate is the ultimate store of value — future installments are paid in weaker currency.",
        "angle": "inflation_hedge",
    },
    "inflation_hedge": {
        "strategy_ar": "العقار حقق 30% ارتفاع سنوي مقابل 14% تضخم. فلوسك في البنك بتخسر قيمتها.",
        "strategy_en": "Property delivered 30% annual appreciation vs 14% inflation. Cash in the bank is losing value daily.",
        "angle": "capital_preservation",
    },
    "interest_rates": {
        "strategy_ar": "سعر الفايدة عالي = فرصة للمشتري الكاش + أقساط طويلة بتقلل التكلفة الحقيقية.",
        "strategy_en": "High rates = opportunity for cash buyers + long installment plans reduce real cost over time.",
        "angle": "payment_strategy",
    },
    "supply_chain": {
        "strategy_ar": "اضطرابات سلاسل التوريد بترفع تكاليف البناء. الوحدات الجاهزة محصنة تمامًا.",
        "strategy_en": "Supply chain disruptions are inflating build costs. Ready-to-move units are completely immune.",
        "angle": "ready_vs_offplan",
    },
    "shipping_disruption": {
        "strategy_ar": "أزمة البحر الأحمر بتأخر شحنات الحديد والأسمنت — أسعار ربع السنة الجاي هترتفع حتمًا.",
        "strategy_en": "Red Sea crisis is delaying steel and cement shipments — next quarter prices are guaranteed to jump.",
        "angle": "urgency",
    },
    "foreign_investment": {
        "strategy_ar": "تدفق الاستثمارات الخليجية بيرفع الطلب على المناطق المميزة — ادخل قبل ما الأسعار تتحرك.",
        "strategy_en": "Gulf investment inflows are driving demand in premium areas — enter before prices adjust upward.",
        "angle": "demand_wave",
    },
    "developer_repricing": {
        "strategy_ar": "المطورين بيراجعوا الأسعار كل ربع — أي حاجة تشتريها النهاردة سعرها هيزيد الشهر الجاي.",
        "strategy_en": "Developers reprice quarterly — anything bought today will cost more next month.",
        "angle": "urgency",
    },
    "mortgage_affordability": {
        "strategy_ar": "لو بتفكر في تمويل عقاري، اتحرك قبل أي تعديل في سعر الفايدة.",
        "strategy_en": "If mortgage is your play, act before the next rate adjustment.",
        "angle": "financing",
    },
    "demand_increase": {
        "strategy_ar": "الطلب المتزايد بيحرك الأسعار لفوق — الفرصة في التحرك السريع.",
        "strategy_en": "Rising demand is pushing prices up — the opportunity is in acting fast.",
        "angle": "urgency",
    },
    "price_appreciation": {
        "strategy_ar": "المنطقة دي حققت نمو فوق المتوسط — فرصة استثمارية قبل ما تتشبع.",
        "strategy_en": "This area delivered above-average growth — investment opportunity before saturation.",
        "angle": "investment",
    },
    "infrastructure": {
        "strategy_ar": "مشاريع البنية التحتية الجديدة بترفع قيمة المناطق المحيطة 20-40% خلال 3 سنين.",
        "strategy_en": "New infrastructure projects boost surrounding area values 20-40% within 3 years.",
        "angle": "location_play",
    },
}


# ═══════════════════════════════════════════════════════════════
# GEOPOLITICAL LAYER CLASS
# ═══════════════════════════════════════════════════════════════

class GeopoliticalLayer:
    """
    Cognitive layer that transforms geopolitical events into
    actionable real-estate investment context.
    
    Designed to be initialized per-request with an async DB session,
    matching the pattern of MarketAnalyticsLayer.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_geopolitical_context(self, language: str = "en", max_events: int = 5) -> Optional[str]:
        """
        Main method: Returns a formatted geopolitical context prompt
        ready for injection into the Wolf Brain's narrative.
        
        Args:
            language: 'ar' or 'en' — matches user's detected language
            max_events: Maximum events to include (default 5 for token efficiency)
        
        Returns:
            Formatted prompt string or None if no events available
        """
        # Check cache first (5 minute TTL)
        cache_key = f"geopolitical_context:{language}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            events = await self._fetch_recent_events(max_events)
            if not events:
                return None

            prompt = self._format_context_prompt(events, language)

            # Cache for 5 minutes
            if prompt:
                cache.set(cache_key, prompt, ttl=300)

            return prompt

        except Exception as e:
            logger.warning(f"GeopoliticalLayer error (non-fatal): {e}")
            return None

    async def get_events_summary(self, max_events: int = 10) -> List[Dict[str, Any]]:
        """
        Return raw event data (for admin dashboard or API endpoints).
        """
        events = await self._fetch_recent_events(max_events)
        return [
            {
                "id": e.id,
                "title": e.title,
                "summary": e.summary,
                "category": e.category,
                "region": e.region,
                "impact_level": e.impact_level,
                "impact_tags": json.loads(e.impact_tags) if e.impact_tags else [],
                "real_estate_impact": e.real_estate_impact,
                "event_date": str(e.event_date) if e.event_date else None,
                "source": e.source,
            }
            for e in events
        ]

    async def get_macro_snapshot(self) -> Dict[str, Any]:
        """
        Build a quick macro-environment snapshot from recent events.
        Used for the compact economic context in analytics enrichment.
        """
        cache_key = "geopolitical_macro_snapshot"
        cached = cache.get_json(cache_key)
        if cached:
            return cached

        events = await self._fetch_recent_events(10)
        if not events:
            return {"has_data": False}

        # Aggregate signals
        categories_seen = set()
        high_impact_count = 0
        all_tags: List[str] = []

        for e in events:
            categories_seen.add(e.category)
            if e.impact_level == "high":
                high_impact_count += 1
            if e.impact_tags:
                try:
                    all_tags.extend(json.loads(e.impact_tags))
                except (json.JSONDecodeError, TypeError):
                    pass

        # Determine overall market sentiment
        risk_categories = {"conflict", "currency", "inflation", "construction_costs"}
        active_risks = categories_seen & risk_categories
        sentiment = "cautious" if len(active_risks) >= 2 else "neutral" if active_risks else "favorable"

        snapshot = {
            "has_data": True,
            "event_count": len(events),
            "high_impact_count": high_impact_count,
            "active_categories": list(categories_seen),
            "top_tags": list(set(all_tags))[:10],
            "market_sentiment": sentiment,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

        cache.set_json(cache_key, snapshot, ttl=300)
        return snapshot

    # ─────────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ─────────────────────────────────────────────────────────────

    async def _fetch_recent_events(self, limit: int = 5) -> List[GeopoliticalEvent]:
        """Fetch recent active events, prioritizing high impact."""
        try:
            # Fetch events from the last 30 days, active only
            cutoff = datetime.now(timezone.utc) - timedelta(days=30)

            stmt = (
                select(GeopoliticalEvent)
                .where(
                    and_(
                        GeopoliticalEvent.is_active == True,  # noqa: E712
                        GeopoliticalEvent.event_date >= cutoff,
                    )
                )
                .order_by(
                    # High impact first, then most recent
                    desc(
                        GeopoliticalEvent.impact_level == "high"  # noqa: E712
                    ),
                    desc(GeopoliticalEvent.event_date),
                )
                .limit(limit)
            )

            result = await self.db.execute(stmt)
            return list(result.scalars().all())

        except Exception as e:
            logger.warning(f"Failed to fetch geopolitical events: {e}")
            return []

    def _format_context_prompt(self, events: List[GeopoliticalEvent], language: str) -> str:
        """
        Transform events into a prompt injection for the Wolf Brain.
        The output is designed to be appended to the insight_instruction section
        of the narrative generation.
        """
        if not events:
            return ""

        # Header
        if language == "ar":
            lines = [
                "\n[إحاطة الاستخبارات الجيوسياسية — العيون على السوق]",
                "البيانات الحية التالية من مصادر موثقة — استخدمها لتعزيز مصداقيتك:",
            ]
        else:
            lines = [
                "\n[GEOPOLITICAL INTELLIGENCE BRIEFING — Eyes on the Market]",
                "The following LIVE intelligence is from verified sources — use it to reinforce your credibility:",
            ]

        # Event entries
        impact_icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}

        for event in events:
            icon = impact_icons.get(event.impact_level, "⚪")
            lines.append(f"\n{icon} {event.impact_level.upper()}: {event.title}")

            if event.real_estate_impact:
                lines.append(f"   → {event.real_estate_impact[:200]}")

            # Add actionable strategy based on impact tags
            strategies = self._get_strategies_for_event(event, language)
            for s in strategies[:2]:  # Max 2 strategies per event
                lines.append(f"   💡 {s}")

        # Overall advisory
        high_count = sum(1 for e in events if e.impact_level == "high")
        if high_count >= 2:
            if language == "ar":
                lines.append(
                    "\n📊 تقييم شامل: بيئة عالية المخاطر = عقارات كمخزن قيمة. "
                    "ركّز على: أوف بلان بأقساط طويلة + وحدات جاهزة كملاذات آمنة."
                )
            else:
                lines.append(
                    "\n📊 OVERALL ASSESSMENT: High-volatility environment = real estate as safe haven. "
                    "FOCUS: Off-plan with long payment plans + ready units as inflation shields."
                )

        # Instructions for the AI
        if language == "ar":
            lines.append(
                "\nتعليمات: ادمج المعلومات دي بشكل طبيعي في كلامك كخبير مطلع. "
                "لا تقرأ الأخبار حرفيًا — استخدمها كسياق لتبرير توصياتك الاستثمارية. "
                "مثال: 'مع اضطرابات البحر الأحمر اللي بترفع تكاليف البناء، "
                "شراء أوف بلان دلوقتي بيحميك من زيادات الأسعار المتوقعة.'"
            )
        else:
            lines.append(
                "\nINSTRUCTION: Weave this intelligence NATURALLY into your advice as an informed insider. "
                "Do NOT recite news headlines — use them as context to justify your investment recommendations. "
                "Example: 'Given the Red Sea supply chain disruptions pushing construction costs up, "
                "buying off-plan now locks in your price before the developer's next price adjustment.'"
            )

        return "\n".join(lines)

    def _get_strategies_for_event(self, event: GeopoliticalEvent, language: str) -> List[str]:
        """Extract actionable strategies from an event's impact tags."""
        strategies: List[str] = []

        if not event.impact_tags:
            return strategies

        try:
            tags = json.loads(event.impact_tags)
        except (json.JSONDecodeError, TypeError):
            return strategies

        lang_key = "strategy_ar" if language == "ar" else "strategy_en"

        for tag in tags:
            if tag in STRATEGY_MAP:
                strategies.append(STRATEGY_MAP[tag][lang_key])

        return strategies
