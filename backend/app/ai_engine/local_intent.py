import re
from typing import Dict, Any, Optional

# ── Arabic normalization ─────────────────────────────────────────────────────
# Egyptian colloquial frequently drops diacritics and uses ه for ة, ي for ى, and
# bare ا for أ/إ/آ. The intent extractor relies on substring matches against a
# dictionary of canonical keys, so without normalizing both sides the same way
# a perfectly valid user phrase like "القاهره الجديده" fails to match
# "القاهرة الجديدة". Apply the same transform to keys and queries.
_ARABIC_CHAR_MAP = str.maketrans({
    "أ": "ا",
    "إ": "ا",
    "آ": "ا",
    "ة": "ه",
    "ى": "ي",
    "ؤ": "و",
    "ئ": "ي",
})
_ARABIC_DIACRITICS_RE = re.compile(r"[ً-ْٰ]")


def _normalize_arabic(text: str) -> str:
    if not text:
        return text
    text = _ARABIC_DIACRITICS_RE.sub("", text)
    return text.translate(_ARABIC_CHAR_MAP)


def _normalize_keys(mapping: Dict[str, str]) -> Dict[str, str]:
    return {_normalize_arabic(k.lower()): v for k, v in mapping.items()}


def _normalize_list_values(items: Dict[str, list]) -> Dict[str, list]:
    return {k: [_normalize_arabic(v.lower()) for v in vs] for k, vs in items.items()}


def _normalize_keywords(items: list) -> list:
    return [_normalize_arabic(v.lower()) for v in items]


