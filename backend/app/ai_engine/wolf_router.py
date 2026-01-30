"""
Wolf Router - Query Classification Layer
-----------------------------------------
Fast, rule-based + GPT-4o Mini routing to determine query handling.

Routes:
- GENERAL/QUICK → GPT-4o Chat (greetings, simple questions)
- REAL_ESTATE/COMPLEX → Wolf Brain Orchestrator (searches, valuations)
"""

import os
import logging
from enum import Enum
from typing import Dict, List, Optional, Tuple
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class RouteType(Enum):
    """Query routing destinations."""
    GENERAL = "general"           # Simple greetings, off-topic
    SEARCH = "search"             # Property searches
    VALUATION = "valuation"       # Price checks, valuations
    INVESTMENT = "investment"     # ROI, returns, investment analysis
    COMPARISON = "comparison"     # Compare properties/areas
    OBJECTION = "objection"       # Price/timing objections
    LEGAL = "legal"               # Contract, law questions
    PAYMENT = "payment"           # Installments, payment plans
    RESERVATION = "reservation"   # Book viewing, reserve unit


class RouteDecision:
    """Result of routing decision."""
    
    def __init__(
        self,
        route_type: RouteType,
        confidence: float,
        use_hybrid_brain: bool,
        reason: str
    ):
        self.route_type = route_type
        self.confidence = confidence
        self.use_hybrid_brain = use_hybrid_brain
        self.reason = reason
    
    def to_dict(self) -> Dict:
        return {
            "route_type": self.route_type.value,
            "confidence": self.confidence,
            "use_hybrid_brain": self.use_hybrid_brain,
            "reason": self.reason
        }


# Keyword patterns for fast rule-based routing
ROUTE_PATTERNS = {
    RouteType.GENERAL: [
        # Greetings
        r"^(hi|hello|hey|مرحبا|أهلا|السلام|صباح|مساء|ازيك|ازاي|عامل ايه)",
        r"^(thanks|thank you|شكرا|متشكر)",
        r"^(bye|goodbye|مع السلامة|باي)",
        # Off-topic
        r"(weather|طقس|news|أخبار|joke|نكتة)",
    ],
    RouteType.SEARCH: [
        r"(شقة|apartment|flat|فيلا|villa|بنتهاوس|penthouse|دوبلكس|duplex|تاون|townhouse)",
        r"(عايز|أريد|أبحث|looking for|searching|find me|show me|أبي)",
        r"(غرف|غرفة|bedroom|bed|room)",
        r"(متر|sqm|square meter|مساحة|area)",
        r"(كمباوند|compound|مشروع|project)",
        r"(زايد|zayed|التجمع|cairo|القاهرة|العاصمة|capital|أكتوبر|october|الساحل|coast|مدينتي|madinaty)",
    ],
    RouteType.VALUATION: [
        r"(سعر|price|تقييم|valuation|قيمة|value|غالي|expensive|رخيص|cheap)",
        r"(fair|عادل|market|سوق|overpriced|مبالغ)",
        r"(يستاهل|worth|كام|how much)",
    ],
    RouteType.INVESTMENT: [
        r"(استثمار|invest|عائد|return|roi|ربح|profit|إيجار|rent|rental)",
        r"(yield|growth|نمو|appreciation|inflation|تضخم)",
        r"(بنك|bank|شهادات|certificates|ذهب|gold)",
    ],
    RouteType.COMPARISON: [
        r"(مقارنة|compare|قارن|vs|versus|مقابل|أفضل|better|أحسن)",
        r"(difference|فرق|which|أي|choose|اختار)",
    ],
    RouteType.OBJECTION: [
        r"(غالي|expensive|مش فاضي|busy|مش مستعجل|not urgent|محتاج وقت|need time)",
        r"(أفكر|think about|بعدين|later|مش متأكد|not sure)",
        r"(منافس|competitor|nawy|نوي|aqarmap|عقارماب)",
    ],
    RouteType.LEGAL: [
        r"(عقد|contract|قانون|law|114|ضمان|guarantee|تسجيل|register)",
        r"(ملكية|ownership|توكيل|power of attorney|شهر عقاري)",
    ],
    RouteType.PAYMENT: [
        r"(قسط|installment|دفع|payment|مقدم|down payment)",
        r"(تقسيط|financing|شهري|monthly|سنوات|years)",
    ],
    RouteType.RESERVATION: [
        r"(حجز|reserve|book|معاينة|viewing|زيارة|visit)",
        r"(موعد|appointment|أزور|want to see|أشوف)",
    ],
}

# Routes that require full Hybrid Brain processing
HYBRID_BRAIN_ROUTES = {
    RouteType.SEARCH,
    RouteType.VALUATION,
    RouteType.INVESTMENT,
    RouteType.COMPARISON,
    RouteType.OBJECTION,
    RouteType.LEGAL,
    RouteType.PAYMENT,
    RouteType.RESERVATION,
}


