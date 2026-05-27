"""
Zero-Token Intent Extraction
----------------------------
Parses a buyer prompt into a StructuredQuery with NO LLM and NO API calls.

Pipeline: a sequence of pure-function extractors, each ~20-50 lines, that
walk the prompt against:
- numeric/unit regex (price, beds, size, %, year)
- Egyptian zone dictionary (reuses LOCATION_ZONE_MAP from deterministic_normalizer)
- property-type dictionary (reuses _TYPE_MAP)
- finishing-level dictionary (reuses _FINISHING_MAP)
- compound + developer dictionaries (loaded lazily from DB, cached in Redis)

The output StructuredQuery is the deterministic contract that
property_retrieval.py consumes. Every field is optional; an empty
StructuredQuery is a valid result (caller decides what to do with it).

Latency target: p99 < 10ms. Never raises on bad input.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Optional

from app.ingestion.deterministic_normalizer import (
    LOCATION_ZONE_MAP,
    _FINISHING_MAP,
    _TYPE_MAP,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Output contract
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class StructuredQuery:
    """
    The deterministic shape that L1 emits and L2/L3/L4 consume.
    Every field optional. Empty instance == "no signal extracted".
    """
    # Hard filters → SQL WHERE
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    bedrooms_min: Optional[int] = None
    bedrooms_max: Optional[int] = None
    size_sqm_min: Optional[int] = None
    size_sqm_max: Optional[int] = None
    locations: list[str] = field(default_factory=list)
    compounds: list[str] = field(default_factory=list)
    developers: list[str] = field(default_factory=list)
    property_types: list[str] = field(default_factory=list)
    finishing_levels: list[str] = field(default_factory=list)
    ready_by_year_max: Optional[int] = None
    is_delivered: Optional[bool] = None
    is_nawy_now: Optional[bool] = None
    is_cash_only: Optional[bool] = None
    installment_years_min: Optional[int] = None
    down_payment_pct_max: Optional[int] = None
    sale_types: list[str] = field(default_factory=list)

    # Soft signals → L2b BM25 only (NOT embedded — that would cost tokens)
    semantic_text: str = ""

    # Boost-rule fuel
    intent_tags: list[str] = field(default_factory=list)

    # Buyer context (caller-set; we don't infer)
    buyer_budget_cap: Optional[int] = None
    buyer_persona: Optional[str] = None

    def is_empty(self) -> bool:
        """True when nothing was extracted. Caller decides what to do."""
        return (
            self.price_min is None and self.price_max is None
            and self.bedrooms_min is None and self.bedrooms_max is None
            and self.size_sqm_min is None and self.size_sqm_max is None
            and not self.locations and not self.compounds and not self.developers
            and not self.property_types and not self.finishing_levels
            and self.ready_by_year_max is None
            and self.is_delivered is None and self.is_nawy_now is None
            and self.is_cash_only is None and self.installment_years_min is None
            and self.down_payment_pct_max is None and not self.sale_types
            and not self.semantic_text and not self.intent_tags
        )


# ─────────────────────────────────────────────────────────────────────────────
# Normalisation helpers
# ─────────────────────────────────────────────────────────────────────────────

_ARABIC_DIGITS_MAP = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_ARABIC_RE = re.compile(r"[؀-ۿ]")


def _has_arabic(text: str) -> bool:
    return bool(_ARABIC_RE.search(text))


def _normalize(prompt: str) -> str:
    """Lowercase, strip, translate Arabic digits to Latin. Keep Arabic letters."""
    if not prompt:
        return ""
    return prompt.translate(_ARABIC_DIGITS_MAP).lower().strip()


# ─────────────────────────────────────────────────────────────────────────────
# Extractor 1 — numbers (price, beds, size, %, year)
# ─────────────────────────────────────────────────────────────────────────────

# Price: handles 8M, 8 million, 8,000,000, 8 مليون, 8000000 EGP, etc.
# Anchored to "price/budget/under/up to/مليون/جنيه/EGP" cues to avoid catching
# random numbers like bedroom counts.
_PRICE_NUMBER_RE = re.compile(
    r"(?P<num>\d{1,3}(?:[,\.]\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)"
    r"\s*(?P<scale>m\b|million|mil|k\b|thousand|مليون|الف|ألف|ك|م)?"
)

_PRICE_CUE_WORDS = re.compile(
    r"(price|budget|under|below|max(?:imum)?|up\s+to|less\s+than|no\s+more\s+than|"
    r"around|about|approx|ميزانية|سعر|اقل\s+من|أقل\s+من|في\s+حدود|حوالي|تحت|"
    r"egp|جنيه|ج\.م|ج\s*\.\s*م)",
    re.IGNORECASE,
)

_PRICE_MIN_CUE = re.compile(r"(at\s+least|min(?:imum)?|over|more\s+than|اكثر\s+من|أكثر\s+من|على\s+الاقل|على\s+الأقل)", re.IGNORECASE)

_BED_RE = re.compile(
    r"(?:(?P<n>\d+)\s*(?:br|bd|bdrm|bed(?:room)?s?|غرف|غرفة|غرفه))"
    r"|(?:(?P<word>studio|استوديو|ستوديو))",
    re.IGNORECASE,
)

_SIZE_RE = re.compile(
    r"(?P<n>\d{2,5})\s*(?:sqm|sq\.?m|m²|m\^2|m2|متر|م2|م²)",
    re.IGNORECASE,
)

_PERCENT_RE = re.compile(
    r"(?P<n>\d{1,2})\s*%\s*(?P<ctx>down|deposit|installment(?:s)?|مقدم|قسط)?",
    re.IGNORECASE,
)

_YEAR_RE = re.compile(r"\b(?P<year>20\d{2})\b")

_QUARTER_RE = re.compile(r"\bq(?P<q>[1-4])\s*(?P<year>20\d{2})\b", re.IGNORECASE)

_INSTALLMENT_YEARS_RE = re.compile(
    r"(?P<n>\d{1,2})[\s-]*(?:year|years|yr|yrs|سنة|سنوات|سنه|سنين)",
    re.IGNORECASE,
)


def _parse_price_with_scale(num_str: str, scale: Optional[str]) -> int:
    try:
        num = float(num_str.replace(",", ""))
    except ValueError:
        return 0
    if not scale:
        return int(num)
    scale = scale.lower()
    if scale in {"m", "million", "mil", "مليون", "م"}:
        return int(num * 1_000_000)
    if scale in {"k", "thousand", "الف", "ألف", "ك"}:
        return int(num * 1_000)
    return int(num)


def extract_numbers(prompt: str, q: StructuredQuery) -> StructuredQuery:
    text = _normalize(prompt)

    # Bedrooms (and studio → 1)
    for m in _BED_RE.finditer(text):
        if m.group("word"):
            q.bedrooms_min = q.bedrooms_min or 0
            q.bedrooms_max = 0  # studio = 0 bedrooms in DB convention
            continue
        n = int(m.group("n"))
        if 0 < n < 20:
            if q.bedrooms_min is None or n < q.bedrooms_min:
                q.bedrooms_min = n
            if q.bedrooms_max is None or n > q.bedrooms_max:
                q.bedrooms_max = n
    if q.bedrooms_min is not None and q.bedrooms_max is not None and q.bedrooms_min == q.bedrooms_max:
        # exact bedroom hint — keep both equal
        pass

    # Size
    for m in _SIZE_RE.finditer(text):
        n = int(m.group("n"))
        if 20 < n < 5000:
            if q.size_sqm_min is None or n < q.size_sqm_min:
                q.size_sqm_min = n
            if q.size_sqm_max is None or n > q.size_sqm_max:
                q.size_sqm_max = n

    # Percent — down payment or installment %
    for m in _PERCENT_RE.finditer(text):
        n = int(m.group("n"))
        ctx = (m.group("ctx") or "").lower()
        if "down" in ctx or "deposit" in ctx or "مقدم" in ctx:
            q.down_payment_pct_max = n

    # Installment years
    iy = _INSTALLMENT_YEARS_RE.search(text)
    if iy:
        years = int(iy.group("n"))
        # only count when context is payment-related (avoid year-of-build noise)
        if any(
            cue in text for cue in
            ("year", "yr", "سنة", "سنه", "سنوات", "سنين", "installment", "قسط", "تقسيط", "plan")
        ):
            if 1 <= years <= 20:
                q.installment_years_min = years

    # Delivery year
    q_m = _QUARTER_RE.search(text)
    if q_m:
        q.ready_by_year_max = int(q_m.group("year"))
    else:
        # year-only — only count if context says "by", "ready by", "delivery"
        for m in _YEAR_RE.finditer(text):
            year = int(m.group("year"))
            if 2024 <= year <= 2035:
                pos = m.start()
                ctx_window = text[max(0, pos - 30):pos]
                if re.search(
                    r"(by|before|until|ready|delivery|تسليم|deliver|handover|قبل|بحلول)",
                    ctx_window,
                ):
                    q.ready_by_year_max = year

    # Price — anchored to cue words OR scale words (m/million/k/مليون etc.)
    # to avoid catching unrelated numbers (bedroom counts, sizes, etc.).
    cue_positions = [m.start() for m in _PRICE_CUE_WORDS.finditer(text)]
    for m in _PRICE_NUMBER_RE.finditer(text):
        num_start = m.start("num")
        has_scale = m.group("scale") is not None
        # Accept this number if either:
        #   - it carries a scale word ("15M", "15 مليون") — the scale itself is the cue
        #   - OR a cue word (budget, price, under, ميزانية, …) is within 40 chars
        near_cue = any(abs(num_start - cp) < 40 for cp in cue_positions)
        if not (has_scale or near_cue):
            continue
        price = _parse_price_with_scale(m.group("num"), m.group("scale"))
        if not (100_000 <= price <= 1_000_000_000):
            continue
        # Check if min-cue ("at least", "over", "اكثر من") is DIRECTLY before
        # this number (within 15 chars — long enough for "at least " + number
        # but short enough to not bleed across separate price clauses).
        near = text[max(0, num_start - 15):num_start]
        if _PRICE_MIN_CUE.search(near):
            # Use a tighter min: keep the smallest min seen (in case multiple
            # interpretations match — e.g. "at least 5 million or even 7 million").
            if q.price_min is None or price < q.price_min:
                q.price_min = price
        else:
            if q.price_max is None or price > q.price_max:
                q.price_max = price

    return q


# ─────────────────────────────────────────────────────────────────────────────
# Extractor 2 — locations (canonical Egyptian zones)
# ─────────────────────────────────────────────────────────────────────────────

# Build a reverse-lookup once at import time.
# Source: LOCATION_ZONE_MAP in deterministic_normalizer.py
# Key = lowercase token to match, Value = canonical zone name to filter against.
_LOCATION_LOOKUP: dict[str, str] = {
    k.lower().strip(): v for k, v in LOCATION_ZONE_MAP.items()
}
# Also map canonical → canonical (so "New Cairo" also matches itself).
for v in set(LOCATION_ZONE_MAP.values()):
    _LOCATION_LOOKUP.setdefault(v.lower().strip(), v)

# Arabic dialect extras (LOCATION_ZONE_MAP in the normalizer is sparse on
# Arabic; supplement with the conversational forms buyers actually type).
_ARABIC_LOCATION_EXTRAS: dict[str, str] = {
    "القاهرة الجديدة": "New Cairo",
    "قاهرة جديدة": "New Cairo",
    "القاهرة جديدة": "New Cairo",
    "كايرو الجديدة": "New Cairo",
    "الشيخ زايد": "Sheikh Zayed",
    "زايد": "Sheikh Zayed",
    "مدينة الشيخ زايد": "Sheikh Zayed",
    "زايد الجديدة": "New Zayed",
    "نيو زايد": "New Zayed",
    "السادس من اكتوبر": "6th October",
    "السادس من أكتوبر": "6th October",
    "6 اكتوبر": "6th October",
    "6 أكتوبر": "6th October",
    "اكتوبر": "6th October",
    "أكتوبر": "6th October",
    "العاصمة الادارية": "New Administrative Capital",
    "العاصمة الإدارية": "New Administrative Capital",
    "العاصمة الجديدة": "New Administrative Capital",
    "الساحل الشمالي": "North Coast",
    "الساحل": "North Coast",
    "ساحل": "North Coast",
    "العين السخنة": "Ain Sokhna",
    "السخنة": "Ain Sokhna",
    "عين السخنة": "Ain Sokhna",
    "المعادي": "Maadi",
    "معادي": "Maadi",
    "الزمالك": "Zamalek",
    "زمالك": "Zamalek",
    "مصر الجديدة": "Heliopolis",
    "هليوبوليس": "Heliopolis",
    "مدينة نصر": "Nasr City",
    "نصر": "Nasr City",
    "المهندسين": "Mohandessin",
    "الدقي": "Dokki",
}
for k, v in _ARABIC_LOCATION_EXTRAS.items():
    _LOCATION_LOOKUP.setdefault(k.lower().strip(), v)


def extract_locations(prompt: str, q: StructuredQuery) -> StructuredQuery:
    text = _normalize(prompt)
    found: list[str] = []
    # Greedy longest-match — sort tokens by length desc so "north coast" beats "north"
    for token in sorted(_LOCATION_LOOKUP.keys(), key=len, reverse=True):
        if not token:
            continue
        # word-boundary match for Latin; substring match for Arabic (boundaries unreliable)
        if _has_arabic(token):
            if token in text:
                canonical = _LOCATION_LOOKUP[token]
                if canonical not in found:
                    found.append(canonical)
        else:
            if re.search(rf"\b{re.escape(token)}\b", text):
                canonical = _LOCATION_LOOKUP[token]
                if canonical not in found:
                    found.append(canonical)
    q.locations = found
    return q


# ─────────────────────────────────────────────────────────────────────────────
# Extractor 3 — property type (Apartment/Villa/etc.)
# ─────────────────────────────────────────────────────────────────────────────

def extract_property_types(prompt: str, q: StructuredQuery) -> StructuredQuery:
    text = _normalize(prompt)
    found: list[str] = []
    for token, canonical in _TYPE_MAP.items():
        if _has_arabic(token):
            if token in text and canonical not in found:
                found.append(canonical)
        else:
            if re.search(rf"\b{re.escape(token.lower())}\b", text) and canonical not in found:
                found.append(canonical)
    q.property_types = found
    return q


# ─────────────────────────────────────────────────────────────────────────────
# Extractor 4 — finishing (Fully Finished / Semi-Finished / Core & Shell)
# ─────────────────────────────────────────────────────────────────────────────

def extract_finishing(prompt: str, q: StructuredQuery) -> StructuredQuery:
    text = _normalize(prompt)
    found: list[str] = []
    for token, canonical in _FINISHING_MAP.items():
        token_low = token.lower()
        if _has_arabic(token):
            if token in text and canonical not in found:
                found.append(canonical)
        else:
            if token_low in text and canonical not in found:
                found.append(canonical)
    q.finishing_levels = found
    return q


# ─────────────────────────────────────────────────────────────────────────────
# Extractor 4b — compound + developer name dictionaries
# ─────────────────────────────────────────────────────────────────────────────
#
# These can't be hard-coded: compounds and developers grow as the scraper
# ingests new inventory. The caller (property_retrieval.retrieve) is async
# and loads the lists from property_dictionaries.{get_compounds, get_developers}
# (Redis-cached), then passes them into extract_query as kwargs. Keeps this
# module sync + I/O-free.

def _match_named_entities(prompt_norm: str, prompt_lower: str, names: list[str]) -> list[str]:
    """
    Longest-match-first scan of `names` against the prompt. Returns the
    canonical names that matched (preserves case from the input list).

    Match rules:
      - Latin names: case-insensitive, word-boundary match (so 'Mountain View'
        doesn't get caught by 'Mountain View Hyde Park' partial).
      - Arabic / non-Latin: case-insensitive substring (word boundaries are
        unreliable for Arabic). Longest first wins.
    """
    if not names:
        return []
    found: list[str] = []
    consumed_spans: list[tuple[int, int]] = []

    def overlaps_consumed(start: int, end: int) -> bool:
        for s, e in consumed_spans:
            if start < e and end > s:
                return True
        return False

    # names list is already sorted longest-first by the loader
    for name in names:
        if not name:
            continue
        name_low = name.lower()
        if _has_arabic(name):
            idx = prompt_lower.find(name_low)
            if idx >= 0 and not overlaps_consumed(idx, idx + len(name_low)):
                consumed_spans.append((idx, idx + len(name_low)))
                if name not in found:
                    found.append(name)
        else:
            # Word-boundary Latin match (re.escape handles regex meta chars in names)
            for m in re.finditer(rf"\b{re.escape(name_low)}\b", prompt_lower):
                if not overlaps_consumed(m.start(), m.end()):
                    consumed_spans.append((m.start(), m.end()))
                    if name not in found:
                        found.append(name)
                    break  # only need to record the name once
    return found


def extract_compounds(prompt: str, q: StructuredQuery, compound_names: Optional[list[str]] = None) -> StructuredQuery:
    """Populates q.compounds from the prompt against a known list."""
    if not compound_names:
        return q
    text = _normalize(prompt)
    matched = _match_named_entities(text, text, compound_names)
    # Preserve order: longest-first from matcher, dedup
    for c in matched:
        if c not in q.compounds:
            q.compounds.append(c)
    return q


def extract_developers(prompt: str, q: StructuredQuery, developer_names: Optional[list[str]] = None) -> StructuredQuery:
    """Populates q.developers from the prompt against a known list."""
    if not developer_names:
        return q
    text = _normalize(prompt)
    matched = _match_named_entities(text, text, developer_names)
    for d in matched:
        if d not in q.developers:
            q.developers.append(d)
    return q


# ─────────────────────────────────────────────────────────────────────────────
# Extractor 5 — payment & delivery intent flags
# ─────────────────────────────────────────────────────────────────────────────

_PAYMENT_PLAN_CUE = re.compile(
    r"(payment\s*plan|installment|تقسيط|اقساط|أقساط|قسط|monthly)",
    re.IGNORECASE,
)
_CASH_ONLY_CUE = re.compile(r"\b(cash\s*only|cash\s*price|كاش|نقدا|نقداً)\b", re.IGNORECASE)
_NAWY_NOW_CUE = re.compile(
    r"(nawy\s*now|instant\s*delivery|ready\s*to\s*move|move\s*in\s*now|"
    r"ready\s*now|تسليم\s*فوري|جاهزة|جاهز\s*للسكن)",
    re.IGNORECASE,
)
_DELIVERED_CUE = re.compile(
    r"\b(delivered|ready|handed\s*over|تم\s*التسليم|مستلم|مستلمة)\b", re.IGNORECASE,
)
_RESALE_CUE = re.compile(r"\b(resale|second\s*hand|إعادة\s*بيع|اعادة\s*بيع)\b", re.IGNORECASE)
_DEVELOPER_SALE_CUE = re.compile(r"\b(off[\s-]*plan|new\s*launch|primary|من\s*المطور)\b", re.IGNORECASE)


def extract_payment_intent(prompt: str, q: StructuredQuery) -> StructuredQuery:
    text = _normalize(prompt)
    if _PAYMENT_PLAN_CUE.search(text):
        q.is_cash_only = False
        if q.installment_years_min is None:
            q.installment_years_min = 1
    if _CASH_ONLY_CUE.search(text):
        q.is_cash_only = True
    if _NAWY_NOW_CUE.search(text):
        q.is_nawy_now = True
    if _DELIVERED_CUE.search(text) and q.is_nawy_now is None:
        q.is_delivered = True
    if _RESALE_CUE.search(text):
        if "Resale" not in q.sale_types:
            q.sale_types.append("Resale")
    if _DEVELOPER_SALE_CUE.search(text):
        if "Developer" not in q.sale_types:
            q.sale_types.append("Developer")
    return q


# ─────────────────────────────────────────────────────────────────────────────
# Extractor 6 — intent tags (persona/lifestyle, used by L3 boosts)
# ─────────────────────────────────────────────────────────────────────────────

_INTENT_TAG_RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b(diaspora|expat|abroad|مغترب|من\s*برة)\b", re.IGNORECASE), "diaspora"),
    (re.compile(r"\b(first[\s-]*time|أول\s*مرة|اول\s*شقة)\b", re.IGNORECASE), "first_time_buyer"),
    (re.compile(r"\b(investor|investment|roi|عائد|للاستثمار|استثمار)\b", re.IGNORECASE), "investor"),
    (re.compile(r"\b(family|kids|children|عيال|اولاد|أولاد|عائلة)\b", re.IGNORECASE), "family"),
    (re.compile(r"\b(retire|retirement|تقاعد)\b", re.IGNORECASE), "retiree"),
    (re.compile(r"\b(luxury|premium|elite|فاخر|فخم)\b", re.IGNORECASE), "luxury"),
]


def extract_intent_tags(prompt: str, q: StructuredQuery) -> StructuredQuery:
    text = prompt or ""
    for pat, tag in _INTENT_TAG_RULES:
        if pat.search(text) and tag not in q.intent_tags:
            q.intent_tags.append(tag)
    # Derive "needs_delivery_by_<year>" from the ready_by_year_max
    if q.ready_by_year_max and q.ready_by_year_max <= 2025:
        tag = f"needs_delivery_by_{q.ready_by_year_max}"
        if tag not in q.intent_tags:
            q.intent_tags.append(tag)
    return q


# ─────────────────────────────────────────────────────────────────────────────
# Extractor 7 — semantic text (the leftover after structured extraction)
# ─────────────────────────────────────────────────────────────────────────────

# Words to STRIP from semantic_text because they're already structured filters
# or are stop words that don't help BM25.
_STOPWORDS = {
    "i", "want", "need", "looking", "for", "show", "me", "find", "search",
    "with", "in", "at", "the", "a", "an", "and", "or", "of", "to", "on",
    "from", "by", "is", "are", "have", "has", "any", "some", "all", "my",
    "your", "their", "his", "her", "this", "that", "these", "those",
    "ابحث", "ابغى", "اريد", "أريد", "عايز", "محتاج", "في", "من", "ل", "على",
    "egp", "ج.م", "جنيه", "br", "bd", "bedroom", "bedrooms", "sqm", "m2", "m²",
    "متر", "year", "years", "yr", "yrs", "سنة", "سنوات",
}


def extract_semantic_text(prompt: str, q: StructuredQuery) -> StructuredQuery:
    """
    Pull out the descriptive leftover words after structured extraction.
    Used by L2b BM25 (search_tsv match). Never embedded.
    """
    text = _normalize(prompt)

    # Remove all matched structural pieces
    text = _PRICE_NUMBER_RE.sub(" ", text)
    text = _BED_RE.sub(" ", text)
    text = _SIZE_RE.sub(" ", text)
    text = _PERCENT_RE.sub(" ", text)
    text = _YEAR_RE.sub(" ", text)
    text = _INSTALLMENT_YEARS_RE.sub(" ", text)

    for loc in q.locations:
        text = re.sub(rf"\b{re.escape(loc.lower())}\b", " ", text)
    for ptype in q.property_types:
        text = re.sub(rf"\b{re.escape(ptype.lower())}\b", " ", text)
    for fin in q.finishing_levels:
        text = re.sub(rf"\b{re.escape(fin.lower())}\b", " ", text)

    # Drop stopwords; keep the rest as the semantic remainder
    tokens = [tok for tok in re.split(r"[^\w؀-ۿ]+", text) if tok and tok not in _STOPWORDS and len(tok) > 2]
    q.semantic_text = " ".join(tokens).strip()
    return q


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def extract_query(
    prompt: str,
    buyer_budget_cap: Optional[int] = None,
    buyer_persona: Optional[str] = None,
    compound_names: Optional[list[str]] = None,
    developer_names: Optional[list[str]] = None,
) -> StructuredQuery:
    """
    Pure-Python intent extraction. No LLM, no API calls, no awaits.

    Order matters: extract structured signals first, then derive semantic
    remainder from what's left, then add intent tags + buyer context.

    `compound_names` and `developer_names` are pre-loaded lists (typically
    Redis-cached by property_dictionaries.{get_compounds, get_developers})
    passed in by the async caller so this function stays I/O-free.
    Both default to None; when absent, those extractors are skipped.

    Returns a fresh StructuredQuery; never raises (logs on bad input).
    """
    q = StructuredQuery(
        buyer_budget_cap=buyer_budget_cap,
        buyer_persona=buyer_persona,
    )
    if not prompt or not isinstance(prompt, str):
        return q
    try:
        q = extract_numbers(prompt, q)
        q = extract_locations(prompt, q)
        q = extract_property_types(prompt, q)
        q = extract_finishing(prompt, q)
        q = extract_compounds(prompt, q, compound_names)
        q = extract_developers(prompt, q, developer_names)
        q = extract_payment_intent(prompt, q)
        q = extract_intent_tags(prompt, q)
        q = extract_semantic_text(prompt, q)
    except Exception as exc:
        # Never break the chat over a bad prompt
        logger.warning("[zero_token_intent] extract_query failed: %s", exc)
    return q
