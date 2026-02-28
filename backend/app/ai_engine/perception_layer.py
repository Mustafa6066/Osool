"""
Perception Layer - Intent Extraction Engine
--------------------------------------------
GPT-4o-mini powered intent extraction with Pydantic Structured Outputs.

Upgrades (v2):
- Pydantic structured outputs (schema-validated, no JSON parsing errors)
- Semantic caching (hash-based, avoids repeat LLM calls)
- GPT-4o-mini (faster + cheaper for structured extraction)
- Retry with tenacity
"""

import os
import json
import logging
import hashlib
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

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
    
    # Sakan A'eli (Investment Product) - ONLY Explicit Types
    "عمارة": "residential_building",
    "بيت كامل": "residential_building",
    "building": "residential_building",
    
    # Land/Plots
    "ارض": "plot",
    "اراضي": "plot",
    "plot": "plot",
    "land": "plot",

    # General housing terms (Egyptian colloquial)
    "سكن": "apartment",
    "سكن عائلي": "villa",
    "بيت": "apartment",
    "منزل": "apartment",
}


class PerceptionLayer:
    """
    The Wolf's Eyes - Extract intent and filters from natural language.
    
    Uses GPT-4o-mini with Pydantic Structured Outputs for robust extraction.
    Includes in-memory semantic cache to avoid repeat LLM calls.
    """
    
    # ── Pydantic schema for OpenAI Structured Outputs ──
    class IntentExtraction(BaseModel):
        """Structured intent extracted from user query."""
        action: str = Field(
            description="One of: search, valuation, objection, general, comparison, investment, legal, payment, reservation"
        )
        intent_bucket: str = Field(
            default="window_shopper",
            description="One of: window_shopper, serious_buyer, objection_mode"
        )
        filters: Dict[str, Any] = Field(
            default_factory=dict,
            description="Extracted filters: location, budget_min, budget_max, purpose, bedrooms, property_type, size_min, size_max, developer, keywords, finishing"
        )
    
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.stats = {
            "llm_extractions": 0,
            "rule_based_extractions": 0,
            "cache_hits": 0,
            "failures": 0,
        }
        # Semantic cache: hash(query + last_2_history) -> Intent
        self._intent_cache: Dict[str, Intent] = {}
        self._CACHE_MAX = 500
    
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
        
        Uses hash-based semantic cache to avoid repeated LLM calls
        for identical or near-identical queries.
        """
        language = self.detect_language(query)
        
        # ── Semantic cache lookup ──
        cache_key = self._make_cache_key(query, history)
        if cache_key in self._intent_cache:
            self.stats["cache_hits"] += 1
            cached = self._intent_cache[cache_key]
            logger.debug(f"🎯 Perception cache hit for: {query[:30]}...")
            return cached
        
        try:
            # Use GPT-4o-mini with Pydantic Structured Outputs
            intent_data = await self._extract_with_llm(query, history)
            self.stats["llm_extractions"] += 1
            
            # Normalize extracted data
            intent_data = self._normalize_filters(intent_data)
            
            intent = Intent(
                action=intent_data.get("action", "search"),
                filters=intent_data.get("filters", {}),
                language=language,
                confidence=0.95,  # Higher confidence with structured outputs
                raw_query=query,
                intent_bucket=intent_data.get("intent_bucket", "window_shopper")
            )
            
            # Cache the result
            self._cache_intent(cache_key, intent)
            return intent
            
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
                intent_bucket="window_shopper"
            )
    
    def _make_cache_key(self, query: str, history: Optional[List[Dict]]) -> str:
        """Generate cache key from query + recent history context."""
        context = query.strip().lower()
        if history:
            for msg in history[-2:]:
                if isinstance(msg, dict):
                    context += "|" + msg.get("content", "")[:50]
        return hashlib.md5(context.encode()).hexdigest()
    
    def _cache_intent(self, key: str, intent: Intent):
        """Cache intent with LRU eviction."""
        if len(self._intent_cache) >= self._CACHE_MAX:
            oldest_key = next(iter(self._intent_cache))
            del self._intent_cache[oldest_key]
        self._intent_cache[key] = intent
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=3),
        reraise=True,
    )
    async def _extract_with_llm(
        self,
        query: str,
        history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Use GPT-4o-mini with Pydantic Structured Outputs for robust extraction."""
        
        system_prompt = """You are the Perception Layer of Osool, an Egyptian Real Estate AI.

Extract structured intent from the user's query.

Extract:
1. action: One of: search, valuation, objection, general, comparison, investment, legal, payment, reservation
2. intent_bucket: One of:
    - "window_shopper": Casual browsing, broad questions
    - "serious_buyer": Specific budget, timeline, ready to book
    - "objection_mode": Complaining, debating price, skeptical
3. filters: Object with optional fields:
   - location: Area name (New Cairo, Sheikh Zayed, New Capital, 6th October, North Coast, etc.)
   - budget_min: Minimum budget in EGP (convert millions: 5M = 5000000)
   - budget_max: Maximum budget in EGP
   - purpose: "living" OR "investment" OR "commercial"
   - bedrooms: Number of bedrooms (integer)
   - property_type: apartment, villa, townhouse, twinhouse, penthouse, duplex, studio
   - size_min: Minimum size in sqm
   - size_max: Maximum size in sqm
   - developer: Developer name if mentioned
   - keywords: Any specific compound/project names mentioned
   - finishing: core, semi, finished, lux

CONTEXT RULES FOR 'purpose':
- Family signals ("بيت العيلة", "استقرار", "مدارس", "kids", "اعيش"): purpose="living"
- Investment signals ("ROI", "استثمار", "عائد", "ايجار"): purpose="investment"
- "سكن عائلي" = purpose: "living" + intent_bucket: "serious_buyer"

INTENT BUCKET RULES:
- "serious_buyer": budget OR delivery timeline OR specific location = Serious
- "window_shopper": Generic questions like "show me everything"
- "objection_mode": Complaining, debating price

IMPORTANT: Convert Arabic numbers to integers. Convert "مليون" to actual number."""

        messages = []
        if history:
            for msg in history[-4:]:
                if isinstance(msg, dict):
                    messages.append(msg)
        messages.append({"role": "user", "content": query})
        
        # Use Pydantic Structured Outputs (schema-validated, zero parsing errors)
        from app.config import config
        model = getattr(config, 'GPT_MINI_MODEL', 'gpt-4o-mini')
        
        response = await self.openai_client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                *messages
            ],
            max_tokens=400,
            temperature=0.1,
            response_format=self.IntentExtraction,
        )
        
        parsed = response.choices[0].message.parsed
        
        if parsed is None:
            # Fallback: refusal or parse failure
            logger.warning("Structured output returned None — falling back to JSON mode")
            raise ValueError("Structured output parse failure")
        
        return {
            "action": parsed.action,
            "intent_bucket": parsed.intent_bucket,
            "filters": parsed.filters,
        }
    
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
        
        # Extract property type (check multi-word aliases first)
        sorted_aliases = sorted(PROPERTY_TYPE_ALIASES.keys(), key=len, reverse=True)
        for alias in sorted_aliases:
            if alias in query_lower:
                filters["property_type"] = PROPERTY_TYPE_ALIASES[alias]
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
        
        # --- PURPOSE DETECTION ---
        family_keywords = ["سكن عائلي", "عيلة", "عائلي", "family", "بيت عيلة"]
        if any(kw in query_lower for kw in family_keywords):
            filters["purpose"] = "living"
            
        investment_keywords = ["استثمار", "عائد", "roi", "investment", "return", "profit"]
        if any(kw in query_lower for kw in investment_keywords):
            filters["purpose"] = "investment"

        # --- EGYPTIAN FINISHING TERMS ---
        finishing_terms = {
            "تشطيب كامل": "finished",
            "سوبر لوكس": "finished",
            "تشطيب سوبر لوكس": "finished",
            "كامل التشطيب": "finished",
            "نص تشطيب": "semi-finished",
            "نصف تشطيب": "semi-finished",
            "على الطوب": "core",
            "طوب أحمر": "core",
            "بدون تشطيب": "core",
            "تسليم فوري": "ready",
            "استلام فوري": "ready",
        }
        for term, value in finishing_terms.items():
            if term in query_lower:
                filters["finishing"] = value
                break
            
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
            "cache_size": len(self._intent_cache),
            "success_rate": ((total - self.stats["failures"]) / max(total, 1)) * 100
        }


# Singleton instance
perception_layer = PerceptionLayer()

__all__ = ["PerceptionLayer", "perception_layer", "Intent"]