class WolfRouter:
    """
    The Wolf's First Filter - Route queries to appropriate handlers.
    
    Uses fast rule-based matching first, then GPT-4o Mini for ambiguous queries.
    """
    
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.stats = {
            "rule_based": 0,
            "llm_fallback": 0,
        }
    
    async def route(
        self,
        query: str,
        history: Optional[List[Dict]] = None
    ) -> RouteDecision:
        """
        Determine the best route for a query.
        
        Args:
            query: User's message
            history: Conversation history
            
        Returns:
            RouteDecision with routing information
        """
        import re
        
        query_lower = query.lower().strip()
        
        # STEP 1: Fast rule-based routing
        matched_routes = []
        
        for route_type, patterns in ROUTE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    matched_routes.append(route_type)
                    break
        
        # If we found clear matches
        if len(matched_routes) == 1:
            route = matched_routes[0]
            self.stats["rule_based"] += 1
            logger.info(f"🔀 Router (rule-based): {route.value}")
            
            return RouteDecision(
                route_type=route,
                confidence=0.9,
                use_hybrid_brain=route in HYBRID_BRAIN_ROUTES,
                reason=f"Pattern match: {route.value}"
            )
        
        # If multiple matches, prioritize real estate routes
        if len(matched_routes) > 1:
            # Filter to hybrid brain routes (real estate focused)
            re_routes = [r for r in matched_routes if r in HYBRID_BRAIN_ROUTES]
            if re_routes:
                # Prioritize search > investment > valuation > others
                priority = [RouteType.SEARCH, RouteType.INVESTMENT, RouteType.VALUATION]
                for p in priority:
                    if p in re_routes:
                        self.stats["rule_based"] += 1
                        logger.info(f"🔀 Router (priority): {p.value}")
                        return RouteDecision(
                            route_type=p,
                            confidence=0.8,
                            use_hybrid_brain=True,
                            reason=f"Priority match from {len(matched_routes)} candidates"
                        )
                
                # Default to first RE route
                route = re_routes[0]
                self.stats["rule_based"] += 1
                return RouteDecision(
                    route_type=route,
                    confidence=0.75,
                    use_hybrid_brain=True,
                    reason=f"Best match from {len(matched_routes)} candidates"
                )
        
        # STEP 2: No clear match - use GPT-4o Mini for classification
        route = await self._classify_with_llm(query, history)
        self.stats["llm_fallback"] += 1
        logger.info(f"🔀 Router (LLM): {route.value}")
        
        return RouteDecision(
            route_type=route,
            confidence=0.85,
            use_hybrid_brain=route in HYBRID_BRAIN_ROUTES,
            reason="LLM classification"
        )
    
    async def _classify_with_llm(
        self,
        query: str,
        history: Optional[List[Dict]] = None
    ) -> RouteType:
        """
        Use GPT-4o Mini for ambiguous query classification.
        """
        try:
            system_prompt = """You are a query classifier for Osool, an Egyptian real estate AI.
            
Classify the user's query into ONE of these categories:
- general: Greetings, thanks, off-topic, small talk
- search: Looking for properties (apartments, villas, locations)
- valuation: Price questions, is this fair, market value
- investment: ROI, returns, inflation, investment analysis
- comparison: Compare properties, areas, developers
- objection: Concerns about price, timing, competitors
- legal: Contract, law, ownership questions
- payment: Installments, down payment, financing
- reservation: Book viewing, reserve unit, appointments

Return ONLY the category name, nothing else."""

            messages = [{"role": "user", "content": query}]
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    *messages
                ],
                max_tokens=20,
                temperature=0
            )
            
            category = response.choices[0].message.content.strip().lower()
            
            # Map to RouteType
            route_map = {
                "general": RouteType.GENERAL,
                "search": RouteType.SEARCH,
                "valuation": RouteType.VALUATION,
                "investment": RouteType.INVESTMENT,
                "comparison": RouteType.COMPARISON,
                "objection": RouteType.OBJECTION,
                "legal": RouteType.LEGAL,
                "payment": RouteType.PAYMENT,
                "reservation": RouteType.RESERVATION,
            }
            
            return route_map.get(category, RouteType.SEARCH)  # Default to search
            
        except Exception as e:
            logger.warning(f"LLM classification failed: {e}")
            # Default to search for real estate platform
            return RouteType.SEARCH
    
    def get_stats(self) -> Dict:
        """Get routing statistics."""
        total = self.stats["rule_based"] + self.stats["llm_fallback"]
        return {
            **self.stats,
            "total": total,
            "rule_based_percent": (self.stats["rule_based"] / max(total, 1)) * 100
        }


# Singleton instance
wolf_router = WolfRouter()

__all__ = ["WolfRouter", "wolf_router", "RouteType", "RouteDecision"]
