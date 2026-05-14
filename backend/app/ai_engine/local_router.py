import asyncio
import inspect
import re
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, select
from app.models import Property
from app.ai_engine.local_intent import local_intent_extractor
from app.ai_engine.template_generator import template_generator
from app.ai_engine.analytical_engine import analytical_engine

class LocalRouter:
    """
    Coordinates the Zero-Token Free Path logic.
    """

    def process_query(self, query: str, session_count: int, db: Session, previous_queries: List[str] | None = None) -> Dict[str, Any]:
        """
        Processes a user query and returns a response dict.
        """
        # 1. Trigger 2: Depth Limit
        if session_count >= 5:
            return self._generate_upsell_response("DEPTH_LIMIT", query)

        # 2. Extract Intent
        intent_data = local_intent_extractor.extract_intent(query)
        intent_data = self._merge_previous_intent(intent_data, previous_queries or [])

        # 3. Trigger 1 & 3: Complex or Action Intent
        if intent_data["intent"] == "COMPLEX":
            return self._generate_upsell_response("COMPLEX", query)
        elif intent_data["intent"] == "ACTION":
            return self._generate_upsell_response("ACTION", query)

        # 4. Handle Normal Search
        if not intent_data["area"] or not intent_data["max_budget"]:
             # Needs clarification, handle gracefully without LLM
             area_missing = not bool(intent_data["area"])
             budget_missing = not bool(intent_data["max_budget"])
             return {
                 "type": "clarification",
                 "response_type": "free_local",
                 "text": self._get_clarification_text(
                     query=query,
                     area_missing=area_missing,
                     budget_missing=budget_missing,
                     area=intent_data.get("area"),
                     compound=intent_data.get("compound"),
                 ),
                 "properties": [],
                 "show_upsell": False,
                 "upsell_reason": None,
                 "cta_actions": []
             }

        # Query Database with tiered fallback
        properties, fallback_meta = asyncio.run(self._query_with_fallback(db, intent_data))

        effective_area = intent_data["area"]
        if fallback_meta and fallback_meta.get("tier") == "area_swap" and properties:
            effective_area = properties[0].get("location") or intent_data["area"]

        # Run Analytical Engine (inject scores and bargain info)
        enriched_properties = asyncio.run(self._enrich_with_analytics_async(properties, effective_area))

        # Generate Text Response
        response_text = template_generator.generate_response(
            enriched_properties,
            intent_data["area"],
            intent_data["max_budget"],
            language=self._detect_language(query, previous_queries or []),
            compound=intent_data.get("compound"),
            fallback_meta=fallback_meta,
        )

        return {
            "type": "success",
            "response_type": "free_local",
            "text": response_text,
            "properties": enriched_properties[:1], # Send top property for the UI card
            "show_upsell": False,
            "upsell_reason": None,
            "cta_actions": [],
            "fallback_tier": (fallback_meta or {}).get("tier"),
        }

    async def process_query_async(
        self,
        query: str,
        session_count: int,
        db,
        previous_queries: List[str] | None = None,
    ) -> Dict[str, Any]:
        """
        Async-compatible version for FastAPI AsyncSession routes.
        """
        # 1. Trigger 2: Depth Limit
        if session_count >= 5:
            return self._generate_upsell_response("DEPTH_LIMIT", query)

        # 2. Extract Intent
        intent_data = local_intent_extractor.extract_intent(query)
        intent_data = self._merge_previous_intent(intent_data, previous_queries or [])

        # 3. Trigger 1 & 3: Complex or Action Intent
        if intent_data["intent"] == "COMPLEX":
            return self._generate_upsell_response("COMPLEX", query)
        if intent_data["intent"] == "ACTION":
            return self._generate_upsell_response("ACTION", query)

        # 4. Handle Normal Search
        if not intent_data["area"] or not intent_data["max_budget"]:
            area_missing = not bool(intent_data["area"])
            budget_missing = not bool(intent_data["max_budget"])
            return {
                "type": "clarification",
                "response_type": "free_local",
                "text": self._get_clarification_text(
                    query=query,
                    area_missing=area_missing,
                    budget_missing=budget_missing,
                    area=intent_data.get("area"),
                    compound=intent_data.get("compound"),
                ),
                "properties": [],
                "show_upsell": False,
                "upsell_reason": None,
                "cta_actions": [],
            }

        properties, fallback_meta = await self._query_with_fallback(db, intent_data)

        # If a fallback swapped area (e.g., Sodic in Sheikh Zayed instead of New Cairo),
        # enrich against the actual property location for accurate price-per-sqm framing.
        effective_area = intent_data["area"]
        if fallback_meta and fallback_meta.get("tier") == "area_swap" and properties:
            effective_area = properties[0].get("location") or intent_data["area"]

        enriched_properties = await self._enrich_with_analytics_async(properties, effective_area)
        response_text = template_generator.generate_response(
            enriched_properties,
            intent_data["area"],
            intent_data["max_budget"],
            language=self._detect_language(query, previous_queries or []),
            compound=intent_data.get("compound"),
            fallback_meta=fallback_meta,
        )

        return {
            "type": "success",
            "response_type": "free_local",
            "text": response_text,
            "properties": enriched_properties[:1],
            "show_upsell": False,
            "upsell_reason": None,
            "cta_actions": [],
            "fallback_tier": (fallback_meta or {}).get("tier"),
        }

    def _query_database(self, db: Session, intent: Dict[str, Any]) -> List[Dict]:
        """
        Executes a fast SQL query based on extracted intent.
        """
        stmt = select(Property).where(Property.is_available == True)

        if intent["area"]:
            stmt = stmt.where(Property.location.ilike(f"%{intent['area']}%"))

        if intent.get("compound"):
            stmt = stmt.where(
                or_(
                    Property.compound.ilike(f"%{intent['compound']}%"),
                    Property.developer.ilike(f"%{intent['compound']}%"),
                )
            )

        if intent["max_budget"]:
             stmt = stmt.where(Property.price <= intent["max_budget"])

        if intent["property_type"]:
             stmt = stmt.where(Property.type.ilike(f"%{intent['property_type']}%"))

        if intent["rooms"]:
             stmt = stmt.where(Property.bedrooms >= intent["rooms"])

        # Order by price ascending to find the best deals under budget
        stmt = stmt.order_by(Property.price.asc()).limit(10)

        results = db.execute(stmt).scalars().all()

        # Convert to dict for easier manipulation
        return [self._prop_to_dict(p) for p in results]

    async def _query_database_async(self, db, intent: Dict[str, Any]) -> List[Dict]:
        """
        AsyncSession variant for fast stream route integration.
        """
        stmt = select(Property).where(Property.is_available == True)

        if intent["area"]:
            stmt = stmt.where(Property.location.ilike(f"%{intent['area']}%"))

        if intent.get("compound"):
            stmt = stmt.where(
                or_(
                    Property.compound.ilike(f"%{intent['compound']}%"),
                    Property.developer.ilike(f"%{intent['compound']}%"),
                )
            )

        if intent["max_budget"]:
            stmt = stmt.where(Property.price <= intent["max_budget"])

        if intent["property_type"]:
            stmt = stmt.where(Property.type.ilike(f"%{intent['property_type']}%"))

        if intent["rooms"]:
            stmt = stmt.where(Property.bedrooms >= intent["rooms"])

        stmt = stmt.order_by(Property.price.asc()).limit(10)
        results = (await db.execute(stmt)).scalars().all()
        return [self._prop_to_dict(p) for p in results]

    async def _query_with_fallback(
        self,
        db,
        intent: Dict[str, Any],
    ) -> Tuple[List[Dict], Optional[Dict[str, Any]]]:
        """
        Tiered fallback search: try the exact criteria first, then progressively
        relax to surface the best next-best option. Returns (properties, meta);
        meta is ``None`` for an exact match and otherwise describes which
        constraint was relaxed so the template generator can frame the pitch.
        """
        base_budget = intent.get("max_budget")
        base_compound = intent.get("compound")
        base_area = intent.get("area")

        # Tier 1: exact match
        props = await self._query_database_async(db, intent)
        if props:
            return props, None

        # Tier 2: same compound + area, stretch budget by +25%.
        # Surfaces "just over budget" deals which are usually worth pitching.
        if base_budget and base_compound and base_area:
            relaxed = dict(intent)
            relaxed["max_budget"] = int(base_budget * 1.25)
            props = await self._query_database_async(db, relaxed)
            if props:
                return props, {
                    "tier": "budget_stretch",
                    "original_budget": base_budget,
                    "stretched_budget": relaxed["max_budget"],
                    "compound": base_compound,
                    "area": base_area,
                }

        # Tier 3: same area + budget, drop compound.
        # "Sodic isn't in stock here, but here's the best alternative in your area."
        if base_compound and base_area and base_budget:
            relaxed = dict(intent)
            relaxed["compound"] = None
            props = await self._query_database_async(db, relaxed)
            if props:
                return props, {
                    "tier": "compound_swap",
                    "missing_compound": base_compound,
                    "area": base_area,
                    "budget": base_budget,
                }

        # Tier 4: same compound, swap area (within budget).
        # "Your developer of choice doesn't have units here — but they have great ones in X."
        if base_compound and base_budget:
            relaxed = dict(intent)
            relaxed["area"] = None
            props = await self._query_database_async(db, relaxed)
            if props:
                return props, {
                    "tier": "area_swap",
                    "missing_area": base_area,
                    "compound": base_compound,
                    "budget": base_budget,
                }

        # Tier 5: drop compound AND stretch budget +50% in the same area.
        if base_area and base_budget:
            relaxed = dict(intent)
            relaxed["compound"] = None
            relaxed["max_budget"] = int(base_budget * 1.5)
            props = await self._query_database_async(db, relaxed)
            if props:
                return props, {
                    "tier": "compound_swap_budget_stretch",
                    "missing_compound": base_compound,
                    "original_budget": base_budget,
                    "stretched_budget": relaxed["max_budget"],
                    "area": base_area,
                }

        # Tier 6: drop budget cap entirely, keep area; closest above-budget unit wins.
        if base_area:
            relaxed = dict(intent)
            relaxed["compound"] = None
            relaxed["max_budget"] = None
            relaxed["property_type"] = None
            relaxed["rooms"] = None
            props = await self._query_database_async(db, relaxed)
            if props:
                return props, {
                    "tier": "budget_uncapped",
                    "missing_compound": base_compound,
                    "original_budget": base_budget,
                    "area": base_area,
                }

        return [], None

    def _prop_to_dict(self, prop: Property) -> Dict:
        return {
            "id": prop.id,
            "title": prop.title,
            "location": prop.location,
            "compound": prop.compound,
            "developer": prop.developer,
            "price": prop.price,
            "price_per_sqm": prop.price_per_sqm,
            "size_sqm": prop.size_sqm,
            "bedrooms": prop.bedrooms,
            "sale_type": prop.sale_type,
            "installment_years": prop.installment_years,
            "down_payment": prop.down_payment,
            "image_url": prop.image_url,
            "osool_score": prop.osool_score,
            "bargain_percentage": prop.bargain_percentage
        }

    async def _resolve_area_avg_price(self, area: str) -> int:
        """
        Resolve the analytics helper whether it returns a value or a coroutine.
        """
        try:
            candidate = analytical_engine._get_area_avg_price(area)
            if inspect.isawaitable(candidate):
                return int(await candidate)
            return int(candidate)
        except Exception:
            return 50000

    async def _enrich_with_analytics_async(self, properties: List[Dict], area: str) -> List[Dict]:
         """
         Uses the local analytical engine to score properties.
         """
         if not properties:
             return []

         area_avg_price = await self._resolve_area_avg_price(area)

         for prop in properties:
             prop["area_avg_price"] = area_avg_price

             # Calculate bargain percentage
             price_sqm = prop.get("price_per_sqm") or (prop["price"] / prop["size_sqm"] if prop.get("size_sqm") else 0)
             if area_avg_price > 0 and price_sqm > 0:
                 prop["bargain_percentage"] = ((area_avg_price - price_sqm) / area_avg_price) * 100
             else:
                 prop["bargain_percentage"] = 0

             # Simple scoring logic (could use score_property() from analytical_engine if it exists)
             score = 50
             if prop["bargain_percentage"] > 10:
                 score += 20
             if prop.get("installment_years", 0) >= 7:
                 score += 15
             if prop.get("down_payment", 1000000) / prop["price"] <= 0.15:
                 score += 10

             prop["osool_score"] = min(100, score)

         # Sort by osool_score descending
         properties.sort(key=lambda x: x.get("osool_score", 0), reverse=True)
         return properties

    def _enrich_with_analytics(self, properties: List[Dict], area: str) -> List[Dict]:
         return asyncio.run(self._enrich_with_analytics_async(properties, area))


    def _contains_arabic(self, text: str) -> bool:
        return bool(text and re.search(r"[\u0600-\u06FF]", text))

    def _detect_language(self, query: str, previous_queries: List[str]) -> str:
        if self._contains_arabic(query) or any(self._contains_arabic(item) for item in previous_queries):
            return "ar"
        return "en"

    def _merge_previous_intent(self, intent_data: Dict[str, Any], previous_queries: List[str]) -> Dict[str, Any]:
        if intent_data.get("intent") != "SEARCH" or not previous_queries:
            return intent_data

        merged = dict(intent_data)
        for previous_query in previous_queries:
            previous_intent = local_intent_extractor.extract_intent(previous_query)
            if previous_intent.get("intent") != "SEARCH":
                continue

            for key in ("area", "compound", "property_type", "max_budget", "rooms"):
                if not merged.get(key) and previous_intent.get(key):
                    merged[key] = previous_intent[key]

            if merged.get("area") and merged.get("max_budget") and merged.get("compound"):
                break

        return merged

    def _get_clarification_text(
        self,
        query: str,
        area_missing: bool,
        budget_missing: bool,
        area: str | None = None,
        compound: str | None = None,
    ) -> str:
        is_arabic = self._contains_arabic(query)

        if is_arabic:
            area_label_map = {
                "new cairo": "القاهرة الجديدة",
                "sheikh zayed": "الشيخ زايد",
                "6th of october": "6 أكتوبر",
                "north coast": "الساحل الشمالي",
                "new capital": "العاصمة الإدارية",
            }
            area_label = area_label_map.get((area or "").lower(), area or "")
            target_label = f"{compound} في {area_label}" if compound and area_label else compound or area_label

            if area_missing and budget_missing:
                if compound:
                    return f"تمام، فهمت إنك مهتم بـ {compound}. قولي المنطقة المفضلة (مثال: القاهرة الجديدة) والميزانية القصوى علشان أطلع لك أفضل الفرص فورًا."
                return "علشان أجيب لك أفضل الفرص، قولي المنطقة اللي تفضلها (مثال: القاهرة الجديدة) والميزانية القصوى."
            if budget_missing and not area_missing:
                if target_label:
                    return f"تمام، فهمت إنك مهتم بـ {target_label}. قولي الميزانية القصوى وأنا أطلع لك أفضل الفرص فورًا."
                return "تمام، قولي الميزانية القصوى وأنا أطلع لك أفضل الفرص فورًا."
            if area_missing and not budget_missing:
                if compound:
                    return f"ممتاز. عندي اهتمامك بـ {compound} وميزانيتك. قولي المنطقة المفضلة (مثال: القاهرة الجديدة) علشان أحدد لك أفضل الخيارات."
                return "ممتاز. قولي المنطقة اللي تفضلها (مثال: القاهرة الجديدة) علشان أحدد لك أفضل الخيارات ضمن ميزانيتك."
            return "ممتاز، هل تحب شقة ولا فيلا؟"

        if area_missing and budget_missing:
            if compound:
                return f"Great, I understood you are interested in {compound}. Please share your preferred area (e.g., New Cairo) and maximum budget so I can fetch the best options right away."
            return "To find the best deals, please tell me your preferred area (e.g., New Cairo) and maximum budget."
        if budget_missing and not area_missing:
            area_label = (area or "selected area").title()
            target_label = f"{compound} in {area_label}" if compound else area_label
            return f"Great, I understood you are interested in {target_label}. Please share your maximum budget and I will fetch the best options right away."
        if area_missing and not budget_missing:
            if compound:
                return f"Great, I have your interest in {compound} and budget noted. Please share your preferred area (e.g., New Cairo) so I can fetch the best options."
            return "Great, please share your preferred area (e.g., New Cairo) so I can fetch the best options within your budget."
        return "Great, are you looking for an apartment or a villa?"

    def _generate_upsell_response(self, trigger_type: str, query: str = "") -> Dict[str, Any]:
        """
        Generates the graceful handoff message.
        """
        is_arabic = self._contains_arabic(query)
        text = ""
        upsell_reason = None
        if trigger_type == "COMPLEX":
            if is_arabic:
                text = "سؤال ممتاز جدًا. تحليل التحوط من التضخم وتأثير العوامل الجيوسياسية وتوقع العائد بدقة يحتاج محركنا المتقدم وأدوات تحليل سوق أعمق."
            else:
                text = "That is a brilliant question. Analyzing inflation hedging, geopolitical impacts, and precise predictive ROI requires our Dual-Engine AI and deep market forecasting tools."
            upsell_reason = "complex_forecasting"
        elif trigger_type == "DEPTH_LIMIT":
            if is_arabic:
                text = "أسئلتك ممتازة ومفصلة! لو تحب تحليل أعمق ومخصص بشكل كامل مع استخدام غير محدود..."
            else:
                text = "You've been asking some great, in-depth questions! To get more detailed, personalized insights and unlimited analysis..."
            upsell_reason = "depth_limit"
        elif trigger_type == "ACTION":
            if is_arabic:
                text = "اختيار ممتاز! لحجز معاينة أو الحصول على التفاصيل الرسمية، أفضل خطوة هي التواصل مع خبير أو استخدام الأدوات المتقدمة."
            else:
                text = "Excellent choice! To schedule a visit or get official details, connecting with a human expert or using our premium tools is the best next step."
            upsell_reason = "action_intent"

        if is_arabic:
            text += "\n\nللحصول على تحليل تنبؤي ومخصص، اختر أحد الخيارات التالية:"
        else:
            text += "\n\nTo get a personalized, predictive analysis, choose one of the options below:"

        consultant_label = "تواصل مع مستشار" if is_arabic else "Talk to Consultant"
        premium_label = "فتح الباقة المتقدمة" if is_arabic else "Unlock Premium"

        return {
            "type": "upsell",
            "response_type": "free_local",
            "text": text,
            "properties": [],
            "show_upsell": True,
            "upsell_reason": upsell_reason,
            "cta_actions": [
                {
                    "id": "talk_to_consultant",
                    "label": consultant_label,
                    "type": "consultant",
                },
                {
                    "id": "unlock_premium",
                    "label": premium_label,
                    "type": "upgrade",
                },
            ],
        }

local_router = LocalRouter()
