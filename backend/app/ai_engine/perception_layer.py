"""
Perception Layer - Intent Extraction Engine
--------------------------------------------
GPT-4o powered intent extraction and filter parsing.

Extracts:
- Action type (search, valuation, objection, general)
- Filters (location, budget, bedrooms, property_type, etc.)
- Language detection (ar/en)
- Conversation phase tracking
"""

import os
import json
import logging
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


@dataclass
class Intent:
    """Parsed intent from user query."""
    
    action: str  # search, valuation, objection, general, comparison, investment
    filters: Dict[str, Any] = field(default_factory=dict)
    language: str = "ar"  # ar or en
    confidence: float = 0.9
    raw_query: str = ""
    intent_bucket: str = "window_shopper" # window_shopper, serious_buyer, objection_mode
    
    def to_dict(self) -> Dict:
        return {
            "action": self.action,
            "filters": self.filters,
            "language": self.language,
            "confidence": self.confidence,
            "raw_query": self.raw_query,
            "intent_bucket": self.intent_bucket
        }


# Location normalization mappings
LOCATION_ALIASES = {
    # New Cairo variants
    "التجمع": "New Cairo",
    "التجمع الخامس": "New Cairo",
    "التجمع الخامس": "New Cairo",
    "القاهرة الجديدة": "New Cairo",
    "new cairo": "New Cairo",
    "5th settlement": "New Cairo",
    
    # Sheikh Zayed variants
    "زايد": "Sheikh Zayed",
    "الشيخ زايد": "Sheikh Zayed",
    "sheikh zayed": "Sheikh Zayed",
    "el sheikh zayed": "Sheikh Zayed",
    
    # New Capital variants
    "العاصمة": "New Capital",
    "العاصمة الإدارية": "New Capital",
    "العاصمة الادارية": "New Capital",
    "new capital": "New Capital",
    "new administrative capital": "New Capital",
    "nac": "New Capital",
    
    # 6th October variants
    "أكتوبر": "6th October",
    "اكتوبر": "6th October",
    "6 أكتوبر": "6th October",
    "6th october": "6th October",
    "6 october": "6th October",
    
    # North Coast variants
    "الساحل": "North Coast",
    "الساحل الشمالي": "North Coast",
    "north coast": "North Coast",
    "sahel": "North Coast",
    
    # Madinaty variants
    "مدينتي": "Madinaty",
    "madinaty": "Madinaty",
    
    # Maadi variants
    "المعادي": "Maadi",
    "madinaty": "Madinaty",
    
    # Maadi variants
    "المعادي": "Maadi",
    "معادي": "Maadi",
    "maadi": "Maadi",
    
    # Rehab variants
    "الرحاب": "Rehab",
    "رحاب": "Rehab",
    "rehab": "Rehab",
    
}

# Property type normalization
PROPERTY_TYPE_ALIASES = {
    "شقة": "apartment",
    "شقه": "apartment",
    "apartment": "apartment",
    "flat": "apartment",
    
    "فيلا": "villa",
    "فيللا": "villa",
    "villa": "villa",
    
    "تاون هاوس": "townhouse",
    "تاونهاوس": "townhouse",
    "تاون": "townhouse",
    "townhouse": "townhouse",
    "town house": "townhouse",
    
    "توين هاوس": "twinhouse",
    "توينهاوس": "twinhouse",
    "توين": "twinhouse",
    "twinhouse": "twinhouse",
    "twin house": "twinhouse",
    
    "بنتهاوس": "penthouse",
    "بنت هاوس": "penthouse",
    "penthouse": "penthouse",
    
    "دوبلكس": "duplex",
    "duplex": "duplex",
    
    "ستوديو": "studio",
    "studio": "studio",
    
    "مكتب": "office",
    "اوفيس": "office",
    "office": "office",
}


