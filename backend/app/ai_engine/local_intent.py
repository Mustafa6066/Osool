import re
from typing import Dict, Any, Optional

class LocalIntentExtractor:
    """
    Zero-Token Local Intent Extractor.
    Uses regex and keyword matching to extract structured data from user queries.
    """

    AREA_MAPPING = {
        "new cairo": "new cairo",
        "القاهرة الجديدة": "new cairo",
        "tagamoa": "new cairo",
        "التجمع": "new cairo",
        "fifth settlement": "new cairo",
        "الخامس": "new cairo",
        "zayed": "sheikh zayed",
        "زايد": "sheikh zayed",
        "sheikh zayed": "sheikh zayed",
        "october": "6th of october",
        "اكتوبر": "6th of october",
        "6th october": "6th of october"
    }

    PROPERTY_TYPES = {
        "apartment": ["apartment", "شقة", "شقه"],
        "villa": ["villa", "فيلا", "فيله"],
        "townhouse": ["townhouse", "تاون هاوس", "تاون"],
        "twinhouse": ["twinhouse", "توين هاوس", "توين"],
        "chalet": ["chalet", "شاليه"],
        "studio": ["studio", "استوديو", "ستوديو"]
    }

    COMPLEX_KEYWORDS = [
        "roi", "inflation", "hedge", "geopolitical", "predict", "forecast", "compare",
        "تضخم", "عائد", "مقارنة", "توقعات", "سياسي", "اقتصادي", "استثمار"
    ]

    ACTION_KEYWORDS = [
        "visit", "brochure", "call", "schedule", "meeting", "contact",
        "زيارة", "بروشور", "اتصال", "موعد", "تواصل"
    ]

    def extract_intent(self, query: str) -> Dict[str, Any]:
        """
        Parses the query and returns structured intent.
        """
        query_lower = query.lower()
        intent_data = {
            "intent": "SEARCH",
            "area": None,
            "property_type": None,
            "max_budget": None,
            "rooms": None
        }

        # 1. Check for Complex / Deep Questions (Trigger 1)
        if any(keyword in query_lower for keyword in self.COMPLEX_KEYWORDS):
            intent_data["intent"] = "COMPLEX"
            return intent_data

        # 2. Check for Action Intent (Trigger 3)
        if any(keyword in query_lower for keyword in self.ACTION_KEYWORDS):
            intent_data["intent"] = "ACTION"
            return intent_data

        # 3. Extract Area
        for key, value in self.AREA_MAPPING.items():
            if key in query_lower:
                intent_data["area"] = value
                break

        # 4. Extract Property Type
        for prop_type, keywords in self.PROPERTY_TYPES.items():
            if any(kw in query_lower for kw in keywords):
                intent_data["property_type"] = prop_type
                break

        # 5. Extract Budget (Regex)
        # Matches: "8 million", "8 m", "8 مليون", "8000000"
        budget_match = re.search(r'(\d+(?:\.\d+)?)\s*(million|m|مليون)', query_lower)
        if budget_match:
            amount = float(budget_match.group(1))
            intent_data["max_budget"] = int(amount * 1_000_000)
        else:
            # Try to find a plain large number
            raw_budget_match = re.search(r'(?<!\d)(\d{6,})(?!\d)', query_lower)
            if raw_budget_match:
                intent_data["max_budget"] = int(raw_budget_match.group(1))

        # 6. Extract Rooms
        # Matches: "3 rooms", "3 غرف", "3 bedroom", "3-bedroom"
        rooms_match = re.search(r'(\d+)\s*(?:rooms?|bedrooms?|غرف|غرفة)', query_lower)
        if rooms_match:
            intent_data["rooms"] = int(rooms_match.group(1))

        return intent_data

local_intent_extractor = LocalIntentExtractor()
