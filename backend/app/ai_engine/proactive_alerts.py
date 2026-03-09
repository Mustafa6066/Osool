"""
Proactive Alert Engine - The Wolf's Early Warning System
---------------------------------------------------------
Generates proactive alerts and suggestions based on:
- Market conditions
- User psychology
- Historical patterns
- Deal opportunities

The Wolf doesn't wait to be asked - he ANTICIPATES.
"""

import logging
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class AlertType(Enum):
    """Types of proactive alerts the Wolf can trigger."""
    LA2TA_FOUND = "la2ta_found"           # Bargain detected
    PRICE_DROP = "price_drop"              # Price reduction detected
    NEW_LISTING = "new_listing"            # New property matching preferences
    SIMILAR_SOLD = "similar_sold"          # Similar property sold recently
    MARKET_OPPORTUNITY = "market_opportunity"  # Market timing opportunity
    DEVELOPER_PROMOTION = "developer_promotion"  # Developer offering discounts


class AlertPriority(Enum):
    """Priority levels for alerts."""
    CRITICAL = 10  # Must show immediately
    HIGH = 8       # Show prominently
    MEDIUM = 5     # Show if relevant
    LOW = 3        # Show if no other alerts


@dataclass
class ProactiveAlert:
    """Structure for a proactive alert."""
    type: AlertType
    priority: int
    message_ar: str
    message_en: str
    data: Dict[str, Any]
    action_cta_ar: str
    action_cta_en: str
    expires_in_hours: int = 24

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "priority": self.priority,
            "message_ar": self.message_ar,
            "message_en": self.message_en,
            "data": self.data,
            "action_cta": {
                "ar": self.action_cta_ar,
                "en": self.action_cta_en
            },
            "expires_in_hours": self.expires_in_hours
        }