class LocalIntentExtractor:
    """
    Zero-Token Local Intent Extractor.
    Uses regex and keyword matching to extract structured data from user queries.
    """

    _AREA_MAPPING_RAW = {
        "new cairo": "new cairo",
        "القاهرة الجديدة": "new cairo",
        "tagamoa": "new cairo",
        "tagamo3": "new cairo",
        "tagamo3a": "new cairo",
        "التجمع": "new cairo",
        "تجمع": "new cairo",
        "التجمع الخامس": "new cairo",
        "fifth settlement": "new cairo",
        "5th settlement": "new cairo",
        "الخامس": "new cairo",
        "zayed": "sheikh zayed",
        "زايد": "sheikh zayed",
        "الشيخ زايد": "sheikh zayed",
        "sheikh zayed": "sheikh zayed",
        "october": "6th of october",
        "اكتوبر": "6th of october",
        "أكتوبر": "6th of october",
        "السادس من اكتوبر": "6th of october",
        "6th october": "6th of october",
        "north coast": "north coast",
        "الساحل الشمالي": "north coast",
        "الساحل": "north coast",
        "ساحل": "north coast",
        "new capital": "new capital",
        "العاصمة الإدارية": "new capital",
        "العاصمة": "new capital",
        "مدينتي": "madinaty",
        "madinaty": "madinaty",
        "الرحاب": "rehab",
        "rehab": "rehab",
        "المعادي": "maadi",
        "maadi": "maadi",
        "الشروق": "shorouk",
        "shorouk": "shorouk",
    }

    _PROPERTY_TYPES_RAW = {
        "apartment": ["apartment", "شقة", "شقه"],
        "villa": ["villa", "فيلا", "فيله"],
        "townhouse": ["townhouse", "تاون هاوس", "تاون"],
        "twinhouse": ["twinhouse", "توين هاوس", "توين"],
        "chalet": ["chalet", "شاليه"],
        "studio": ["studio", "استوديو", "ستوديو"],
        "duplex": ["duplex", "دوبلكس"],
        "penthouse": ["penthouse", "بنتهاوس"],
    }

    _COMPOUND_MAPPING_RAW = {
        "palm hills": "Palm Hills",
        "palm hill": "Palm Hills",
        "palmhills": "Palm Hills",
        "plan hills": "Palm Hills",
        "بالم هيلز": "Palm Hills",
        "بالم هيلس": "Palm Hills",
        "بالمهيلز": "Palm Hills",
        "سراي": "Sarai",
        "sarai": "Sarai",
        "mountain view": "Mountain View",
        "ماونتن فيو": "Mountain View",
        "hyde park": "Hyde Park",
        "هايد بارك": "Hyde Park",
        "zed east": "ZED East",
        "zed": "ZED",
        "زيد": "ZED",
        "taj city": "Taj City",
        "تاج سيتي": "Taj City",
        "sodic": "Sodic",
        "سوديك": "Sodic",
        "badya": "Badya",
        "بادية": "Badya",
        "waterway": "Waterway",
        "واتر واي": "Waterway",
        # Hassan Allam — common Egyptian developer/compound. Multiple Arabic spellings.
        "hassan allam": "Hassan Allam",
        "حسن علام": "Hassan Allam",
        "علام": "Hassan Allam",
        # Emaar / Marassi / Uptown Cairo
        "emaar": "Emaar",
        "إعمار": "Emaar",
        "اعمار": "Emaar",
        "marassi": "Marassi",
        "مراسي": "Marassi",
        "uptown cairo": "Uptown Cairo",
        "أب تاون": "Uptown Cairo",
        # Mountain View variants
        "icity": "Mountain View iCity",
        "آي سيتي": "Mountain View iCity",
        # Tatweer Misr / Bloomfields / Fouka Bay
        "tatweer misr": "Tatweer Misr",
        "تطوير مصر": "Tatweer Misr",
        "bloomfields": "Bloomfields",
        "بلوم فيلدز": "Bloomfields",
        "fouka bay": "Fouka Bay",
        "فوكا باي": "Fouka Bay",
        # Madinet Masr / Sarai / Taj City already above
        "madinet masr": "Madinet Masr",
        "مدينة مصر": "Madinet Masr",
        # ORA / Zed
        "ora": "ORA",
        "أورا": "ORA",
        # La Vista
        "la vista": "La Vista",
        "lavista": "La Vista",
        "لافيستا": "La Vista",
        "لافستا": "La Vista",
        "لا فيستا": "La Vista",
        # Cairo Festival City
        "cairo festival": "Cairo Festival City",
        "فستيفال": "Cairo Festival City",
        # New Giza
        "new giza": "New Giza",
        "نيو جيزة": "New Giza",
    }

    # Entity kind tags for the free-path comparison funnel. Each alias is tagged
    # as either "developer" (resolves to a flagship compound via flagship_compounds.py)
    # or "compound" (used as-is). The keys mirror _COMPOUND_MAPPING_RAW but the
    # canonical values may differ when a brand name is ambiguous.
    _ENTITY_KIND_RAW: dict[str, tuple[str, str]] = {
        # Developers — auto-resolve to a flagship compound at dialog time.
        "hassan allam": ("Hassan Allam", "developer"),
        "حسن علام": ("Hassan Allam", "developer"),
        "علام": ("Hassan Allam", "developer"),
        "sodic": ("Sodic", "developer"),
        "سوديك": ("Sodic", "developer"),
        "la vista": ("La Vista", "developer"),
        "lavista": ("La Vista", "developer"),
        "لافيستا": ("La Vista", "developer"),
        "لافستا": ("La Vista", "developer"),
        "لا فيستا": ("La Vista", "developer"),
        "emaar": ("Emaar", "developer"),
        "إعمار": ("Emaar", "developer"),
        "اعمار": ("Emaar", "developer"),
        "ora": ("ORA", "developer"),
        "أورا": ("ORA", "developer"),
        "tatweer misr": ("Tatweer Misr", "developer"),
        "تطوير مصر": ("Tatweer Misr", "developer"),
        "palm hills": ("Palm Hills", "developer"),
        "palm hill": ("Palm Hills", "developer"),
        "palmhills": ("Palm Hills", "developer"),
        "بالم هيلز": ("Palm Hills", "developer"),
        "بالم هيلس": ("Palm Hills", "developer"),
        "بالمهيلز": ("Palm Hills", "developer"),
        "mountain view": ("Mountain View", "developer"),
        "ماونتن فيو": ("Mountain View", "developer"),
        "madinet masr": ("Madinet Masr", "developer"),
        "مدينة مصر": ("Madinet Masr", "developer"),

        # Compounds — used directly.
        "sarai": ("Sarai", "compound"),
        "سراي": ("Sarai", "compound"),
        "hyde park": ("Hyde Park", "compound"),
        "هايد بارك": ("Hyde Park", "compound"),
        "zed east": ("ZED East", "compound"),
        "zed": ("ZED East", "compound"),
        "زيد": ("ZED East", "compound"),
        "taj city": ("Taj City", "compound"),
        "تاج سيتي": ("Taj City", "compound"),
        "badya": ("Badya", "compound"),
        "بادية": ("Badya", "compound"),
        "waterway": ("Waterway", "compound"),
        "واتر واي": ("Waterway", "compound"),
        "marassi": ("Marassi", "compound"),
        "مراسي": ("Marassi", "compound"),
        "uptown cairo": ("Uptown Cairo", "compound"),
        "أب تاون": ("Uptown Cairo", "compound"),
        "icity": ("Mountain View iCity", "compound"),
        "آي سيتي": ("Mountain View iCity", "compound"),
        "bloomfields": ("Bloomfields", "compound"),
        "بلوم فيلدز": ("Bloomfields", "compound"),
        "fouka bay": ("Fouka Bay", "compound"),
        "فوكا باي": ("Fouka Bay", "compound"),
        "cairo festival": ("Cairo Festival City", "compound"),
        "فستيفال": ("Cairo Festival City", "compound"),
        "new giza": ("New Giza", "compound"),
        "نيو جيزة": ("New Giza", "compound"),
        # Sodic-developer flagship compounds — also accept their literal names.
        "sodic east": ("Sodic East", "compound"),
        "سوديك ايست": ("Sodic East", "compound"),
        # La Vista-developer flagship compounds.
        "la vista city": ("La Vista City", "compound"),
        "لافيستا سيتي": ("La Vista City", "compound"),
        # Hassan Allam flagship compounds.
        "swan lake": ("Swan Lake", "compound"),
        "سوان ليك": ("Swan Lake", "compound"),
        "hap town": ("Hap Town", "compound"),
        "هاب تاون": ("Hap Town", "compound"),
        # Tatweer Misr / Mountain View flagship compounds beyond the brand.
        "mivida": ("Mivida", "compound"),
        "ميفيدا": ("Mivida", "compound"),
        # Palm Hills compounds.
        "palm hills new cairo": ("Palm Hills New Cairo", "compound"),
        "palm hills katameya": ("Palm Hills Katameya", "compound"),
    }

    # Comparison-intent triggers — strictly intent-related verbs/phrases.
    # NB: kept disjoint from COMPLEX_KEYWORDS so that "احسن سعر بين X و Y" enters
    # the comparison flow rather than the COMPLEX upsell branch.
    _COMPARISON_INTENT_KEYWORDS_RAW = [
        "compare", "vs", "versus", "best price", "cheapest", "good deal",
        "بين", "احسن سعر", "أحسن سعر", "ايه احسن", "إيه أحسن", "مقارنة بين",
        "أرخص", "ارخص", "افضل سعر", "أفضل سعر", "صفقه", "صفقة",
    ]

    _COMPLEX_KEYWORDS_RAW = [
        "roi", "inflation", "hedge", "geopolitical", "predict", "forecast", "compare", "risk", "macro",
        "تضخم", "عائد", "مقارنة", "توقعات", "سياسي", "اقتصادي", "استثمار"
    ]

    _ACTION_KEYWORDS_RAW = [
        "visit", "brochure", "call", "schedule", "meeting", "contact", "book", "consultant",
        "زيارة", "بروشور", "اتصال", "موعد", "تواصل"
    ]

    AREA_MAPPING = _normalize_keys(_AREA_MAPPING_RAW)
    PROPERTY_TYPES = _normalize_list_values(_PROPERTY_TYPES_RAW)
    COMPOUND_MAPPING = _normalize_keys(_COMPOUND_MAPPING_RAW)
    COMPLEX_KEYWORDS = _normalize_keywords(_COMPLEX_KEYWORDS_RAW)
    ACTION_KEYWORDS = _normalize_keywords(_ACTION_KEYWORDS_RAW)
    # Normalized form of _ENTITY_KIND_RAW: key = normalized alias, value = (canonical, kind).
    ENTITY_KIND_MAPPING: dict[str, tuple[str, str]] = {
        _normalize_arabic(k.lower()): v for k, v in _ENTITY_KIND_RAW.items()
    }
    COMPARISON_INTENT_KEYWORDS = _normalize_keywords(_COMPARISON_INTENT_KEYWORDS_RAW)

    ARABIC_DIGITS_MAP = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

    def _normalize_query(self, query: str) -> str:
        """
        Normalize query text for deterministic regex parsing.
        """
        normalized = query.translate(self.ARABIC_DIGITS_MAP).lower()
        normalized = normalized.replace("٫", ".").replace("،", ",")
        normalized = normalized.replace("ـ", "")
        normalized = normalized.replace("mn", "million")
        normalized = _normalize_arabic(normalized)
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
            "compound": None,
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

        # 4. Extract Compound / Developer Brand
        for key, value in self.COMPOUND_MAPPING.items():
            if key in query_lower:
                intent_data["compound"] = value
                break

        # 5. Extract Property Type
        for prop_type, keywords in self.PROPERTY_TYPES.items():
            if any(kw in query_lower for kw in keywords):
                intent_data["property_type"] = prop_type
                break

        # 6. Extract Budget (Regex + ranges)
        intent_data["max_budget"] = self._extract_budget(query_lower)

        # 7. Extract Rooms
        # Matches: "3 rooms", "3 غرف", "3 bedroom", "3-bedroom". Note ة has been
        # normalized to ه upstream, so غرفه is the canonical form here.
        rooms_match = re.search(r'(\d+)\s*(?:rooms?|bedrooms?|غرف|غرفه)', query_lower)
        if rooms_match:
            intent_data["rooms"] = int(rooms_match.group(1))

        return intent_data

    def extract_entities(self, query: str) -> list[tuple[str, str]]:
        """
        Scan the query for compound/developer aliases and return a list of
        (canonical_name, kind) tuples ordered by where they first appear in
        the source query. Duplicates (same canonical name from multiple
        aliases) are dropped, keeping the earliest occurrence.

        Internally, longer aliases are tried first to avoid e.g. "Sodic"
        consuming the prefix of "Sodic East", but the final return order
        matches the user's typing order so callers can show suggestions in
        the user's own sequence.
        """
        normalized = self._normalize_query(query)
        sorted_aliases = sorted(self.ENTITY_KIND_MAPPING.keys(), key=len, reverse=True)

        # Collect (start_pos, canonical, kind) for each non-overlapping match.
        matches: list[tuple[int, str, str]] = []
        consumed: list[tuple[int, int]] = []

        def _overlaps(start: int, end: int) -> bool:
            return any(not (end <= s or start >= e) for s, e in consumed)

        for alias in sorted_aliases:
            if not alias:
                continue
            search_from = 0
            while True:
                idx = normalized.find(alias, search_from)
                if idx == -1:
                    break
                end = idx + len(alias)
                if not _overlaps(idx, end):
                    canonical, kind = self.ENTITY_KIND_MAPPING[alias]
                    matches.append((idx, canonical, kind))
                    consumed.append((idx, end))
                search_from = end

        # Sort by source position so output mirrors user's typing order.
        matches.sort(key=lambda m: m[0])

        # Dedupe by canonical name, keeping earliest position.
        found: list[tuple[str, str]] = []
        seen: set[str] = set()
        for _, canonical, kind in matches:
            if canonical not in seen:
                seen.add(canonical)
                found.append((canonical, kind))

        return found

    def is_comparison_intent(self, query: str) -> bool:
        """
        Return True if the query reads like a price-comparison request — the
        free path's only first-class intent. The check is permissive on
        purpose: any mention of "between", "best price", "compare", or naming
        two entities counts.
        """
        normalized = self._normalize_query(query)
        if any(keyword in normalized for keyword in self.COMPARISON_INTENT_KEYWORDS):
            return True
        # Also true if user listed ≥2 known entities, even without a comparison
        # verb (e.g. "لافيستا و سوديك").
        return len(self.extract_entities(query)) >= 2

local_intent_extractor = LocalIntentExtractor()
