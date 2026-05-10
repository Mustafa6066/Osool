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
            return self._generate_upsell_response("DEPTH_LIMIT")

        # 2. Extract Intent
        intent_data = local_intent_extractor.extract_intent(query)

        # 3. Trigger 1 & 3: Complex or Action Intent
        if intent_data["intent"] == "COMPLEX":
            return self._generate_upsell_response("COMPLEX")
        elif intent_data["intent"] == "ACTION":
            return self._generate_upsell_response("ACTION")

        # 4. Handle Normal Search
        if not intent_data["area"] or not intent_data["max_budget"]:
             # Needs clarification, handle gracefully without LLM
             return {
                 "type": "clarification",
                 "text": "To find the best deals, please tell me your preferred area (e.g., New Cairo) and maximum budget.",
                 "properties": [],
                 "show_upsell": False
             }

        # Query Database
        properties = self._query_database(db, intent_data)

        # Run Analytical Engine (inject scores and bargain info)
        enriched_properties = self._enrich_with_analytics(properties, intent_data["area"])

        # Generate Text Response
        response_text = template_generator.generate_response(
            enriched_properties,
            intent_data["area"],
            intent_data["max_budget"]
        )

        return {
            "type": "success",
            "text": response_text,
            "properties": enriched_properties[:1], # Send top property for the UI card
            "show_upsell": False
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

    def _enrich_with_analytics(self, properties: List[Dict], area: str) -> List[Dict]:
         """
         Uses the local analytical engine to score properties.
         """
         if not properties:
             return []

         try:
             area_avg_price = analytical_engine._get_area_avg_price(area)
         except Exception:
             area_avg_price = 50000 # Fallback

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


    def _generate_upsell_response(self, trigger_type: str) -> Dict[str, Any]:
        """
        Generates the graceful handoff message.
        """
        text = ""
        if trigger_type == "COMPLEX":
            text = "That is a brilliant question. Analyzing inflation hedging, geopolitical impacts, and precise predictive ROI requires our Dual-Engine AI and deep market forecasting tools."
        elif trigger_type == "DEPTH_LIMIT":
            text = "You've been asking some great, in-depth questions! To get more detailed, personalized insights and unlimited analysis..."
        elif trigger_type == "ACTION":
            text = "Excellent choice! To schedule a visit or get official details, connecting with a human expert or using our premium tools is the best next step."

        text += "\n\nTo get a personalized, predictive analysis, choose one of the options below:"

        return {
            "type": "upsell",
            "text": text,
            "properties": [],
            "show_upsell": True
        }

local_router = LocalRouter()
