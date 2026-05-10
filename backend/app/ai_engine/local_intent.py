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
        "tagamo3": "new cairo",
        "tagamo3a": "new cairo",
        "التجمع": "new cairo",
        "التجمع الخامس": "new cairo",
        "fifth settlement": "new cairo",
        "5th settlement": "new cairo",
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
        "roi", "inflation", "hedge", "geopolitical", "predict", "forecast", "compare", "risk", "macro",
        "تضخم", "عائد", "مقارنة", "توقعات", "سياسي", "اقتصادي", "استثمار"
    ]

    ACTION_KEYWORDS = [
        "visit", "brochure", "call", "schedule", "meeting", "contact", "book", "consultant",
        "زيارة", "بروشور", "اتصال", "موعد", "تواصل"
    ]

    ARABIC_DIGITS_MAP = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

    def _normalize_query(self, query: str) -> str:
        """
        Normalize query text for deterministic regex parsing.
        """
        normalized = query.translate(self.ARABIC_DIGITS_MAP).lower()
        normalized = normalized.replace("٫", ".").replace("،", ",")
        normalized = normalized.replace("mn", "million")
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def _extract_budget(self, text: str) -> Optional[int]:
        """
        Extract max budget from text, supporting ranges and multilingual markers.
        """
        # Example: 5-8 million / 5 to 8 million / من 5 الى 8 مليون
        range_million = re.search(
            r'(\d+(?:\.\d+)?)\s*(?:-|to|الى|إلى|لحد|حتى)\s*(\d+(?:\.\d+)?)\s*(?:million|m|مليون)',
            text,
        )
        if range_million:
            upper = float(range_million.group(2))
            return int(upper * 1_000_000)

        # Example: 5000000 - 8000000
        range_plain = re.search(r'(\d{6,})\s*(?:-|to|الى|إلى|لحد|حتى)\s*(\d{6,})', text)
        if range_plain:
            return int(range_plain.group(2))

        # Example: 8 million / 8m / 8 مليون
        budget_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:million|m|مليون)', text)
        if budget_match:
            amount = float(budget_match.group(1))
            return int(amount * 1_000_000)

        # Example: 8000000
        raw_budget_match = re.search(r'(?<!\d)(\d{6,})(?!\d)', text)
        if raw_budget_match:
            return int(raw_budget_match.group(1))

        return None

    def extract_intent(self, query: str) -> Dict[str, Any]:
        """
        Parses the query and returns structured intent.
        """
        query_lower = self._normalize_query(query)
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

        # 5. Extract Budget (Regex + ranges)
        intent_data["max_budget"] = self._extract_budget(query_lower)

        # 6. Extract Rooms
        # Matches: "3 rooms", "3 غرف", "3 bedroom", "3-bedroom"
        rooms_match = re.search(r'(\d+)\s*(?:rooms?|bedrooms?|غرف|غرفة)', query_lower)
        if rooms_match:
            intent_data["rooms"] = int(rooms_match.group(1))

        return intent_data

local_intent_extractor = LocalIntentExtractor()
