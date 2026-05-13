import asyncio
import inspect
import re
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models import Property
from app.ai_engine.local_intent import local_intent_extractor
from app.ai_engine.template_generator import template_generator
from app.ai_engine.analytical_engine import analytical_engine

class LocalRouter:
    """
    Coordinates the Zero-Token Free Path logic.
    """

    def process_query(self, query: str, session_count: int, db: Session) -> Dict[str, Any]:
        """
        Processes a user query and returns a response dict.
        """
        # 1. Trigger 2: Depth Limit
        if session_count >= 5:
            return self._generate_upsell_response("DEPTH_LIMIT", query)

        # 2. Extract Intent
        intent_data = local_intent_extractor.extract_intent(query)

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
                 ),
                 "properties": [],
                 "show_upsell": False,
                 "upsell_reason": None,
                 "cta_actions": []
             }

        # Query Database
        properties = self._query_database(db, intent_data)

        # Run Analytical Engine (inject scores and bargain info)
        enriched_properties = asyncio.run(self._enrich_with_analytics_async(properties, intent_data["area"]))

        # Generate Text Response
        response_text = template_generator.generate_response(
            enriched_properties,
            intent_data["area"],
            intent_data["max_budget"]
        )

        return {
            "type": "success",
            "response_type": "free_local",
            "text": response_text,
            "properties": enriched_properties[:1], # Send top property for the UI card
            "show_upsell": False,
            "upsell_reason": None,
            "cta_actions": []
        }

    async def process_query_async(self, query: str, session_count: int, db) -> Dict[str, Any]:
        """
        Async-compatible version for FastAPI AsyncSession routes.
        """
        # 1. Trigger 2: Depth Limit
        if session_count >= 5:
            return self._generate_upsell_response("DEPTH_LIMIT", query)

        # 2. Extract Intent
        intent_data = local_intent_extractor.extract_intent(query)

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
                ),
                "properties": [],
                "show_upsell": False,
                "upsell_reason": None,
                "cta_actions": [],
            }

        properties = await self._query_database_async(db, intent_data)
        enriched_properties = await self._enrich_with_analytics_async(properties, intent_data["area"])
        response_text = template_generator.generate_response(
            enriched_properties,
            intent_data["area"],
            intent_data["max_budget"],
        )

        return {
            "type": "success",
            "response_type": "free_local",
            "text": response_text,
            "properties": enriched_properties[:1],
            "show_upsell": False,
            "upsell_reason": None,
            "cta_actions": [],
        }

    def _query_database(self, db: Session, intent: Dict[str, Any]) -> List[Dict]:
        """
        Executes a fast SQL query based on extracted intent.
        """
        stmt = select(Property).where(Property.is_available == True)

        if intent["area"]:
            stmt = stmt.where(Property.location.ilike(f"%{intent['area']}%"))

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

        if intent["max_budget"]:
            stmt = stmt.where(Property.price <= intent["max_budget"])

        if intent["property_type"]:
            stmt = stmt.where(Property.type.ilike(f"%{intent['property_type']}%"))

        if intent["rooms"]:
            stmt = stmt.where(Property.bedrooms >= intent["rooms"])

        stmt = stmt.order_by(Property.price.asc()).limit(10)
        results = (await db.execute(stmt)).scalars().all()
        return [self._prop_to_dict(p) for p in results]

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

    def _get_clarification_text(
        self,
        query: str,
        area_missing: bool,
        budget_missing: bool,
        area: str | None = None,
    ) -> str:
        is_arabic = self._contains_arabic(query)

        if is_arabic:
            area_label_map = {
                "new cairo": "القاهرة الجديدة",
                "sheikh zayed": "الشيخ زايد",
                "6th of october": "6 أكتوبر",
            }
            area_label = area_label_map.get((area or "").lower(), area or "")

            if area_missing and budget_missing:
                return "علشان أجيب لك أفضل الفرص، قولي المنطقة اللي تفضلها (مثال: القاهرة الجديدة) والميزانية القصوى."
            if budget_missing and not area_missing:
                if area_label:
                    return f"تمام، فهمت إنك مهتم بـ {area_label}. قولي الميزانية القصوى وأنا أطلع لك أفضل الفرص فورًا."
                return "تمام، قولي الميزانية القصوى وأنا أطلع لك أفضل الفرص فورًا."
            if area_missing and not budget_missing:
                return "ممتاز. قولي المنطقة اللي تفضلها (مثال: القاهرة الجديدة) علشان أحدد لك أفضل الخيارات ضمن ميزانيتك."
            return "ممتاز، هل تحب شقة ولا فيلا؟"

        if area_missing and budget_missing:
            return "To find the best deals, please tell me your preferred area (e.g., New Cairo) and maximum budget."
        if budget_missing and not area_missing:
            area_label = (area or "selected area").title()
            return f"Great, I understood your preferred area is {area_label}. Please share your maximum budget and I will fetch the best options right away."
        if area_missing and not budget_missing:
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
