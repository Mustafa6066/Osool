"""
Proactive Intelligence Layer
-------------------------------
AI notices user patterns and proactively offers insights without being asked.

Triggers:
1. User viewed 3+ properties in same area → area market brief
2. User compared 2+ developers → developer showdown
3. User mentioned budget but hasn't used inflation calc → suggest it
4. User is HOT lead but hasn't asked about legal → offer Law 114 audit
5. User browsed 3+ sessions → show investment readiness score
"""

import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class ProactiveInsight:
    """A single proactive insight with trigger context."""
    def __init__(
        self,
        insight_type: str,
        message_ar: str,
        message_en: str,
        priority: int = 0,       # Higher = more important
        action: Optional[str] = None,  # Suggested action
        data: Optional[Dict] = None,
    ):
        self.insight_type = insight_type
        self.message_ar = message_ar
        self.message_en = message_en
        self.priority = priority
        self.action = action
        self.data = data or {}

    def to_dict(self, language: str = "ar") -> Dict:
        return {
            "type": self.insight_type,
            "message": self.message_ar if language == "ar" else self.message_en,
            "priority": self.priority,
            "action": self.action,
            "data": self.data,
        }


class ProactiveInsightsEngine:
    """
    Analyzes conversation context and generates proactive insights.
    Called between ANALYZE and STRATEGY phases in wolf_orchestrator.
    """

    def analyze(
        self,
        history: List[Dict],
        properties_viewed: List[Dict],
        tools_used: List[str],
        lead_score: int,
        user_memory: Optional[Dict] = None,
        session_count: int = 1,
    ) -> List[ProactiveInsight]:
        """
        Analyze conversation context and return proactive insights.
        Returns max 1 insight per turn to avoid overwhelming the user.
        """
        insights = []

        # 1. Area concentration detection
        area_insight = self._check_area_concentration(properties_viewed)
        if area_insight:
            insights.append(area_insight)

        # 2. Budget + inflation hedge
        inflation_insight = self._check_inflation_opportunity(
            history, tools_used, user_memory
        )
        if inflation_insight:
            insights.append(inflation_insight)

        # 3. Hot lead without legal check
        legal_insight = self._check_legal_gap(lead_score, tools_used)
        if legal_insight:
            insights.append(legal_insight)

        # 4. Multi-session user without readiness score
        readiness_insight = self._check_readiness_prompt(session_count, tools_used)
        if readiness_insight:
            insights.append(readiness_insight)

        # 5. Developer comparison opportunity
        dev_insight = self._check_developer_opportunity(properties_viewed, tools_used)
        if dev_insight:
            insights.append(dev_insight)

        # Sort by priority and return top 1
        insights.sort(key=lambda x: x.priority, reverse=True)
        return insights[:1]

    def _check_area_concentration(self, properties_viewed: List[Dict]) -> Optional[ProactiveInsight]:
        """User viewed 3+ properties in same area → area brief."""
        if not properties_viewed or len(properties_viewed) < 3:
            return None

        area_counts: Dict[str, int] = {}
        for prop in properties_viewed:
            area = prop.get("location", "")
            if area:
                area_counts[area] = area_counts.get(area, 0) + 1

        for area, count in area_counts.items():
            if count >= 3:
                return ProactiveInsight(
                    insight_type="area_concentration",
                    message_ar=f"لاحظت إنك بتركز على {area} - عايزني أعملك تحليل شامل للمنطقة دي؟ هعرفك متوسط سعر المتر، أحسن المطورين، واتجاه الأسعار.",
                    message_en=f"I noticed you're focused on {area} — want me to generate a full area intelligence report? I'll cover average price/sqm, top developers, and price trends.",
                    priority=80,
                    action="area_analysis",
                    data={"area": area, "properties_viewed": count},
                )
        return None

    def _check_inflation_opportunity(
        self,
        history: List[Dict],
        tools_used: List[str],
        user_memory: Optional[Dict],
    ) -> Optional[ProactiveInsight]:
        """User mentioned budget but hasn't used inflation calculator."""
        if "inflation_killer" in tools_used or "certificates_vs_property" in tools_used:
            return None  # Already used

        # Check if budget was mentioned
        has_budget = False
        if user_memory and (user_memory.get("budget_min") or user_memory.get("budget_max")):
            has_budget = True

        if not has_budget:
            # Check history for budget mentions
            budget_keywords = ["ميزانيت", "budget", "مليون", "million", "فلوس", "money"]
            for msg in history[-10:]:
                content = msg.get("content", "").lower()
                if any(kw in content for kw in budget_keywords):
                    has_budget = True
                    break

        if has_budget:
            return ProactiveInsight(
                insight_type="inflation_opportunity",
                message_ar="بما إنك حددت ميزانية - عايز أوريك إزاي العقار بيحمي فلوسك من التضخم مقارنة بالبنك والدهب؟",
                message_en="Since you've defined a budget — want me to show how property protects your capital against inflation vs. bank deposits and gold?",
                priority=60,
                action="inflation_killer",
            )
        return None

    def _check_legal_gap(self, lead_score: int, tools_used: List[str]) -> Optional[ProactiveInsight]:
        """Hot lead without legal check → suggest Law 114."""
        if lead_score < 65:
            return None
        if "law_114_guardian" in tools_used or "audit_contract" in tools_used:
            return None

        return ProactiveInsight(
            insight_type="legal_gap",
            message_ar="حضرتك قريب من قرار الشراء - أنصحك تعمل مراجعة قانونية (قانون 114) قبل ما توقع. عايزني أبدأ؟",
            message_en="You're close to a buying decision — I recommend a legal review (Law 114) before signing. Should I start?",
            priority=90,
            action="law_114_guardian",
        )

    def _check_readiness_prompt(self, session_count: int, tools_used: List[str]) -> Optional[ProactiveInsight]:
        """Multi-session user → show readiness score."""
        if session_count < 3:
            return None
        if "readiness_score" in tools_used:
            return None

        return ProactiveInsight(
            insight_type="readiness_prompt",
            message_ar="ده ثالث جلسة ليك - عايز أحسبلك 'درجة جاهزية الاستثمار' بتاعتك؟ هتعرف إيه اللي لسه ناقصك.",
            message_en="This is your 3rd session — want me to calculate your Investment Readiness Score? It shows what's still missing.",
            priority=50,
            action="readiness_score",
        )

    def _check_developer_opportunity(
        self,
        properties_viewed: List[Dict],
        tools_used: List[str],
    ) -> Optional[ProactiveInsight]:
        """User viewed properties from 2+ developers → developer comparison."""
        if "developer_analysis" in tools_used:
            return None

        developers = set()
        for prop in properties_viewed:
            dev = prop.get("developer", "")
            if dev:
                developers.add(dev)

        if len(developers) >= 2:
            devs = list(developers)[:3]
            return ProactiveInsight(
                insight_type="developer_comparison",
                message_ar=f"شفت مشاريع من {' و '.join(devs)} - عايزني أعملك مقارنة بين المطورين دول؟ هعرفك مين أحسن في التسليم والجودة.",
                message_en=f"You've viewed projects from {' and '.join(devs)} — want a developer showdown? I'll compare delivery records and quality.",
                priority=70,
                action="developer_analysis",
                data={"developers": devs},
            )
        return None


# Singleton
proactive_engine = ProactiveInsightsEngine()