class PerceptionLayer:
    """
    The Wolf's Eyes - Extract intent and filters from natural language.
    
    Uses GPT-4o for robust extraction with fallback to rule-based parsing.
    """
    
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.stats = {
            "llm_extractions": 0,
            "rule_based_extractions": 0,
            "failures": 0
        }
    
    def detect_language(self, text: str) -> str:
        """Detect if text is primarily Arabic or English."""
        if not text:
            return "en"
        
        arabic_pattern = re.compile(r'[\u0600-\u06FF]')
        arabic_chars = len(arabic_pattern.findall(text))
        total_chars = len(text.replace(" ", ""))
        
        if total_chars == 0:
            return "en"
        
        arabic_ratio = arabic_chars / total_chars
        return "ar" if arabic_ratio > 0.3 else "en"
    
    async def analyze(
        self,
        query: str,
        history: Optional[List[Dict]] = None
    ) -> Intent:
        """
        Extract intent and filters from user query.
        
        Args:
            query: User's natural language query
            history: Conversation history for context
            
        Returns:
            Intent object with action and filters
        """
        language = self.detect_language(query)
        
        try:
            # Use GPT-4o for robust extraction
            intent_data = await self._extract_with_llm(query, history)
            self.stats["llm_extractions"] += 1
            
            # Normalize extracted data
            intent_data = self._normalize_filters(intent_data)
            
            return Intent(
                action=intent_data.get("action", "search"),
                filters=intent_data.get("filters", {}),
                language=language,
                confidence=0.9,
                raw_query=query,
                intent_bucket=intent_data.get("intent_bucket", "window_shopper")
            )
            
        except Exception as e:
            logger.warning(f"LLM extraction failed, using rule-based: {e}")
            self.stats["failures"] += 1
            
            # Fallback to rule-based extraction
            intent_data = self._extract_rule_based(query)
            self.stats["rule_based_extractions"] += 1
            
            return Intent(
                action=intent_data.get("action", "search"),
                filters=intent_data.get("filters", {}),
                language=language,
                confidence=0.7,
                raw_query=query,
                intent_bucket="window_shopper" # Default fallback
            )
    
    async def _extract_with_llm(
        self,
        query: str,
        history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Use GPT-4o to extract structured intent."""
        
        system_prompt = """You are the Perception Layer of Osool, an Egyptian Real Estate AI.
        
Extract structured intent from the user's query. Return ONLY valid JSON (no markdown, no code fences).

Extract:
1. action: One of: search, valuation, objection, general, comparison, investment, legal, payment, reservation
2. intent_bucket: One of:
    - "window_shopper": Casual browsing, broad questions
    - "serious_buyer": Specific budget, timeline, ready to book
    - "objection_mode": Complaining, debating price, skeptical
3. filters: Object with these optional fields:
   - location: Area name (New Cairo, Sheikh Zayed, New Capital, 6th October, North Coast, etc.)
   - budget_min: Minimum budget in EGP (convert millions: 5M = 5000000)
   - budget_max: Maximum budget in EGP
   - purpose: "living" OR "investment" OR "commercial" (CRITICAL: Infer from context!)
   - bedrooms: Number of bedrooms (integer)
   - property_type: apartment, villa, townhouse, twinhouse, penthouse, duplex, studio
   - size_min: Minimum size in sqm
   - size_max: Maximum size in sqm
   - developer: Developer name if mentioned
   - keywords: Any specific compound/project names mentioned
   - finishing: core, semi, finished, lux

CONTEXT RULES FOR 'purpose' (CRITICAL - infer meaning, not just keywords):
- FAMILY LIVING (purpose: "living"): "سكن عائلي", "بيت العيلة", "بيت للعيلة", "استقرار", "مدارس", "سكن", "عيلة", "اولاد", "اعيش", "منزل", "home", "family", "kids", "children", "stay", "live", "marriage", "private", "wife"
- INVESTMENT (purpose: "investment"): "ROI", "rent", "income", "profit", "business", "yield", "return", "flip", "resale", "استثمار", "عائد", "ايجار", "ارباح"
- COMMERCIAL (purpose: "commercial"): "office", "shop", "clinic", "commercial", "مكتب", "محل", "عيادة", "تجاري"
- CAPITAL PRESERVATION: "فلوس البنك", "تحويشة العمر", "حفظ قيمة" -> purpose: "investment" (sub-type: preservation)

INTENT BUCKET RULES (CRITICAL):
- "serious_buyer": If user mentions FAMILY, CHILDREN, MARRIAGE, LIVING, or specific BUDGET + LOCATION = This is a LIFE DECISION MAKER, not a window shopper.
- "serious_buyer": budget OR delivery timeline OR specific location = Serious
- "window_shopper": Generic questions like "show me everything" or "how is the market"
- "objection_mode": Complaining, debating price, skeptical language

Example query: "عايز شقة 3 غرف في التجمع تحت 5 مليون"
Example response:
{
  "action": "search",
  "intent_bucket": "serious_buyer",
  "filters": {
    "location": "New Cairo",
    "bedrooms": 3,
    "budget_max": 5000000,
    "property_type": "apartment"
  }
}

Example query: "بدور على سكن عائلي قريب من مدارس"
Example response:
{
  "action": "search",
  "intent_bucket": "serious_buyer",
  "filters": {
    "purpose": "living",
    "keywords": "family, schools, community"
  }
}

Example query: "I want a place for my kids near schools"
Example response:
{
  "action": "search",
  "intent_bucket": "serious_buyer",
  "filters": {
    "purpose": "living",
    "keywords": "kids, schools"
  }
}

Example query: "ده سعر غالي ولا لأ؟"
Example response:
{
  "action": "valuation",
  "intent_bucket": "objection_mode",
  "filters": {}
}

IMPORTANT: 
- Convert Arabic numbers to integers
- Convert "مليون" (million) to actual number (5 مليون = 5000000)
- Normalize locations to English names
- INFER purpose from context even if not explicitly stated
- "سكن عائلي" = purpose: "living" + intent_bucket: "serious_buyer"
- Return ONLY the JSON object, nothing else"""

        messages = []
        
        # Add relevant history for context
        if history:
            for msg in history[-4:]:  # Last 4 messages
                if isinstance(msg, dict):
                    messages.append(msg)
        
        messages.append({"role": "user", "content": query})
        
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                *messages
            ],
            max_tokens=300,
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Ensure required fields
        if "action" not in result:
            result["action"] = "search"
        if "filters" not in result:
            result["filters"] = {}
        
        return result
    
    def _extract_rule_based(self, query: str) -> Dict[str, Any]:
        """Fallback rule-based extraction."""
        query_lower = query.lower()
        filters = {}
        action = "search"
        
        # Detect action type
        if any(w in query_lower for w in ["سعر", "غالي", "رخيص", "قيمة", "يستاهل", "fair", "price", "worth"]):
            action = "valuation"
        elif any(w in query_lower for w in ["استثمار", "عائد", "roi", "إيجار", "rent", "return"]):
            action = "investment"
        elif any(w in query_lower for w in ["مقارنة", "compare", "vs", "أفضل", "better"]):
            action = "comparison"
        elif any(w in query_lower for w in ["حجز", "reserve", "معاينة", "viewing"]):
            action = "reservation"
        
        # Extract location
        for alias, normalized in LOCATION_ALIASES.items():
            if alias in query_lower:
                filters["location"] = normalized
                break
        
        # Extract property type
        for alias, normalized in PROPERTY_TYPE_ALIASES.items():
            if alias in query_lower:
                filters["property_type"] = normalized
                break
        
        # Extract bedrooms
        bedroom_match = re.search(r'(\d+)\s*(غرف|غرفة|bedroom|bed|room)', query_lower)
        if bedroom_match:
            filters["bedrooms"] = int(bedroom_match.group(1))
        
        # Extract budget
        budget_match = re.search(r'(\d+(?:\.\d+)?)\s*(مليون|million|m)', query_lower)
        if budget_match:
            amount = float(budget_match.group(1)) * 1_000_000
            if "تحت" in query_lower or "under" in query_lower or "أقل" in query_lower:
                filters["budget_max"] = int(amount)
            elif "فوق" in query_lower or "over" in query_lower or "أكتر" in query_lower:
                filters["budget_min"] = int(amount)
            else:
                filters["budget_max"] = int(amount * 1.2)  # Add 20% buffer
                filters["budget_min"] = int(amount * 0.8)
        
        return {"action": action, "filters": filters}
    
    def _normalize_filters(self, intent_data: Dict) -> Dict:
        """Normalize extracted filters to standard format."""
        filters = intent_data.get("filters", {})
        
        # Normalize location
        if "location" in filters:
            loc = filters["location"].lower()
            for alias, normalized in LOCATION_ALIASES.items():
                if alias in loc or loc in alias:
                    filters["location"] = normalized
                    break
        
        # Normalize property type
        if "property_type" in filters:
            ptype = filters["property_type"].lower()
            filters["property_type"] = PROPERTY_TYPE_ALIASES.get(ptype, ptype)
        
        # Ensure budget is integer
        if "budget_min" in filters:
            filters["budget_min"] = int(filters["budget_min"])
        if "budget_max" in filters:
            filters["budget_max"] = int(filters["budget_max"])
        
        intent_data["filters"] = filters
        return intent_data
    
    def get_stats(self) -> Dict:
        """Get extraction statistics."""
        total = self.stats["llm_extractions"] + self.stats["rule_based_extractions"]
        return {
            **self.stats,
            "total": total,
            "success_rate": ((total - self.stats["failures"]) / max(total, 1)) * 100
        }


# Singleton instance
perception_layer = PerceptionLayer()

__all__ = ["PerceptionLayer", "perception_layer", "Intent"]