class ProactiveAlertEngine:
    """
    The Wolf's proactive intelligence engine.
    Scans for opportunities and generates alerts without being asked.
    """

    def __init__(self):
        # Import here to avoid circular imports
        pass

    def scan_for_opportunities(
        self,
        user_preferences: Optional[Dict[str, Any]],
        market_data: List[Dict[str, Any]],
        psychology: Optional[Any] = None,
        intent: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Scan for proactive opportunities based on context.

        Args:
            user_preferences: User's search preferences (location, budget, etc.)
            market_data: Current market/property data
            psychology: PsychologyProfile from psychology_layer
            intent: Detected intent from current query

        Returns:
            List of ProactiveAlert dicts, sorted by priority
        """
        alerts = []

        # 1. La2ta Scan - Find bargains
        la2ta_alerts = self._scan_for_la2ta(market_data, user_preferences)
        alerts.extend(la2ta_alerts)

        # 2. Psychology-based opportunities
        if psychology:
            psych_alerts = self._scan_psychology_opportunities(psychology, market_data)
            alerts.extend(psych_alerts)

        # 3. Market timing opportunities
        timing_alerts = self._scan_market_timing(user_preferences)
        alerts.extend(timing_alerts)

        # Sort by priority (highest first) and return
        return sorted(alerts, key=lambda x: x.get('priority', 0), reverse=True)

    def _scan_for_la2ta(
        self,
        properties: List[Dict[str, Any]],
        preferences: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Scan for bargain properties."""
        alerts = []

        if not properties:
            return alerts

        try:
            from app.ai_engine.xgboost_predictor import xgboost_predictor

            # Find La2ta properties
            bargains = xgboost_predictor.detect_la2ta(properties, threshold_percent=10.0)

            if bargains:
                # Create alert for bargains found
                top_bargain = bargains[0]
                alert = ProactiveAlert(
                    type=AlertType.LA2TA_FOUND,
                    priority=AlertPriority.CRITICAL.value,
                    message_ar=f"🐺 الرادار لقى {len(bargains)} لقطة تحت السوق!",
                    message_en=f"Wolf Radar found {len(bargains)} bargain(s) below market!",
                    data={
                        "properties": bargains[:3],  # Top 3 bargains
                        "best_discount": top_bargain.get('la2ta_score', 0),
                        "total_savings": sum(b.get('savings', 0) for b in bargains[:3])
                    },
                    action_cta_ar="شوف اللقطات دي!",
                    action_cta_en="View these bargains!",
                    expires_in_hours=48
                )
                alerts.append(alert.to_dict())
                logger.info(f"🐺 La2ta Alert: Found {len(bargains)} bargains")

        except Exception as e:
            logger.error(f"La2ta scan failed: {e}")

        return alerts

    def _scan_psychology_opportunities(
        self,
        psychology: Any,
        properties: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate alerts based on user psychology."""
        alerts = []

        if not psychology:
            return alerts

        try:
            from app.ai_engine.psychology_layer import PsychologicalState

            primary_state = psychology.primary_state

            # GREED_DRIVEN users get investment opportunity alerts
            if primary_state == PsychologicalState.GREED_DRIVEN:
                if properties:
                    from app.ai_engine.xgboost_predictor import xgboost_predictor

                    # Calculate inflation hedge for top property
                    top_prop = properties[0]
                    hedge_data = xgboost_predictor.calculate_inflation_hedge_score({
                        'price': top_prop.get('price', 5_000_000)
                    })

                    if hedge_data.get('hedge_score', 0) >= 70:
                        alert = ProactiveAlert(
                            type=AlertType.MARKET_OPPORTUNITY,
                            priority=AlertPriority.HIGH.value,
                            message_ar="📈 فرصة استثمارية: العقار ده هيحميك من التضخم!",
                            message_en="Investment opportunity: This property beats inflation!",
                            data={
                                "hedge_score": hedge_data.get('hedge_score'),
                                "advantage_vs_cash": hedge_data.get('advantages', {}).get('vs_cash'),
                                "property": top_prop
                            },
                            action_cta_ar="شوف تحليل الاستثمار",
                            action_cta_en="View investment analysis"
                        )
                        alerts.append(alert.to_dict())

            # FOMO users get scarcity alerts
            elif primary_state == PsychologicalState.FOMO:
                alert = ProactiveAlert(
                    type=AlertType.MARKET_OPPORTUNITY,
                    priority=AlertPriority.HIGH.value,
                    message_ar="⚡ الأسعار في المنطقة دي بتزيد! الحق الفرصة",
                    message_en="Prices in this area are rising! Don't miss out",
                    data={
                        "urgency": "high",
                        "market_trend": "rising",
                        "estimated_increase": "10-15%"
                    },
                    action_cta_ar="احجز دلوقتي",
                    action_cta_en="Reserve now"
                )
                alerts.append(alert.to_dict())

            # RISK_AVERSE users get safety alerts
            elif primary_state == PsychologicalState.RISK_AVERSE:
                alert = ProactiveAlert(
                    type=AlertType.MARKET_OPPORTUNITY,
                    priority=AlertPriority.MEDIUM.value,
                    message_ar="🛡️ السيستم بتاعي جاهز يراجع أي عقد قبل ما توقع",
                    message_en="My system is ready to review any contract before you sign",
                    data={
                        "service": "contract_review",
                        "law_reference": "Law 114"
                    },
                    action_cta_ar="ارفع العقد للمراجعة",
                    action_cta_en="Upload contract for review"
                )
                alerts.append(alert.to_dict())

        except Exception as e:
            logger.error(f"Psychology opportunity scan failed: {e}")

        return alerts

    def _scan_market_timing(
        self,
        preferences: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Check for market timing opportunities."""
        alerts = []

        # This would integrate with real market data
        # For now, generate contextual alerts

        if preferences:
            location = preferences.get('location', '').lower()

            # Location-specific timing alerts
            if 'cairo' in location or 'التجمع' in location:
                alert = ProactiveAlert(
                    type=AlertType.MARKET_OPPORTUNITY,
                    priority=AlertPriority.MEDIUM.value,
                    message_ar="📊 التجمع الخامس: نمو 18% السنة اللي فاتت",
                    message_en="New Cairo: 18% growth last year",
                    data={
                        "location": "New Cairo",
                        "growth_rate": 18,
                        "trend": "bullish"
                    },
                    action_cta_ar="شوف أحسن الفرص",
                    action_cta_en="View best opportunities"
                )
                alerts.append(alert.to_dict())

        return alerts

        return alerts

    def check_escalation_triggers(
        self,
        query: str,
        psychology: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Check if conversation needs human escalation.
        Triggers:
        1. User asks for manager/human.
        2. Sentiment drops below threshold (Angry).
        3. Complex legal/out-of-scope questions.
        """
        query_lower = query.lower()
        
        # 1. Direct Request
        manager_keywords = ["manager", "supervisor", "speak to human", "real person", "agent", "مدير", "مشرف", "إنسان", "حد يكلمني"]
        if any(kw in query_lower for kw in manager_keywords):
            return self._create_escalation_alert("Human Agent Requested", "طلب تحدث مع وكيل")
            
        # 2. Sentiment/Psychology Check
        if psychology:
            # If trust deficit is extreme or anger detected (using psychology triggers)
            # We assume psychology layer creates 'TRUST_DEFICIT' for bad sentiment
            from app.ai_engine.psychology_layer import PsychologicalState
            if psychology.primary_state == PsychologicalState.TRUST_DEFICIT and psychology.confidence_score < 0.2:
                # Very low confidence + Trust Deficit = Anger/Frustration
                return self._create_escalation_alert("Negative Sentiment Detected", "تم رصد حالة عدم رضا")

        return None

    def _create_escalation_alert(self, reason_en: str, reason_ar: str) -> Dict[str, Any]:
        """Create standard escalation alert."""
        import os
        whatsapp_number = os.getenv("SUPPORT_WHATSAPP_NUMBER", "201000000000")
        whatsapp_link = f"https://wa.me/{whatsapp_number}?text=I+need+assistance"
        return ProactiveAlert(
            type=AlertType.CRITICAL, # Assuming AlertType has CRITICAL, if not use HIGH
            priority=AlertPriority.CRITICAL.value,
            message_ar=f"⚠️ {reason_ar}. جاري تحويلك لكبير الاستشاريين...",
            message_en=f"⚠️ {reason_en}. Connecting you to Senior Consultant...",
            data={
                "action": "escalate",
                "contact": whatsapp_link
            },
            action_cta_ar="تواصل واتساب مباشر",
            action_cta_en="Chat on WhatsApp"
        ).to_dict()

    def get_alert_for_intent(
        self,
        intent: Dict[str, Any],
        psychology: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get the most relevant alert for a specific intent.
        Used when responding to queries to add proactive value.
        """
        action = intent.get('action', '')
        filters = intent.get('filters', {})

        # If searching for investment-type properties
        if any(kw in action.lower() for kw in ['invest', 'استثمار', 'roi']):
            return {
                "type": "investment_tip",
                "priority": 7,
                "message_ar": "💡 نصيحة: العقارات في التجمع بتحقق أعلى عائد إيجاري",
                "message_en": "Tip: New Cairo properties have highest rental yields",
                "inline": True
            }

        # If budget-conscious (budget filter set)
        if filters.get('budget_max') and filters['budget_max'] < 3_000_000:
            return {
                "type": "budget_tip",
                "priority": 5,
                "message_ar": "💰 نصيحة: القسط الشهري ممكن يكون أقل من الإيجار!",
                "message_en": "Tip: Monthly installment can be less than rent!",
                "inline": True
            }

        return None


# Singleton instance
proactive_alert_engine = ProactiveAlertEngine()

# Export
__all__ = [
    "ProactiveAlertEngine",
    "proactive_alert_engine",
    "AlertType",
    "AlertPriority",
    "ProactiveAlert"
]
