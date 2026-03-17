"""
LLM Normalization Service
--------------------------
Pillar 3: AI-powered edge normalization.

Takes the raw JSON payload extracted from Nawy.com (either from __NEXT_DATA__
or XHR interception) and uses gpt-4o-mini with structured JSON output to:

  1. Standardize property types → strict Literal enum
  2. Normalize finishing status → strict Literal enum
  3. Map Egyptian location aliases → canonical zone names
  4. Extract and type-coerce numeric fields (price, size, bedrooms, etc.)
  5. Return Pydantic v2-validated NormalizedProperty objects

Cost note: gpt-4o-mini at $0.00015/1K input + $0.0006/1K output.
           With ~500 tokens per unit call, 30 units/compound, 500 compounds:
           ≈ $1.15 per full scrape run.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, List, Literal, Optional

from openai import AsyncOpenAI
from pydantic import BaseModel, Field, field_validator, model_validator
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Egyptian Location Zone Mapping
# ─────────────────────────────────────────────────────────────────────────────
# The LLM receives this map in its system prompt so it normalizes during
# generation. We also apply it as a Pydantic validator post-parse as a safety net.

LOCATION_ZONE_MAP: dict[str, str] = {
    # ── New Cairo cluster ────────────────────────────────────────────────────
    "Fifth Settlement": "New Cairo",
    "5th Settlement": "New Cairo",
    "التجمع الخامس": "New Cairo",
    "Al Rehab": "New Cairo",
    "El Rehab": "New Cairo",
    "Rehab": "New Cairo",
    "Madinaty": "New Cairo",
    "Future City": "New Cairo",
    "El Shorouk": "New Cairo",
    "Shorouk City": "New Cairo",
    "Al Mostakbal City": "New Cairo",
    "Mostakbal City": "New Cairo",
    "New Cairo City": "New Cairo",
    "مدينة المستقبل": "New Cairo",
    # ── Sheikh Zayed / 6th October cluster ──────────────────────────────────
    "الشيخ زايد": "Sheikh Zayed",
    "6th of October": "6th October",
    "6 October": "6th October",
    "6 Oct": "6th October",
    "السادس من أكتوبر": "6th October",
    "October": "6th October",
    # ── New Administrative Capital ───────────────────────────────────────────
    "New Capital": "New Administrative Capital",
    "NAC": "New Administrative Capital",
    "العاصمة الإدارية": "New Administrative Capital",
    "العاصمة": "New Administrative Capital",
    "Administrative Capital": "New Administrative Capital",
    "R7": "New Administrative Capital",
    "R8": "New Administrative Capital",
    "R3": "New Administrative Capital",
    # ── New Zayed ────────────────────────────────────────────────────────────
    "New Zayed City": "New Zayed",
    "Zayed City": "New Zayed",
    # ── North Coast ─────────────────────────────────────────────────────────
    "Sahel": "North Coast",
    "الساحل": "North Coast",
    "Sidi Abdel Rahman": "North Coast",
    "Sidi Abd El Rahman": "North Coast",
    "Ras El Bar": "North Coast",
    "Ras El Hekma": "North Coast",
    "Marsa Matrouh": "North Coast",
    "El Alamein": "North Coast",
    "New Alamein": "North Coast",
    # ── Ain Sokhna ───────────────────────────────────────────────────────────
    "Sokhna": "Ain Sokhna",
    "عين السخنة": "Ain Sokhna",
    "El Sokhna": "Ain Sokhna",
    # ── Greater Cairo / Historical ───────────────────────────────────────────
    "Maadi": "Maadi",
    "المعادي": "Maadi",
    "Heliopolis": "Heliopolis",
    "مصر الجديدة": "Heliopolis",
    "Nasr City": "Nasr City",
    "مدينة نصر": "Nasr City",
    "Zamalek": "Zamalek",
    "Downtown Cairo": "Downtown Cairo",
    "Dokki": "Dokki",
    "Mohandessin": "Mohandessin",
    # ── Satellite cities ─────────────────────────────────────────────────────
    "Obour City": "Obour",
    "El Obour": "Obour",
    "Badr City": "Badr City",
    "10th of Ramadan": "10th of Ramadan",
    "Bdr": "Badr City",
    # ── South Cairo / Suez corridor ──────────────────────────────────────────
    "New Heliopolis": "New Heliopolis",
    "Katameya": "New Cairo",  # Katameya is within New Cairo axis
    "El Katameya": "New Cairo",
}

# Canonical zone names used in the LLM prompt as the allowed output list
CANONICAL_ZONES = sorted(set(LOCATION_ZONE_MAP.values()))

# ─────────────────────────────────────────────────────────────────────────────
# Pydantic v2 Schemas
# ─────────────────────────────────────────────────────────────────────────────

PropertyType = Literal[
    "Apartment", "Villa", "Townhouse", "Studio", "Duplex",
    "Penthouse", "Chalet", "Office", "Retail", "Twin House",
    "Mixed Use", "Other"
]

FinishingStatus = Literal[
    "Core & Shell", "Semi-Finished", "Fully Finished", "Furnished", "Unknown"
]


class NormalizedProperty(BaseModel):
    """
    Validated, normalized property record ready for DB upsert.
    All field names align directly with app.models.Property columns.
    """

    # ── Identity ──────────────────────────────────────────────────────────────
    nawy_url: str = Field(..., description="Full Nawy.com compound/unit URL")
    nawy_reference: Optional[str] = Field(None, description="Internal Nawy property ID")

    # ── Core attributes (used for content_hash) ───────────────────────────────
    title: str
    type: PropertyType
    location: str = Field(..., description="Canonical Egyptian market zone")
    compound: Optional[str] = None
    developer: Optional[str] = None
    price: float = Field(..., ge=0)
    size_sqm: int = Field(..., ge=0, description="Built-up area in square meters")
    finishing: FinishingStatus

    # ── Secondary attributes ──────────────────────────────────────────────────
    description: Optional[str] = None
    price_per_sqm: Optional[float] = Field(None, ge=0)
    bedrooms: int = Field(0, ge=0)
    bathrooms: Optional[int] = Field(None, ge=0)
    delivery_date: Optional[str] = None          # e.g. "Q2 2026", "2025", "Immediate"
    down_payment_percentage: Optional[int] = Field(None, ge=0, le=100)
    installment_years: Optional[int] = Field(None, ge=0)
    monthly_installment: Optional[float] = Field(None, ge=0)
    image_url: Optional[str] = None
    sale_type: Optional[str] = None              # "Resale" | "Developer" | "Nawy Now"
    is_nawy_now: bool = False
    is_delivered: bool = False
    is_cash_only: bool = False
    land_area: Optional[int] = Field(None, ge=0, description="Land area sqm (for villas)")

    @field_validator("price", "size_sqm", mode="before")
    @classmethod
    def coerce_positive_numeric(cls, v: Any) -> Any:
        """Accept int/float/str, strip commas, return non-negative float/int."""
        if v is None:
            return 0
        if isinstance(v, str):
            v = v.replace(",", "").strip()
            if not v:
                return 0
        try:
            return max(float(v), 0)
        except (ValueError, TypeError):
            return 0

    @field_validator("location", mode="after")
    @classmethod
    def apply_zone_mapping(cls, v: str) -> str:
        """Post-LLM safety net: apply Egyptian zone alias map."""
        return LOCATION_ZONE_MAP.get(v.strip(), v.strip())

    @model_validator(mode="after")
    def derive_price_per_sqm(self) -> "NormalizedProperty":
        """Auto-compute price_per_sqm if not provided and both components exist."""
        if self.price_per_sqm is None and self.price > 0 and self.size_sqm > 0:
            self.price_per_sqm = round(self.price / self.size_sqm, 2)
        return self


class NormalizationResult(BaseModel):
    """Container for a batch normalization result."""
    properties: List[NormalizedProperty] = Field(default_factory=list)
    skipped_count: int = 0
    errors: List[str] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# LLM Client + System Prompt
# ─────────────────────────────────────────────────────────────────────────────

_openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MAX_UNITS_PER_COMPOUND = int(os.getenv("MAX_UNITS_PER_COMPOUND", "30"))

_LOCATION_ZONE_LIST = "\n".join(f"  - {z}" for z in CANONICAL_ZONES)
_ALIAS_EXAMPLES = "\n".join(
    f'  "{k}" → "{v}"' for k, v in list(LOCATION_ZONE_MAP.items())[:12]
)

SYSTEM_PROMPT = f"""
You are an expert real estate data normalization AI for the Egyptian property market.

Given raw JSON scraped from Nawy.com (Egypt's largest property platform), extract and
normalize ONE property record into the exact JSON schema below. Return ONLY valid JSON.

──────────────────────────────────────────────
FIELD RULES
──────────────────────────────────────────────

type — MUST be one of:
  Apartment, Villa, Townhouse, Studio, Duplex, Penthouse,
  Chalet, Office, Retail, Twin House, Mixed Use, Other

finishing — MUST be one of:
  Core & Shell, Semi-Finished, Fully Finished, Furnished, Unknown
  (Map Arabic: "كور وشيل"→"Core & Shell", "تشطيب كامل"→"Fully Finished",
   "نص تشطيب"→"Semi-Finished", "مفروشة"→"Furnished")

location — Output ONLY from this canonical list:
{_LOCATION_ZONE_LIST}

  Location alias examples:
{_ALIAS_EXAMPLES}

price — Numeric EGP value, no currency symbol, no commas. 0 if unknown.
size_sqm — Built-up area (BUA) as integer. 0 if unknown.
delivery_date — String like "Q2 2026", "2025", "Immediate", or null.
down_payment_percentage — Integer 0–100, or null.
sale_type — One of "Resale", "Developer", "Nawy Now", or null.
nawy_url — Must be the exact Nawy.com URL from the source data.
nawy_reference — Nawy's internal property/unit ID if visible, else null.

If a field is not present in the raw data, set it to null.
Do NOT invent data. Do NOT hallucinate prices or sizes.

──────────────────────────────────────────────
REQUIRED OUTPUT SCHEMA (JSON only, no markdown)
──────────────────────────────────────────────
{{
  "nawy_url": "string",
  "nawy_reference": "string|null",
  "title": "string",
  "type": "Apartment|Villa|...",
  "location": "string (from canonical list)",
  "compound": "string|null",
  "developer": "string|null",
  "price": number,
  "size_sqm": integer,
  "finishing": "Core & Shell|...",
  "description": "string|null",
  "price_per_sqm": number|null,
  "bedrooms": integer,
  "bathrooms": integer|null,
  "delivery_date": "string|null",
  "down_payment_percentage": integer|null,
  "installment_years": integer|null,
  "monthly_installment": number|null,
  "image_url": "string|null",
  "sale_type": "string|null",
  "is_nawy_now": boolean,
  "is_delivered": boolean,
  "is_cash_only": boolean,
  "land_area": integer|null
}}
""".strip()


# ─────────────────────────────────────────────────────────────────────────────
# LLM Normalization (single unit)
# ─────────────────────────────────────────────────────────────────────────────

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def _call_llm_normalize(raw_unit_json: str) -> NormalizedProperty:
    """
    Single gpt-4o-mini call with JSON response format enforcement.

    Tenacity retries on any exception (rate limits, transient network errors).
    Pydantic v2 validates the response; ValidationError propagates to caller.

    Args:
        raw_unit_json: JSON string of a single unit/property dict from the scraper.

    Returns:
        NormalizedProperty instance (Pydantic-validated).

    Raises:
        ValidationError: If LLM output doesn't match schema after 3 retries.
    """
    response = await _openai_client.chat.completions.create(
        model=os.getenv("GPT_MINI_MODEL", "gpt-4o-mini"),
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Normalize this Nawy.com property JSON:\n\n{raw_unit_json}",
            },
        ],
        temperature=0,
        max_tokens=900,
    )

    raw_output = response.choices[0].message.content
    return NormalizedProperty.model_validate_json(raw_output)


# ─────────────────────────────────────────────────────────────────────────────
# Unit Discovery (raw JSON structure navigation)
# ─────────────────────────────────────────────────────────────────────────────

def _find_units_in_json(data: Any, max_depth: int = 6) -> list[dict]:
    """
    Recursively searches for the array of unit/property dicts inside the
    raw __NEXT_DATA__ or XHR payload.

    Nawy structures vary per page type:
      - Compound detail:  data["props"]["pageProps"]["compound"]["units"]
      - Search results:   data["props"]["pageProps"]["compounds"]
      - Unit listing:     data["props"]["pageProps"]["units"]

    We detect arrays whose first element looks like a property dict by
    checking for the presence of price/price-like and size/area-like keys.

    Args:
        data:      Any parsed JSON value.
        max_depth: Recursion limit to prevent infinite loops on circular refs.

    Returns:
        First matching list[dict] found, or [] if nothing looks like units.
    """
    _PRICE_KEYS = {"price", "minPrice", "max_price", "min_price", "startingFrom", "starting_price"}
    _SIZE_KEYS = {"area", "size", "built_up_area", "bua", "size_sqm", "builtUpArea"}

    def _is_property_like(obj: Any) -> bool:
        if not isinstance(obj, dict):
            return False
        keys_lower = {k.lower() for k in obj}
        has_price = bool(keys_lower & {k.lower() for k in _PRICE_KEYS})
        has_size = bool(keys_lower & {k.lower() for k in _SIZE_KEYS})
        return has_price or has_size

    def _search(node: Any, depth: int) -> list[dict] | None:
        if depth <= 0:
            return None
        if isinstance(node, list):
            if node and all(_is_property_like(item) for item in node[:3]):
                return [item for item in node if isinstance(item, dict)]
        if isinstance(node, dict):
            # Prioritize well-known key names
            for key in ("units", "compounds", "properties", "listings", "results", "data"):
                if key in node:
                    candidate = _search(node[key], depth - 1)
                    if candidate:
                        return candidate
            # Fall back to any key
            for val in node.values():
                candidate = _search(val, depth - 1)
                if candidate:
                    return candidate
        return None

    result = _search(data, max_depth)
    return result if result is not None else []


def _flatten_compound_as_unit(raw: dict, source_url: str) -> dict:
    """
    Fallback: treats the entire compound-level JSON as a single property dict.
    Used when no unit array is found (e.g. compound info-only pages).
    """
    return {
        **raw,
        "_source_url": source_url,
        "_is_compound_level": True,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Public Batch Normalizer
# ─────────────────────────────────────────────────────────────────────────────

async def normalize_properties(raw_compound_json: dict) -> NormalizationResult:
    """
    Batch normalizer for one compound's raw scraped JSON.

    Steps:
      1. Detect unit array with _find_units_in_json()
      2. If no units found: treat whole payload as one compound-level unit
      3. Cap to MAX_UNITS_PER_COMPOUND to control LLM cost
      4. For each unit: call _call_llm_normalize() (with retry)
      5. Collect successes; log + skip ValidationErrors

    Args:
        raw_compound_json: Full __NEXT_DATA__ or XHR payload dict from core_scraper.

    Returns:
        NormalizationResult with list of NormalizedProperty.
    """
    result = NormalizationResult()
    source_url = raw_compound_json.get("_meta", {}).get("source_url", "unknown")

    units = _find_units_in_json(raw_compound_json)

    if not units:
        logger.warning("[normalizer] No unit array found in payload for %s — trying compound-level", source_url)
        units = [_flatten_compound_as_unit(raw_compound_json, source_url)]

    if len(units) > MAX_UNITS_PER_COMPOUND:
        logger.info(
            "[normalizer] Capping %d units to %d for %s (cost control)",
            len(units), MAX_UNITS_PER_COMPOUND, source_url,
        )
        units = units[:MAX_UNITS_PER_COMPOUND]

    logger.info("[normalizer] Normalizing %d units for %s", len(units), source_url)

    for i, unit in enumerate(units):
        # Small jitter between LLM calls to stay under RPM limits
        if i > 0:
            await asyncio.sleep(0.15)

        unit_str = json.dumps(unit, ensure_ascii=False, default=str)[:4000]  # token budget guard

        try:
            normalized = await _call_llm_normalize(unit_str)
            result.properties.append(normalized)
        except Exception as exc:
            msg = f"Unit {i + 1} at {source_url}: {exc}"
            logger.error("[normalizer] Failed to normalize unit — %s", msg)
            result.skipped_count += 1
            result.errors.append(msg)

    logger.info(
        "[normalizer] Done for %s — normalized=%d skipped=%d",
        source_url,
        len(result.properties),
        result.skipped_count,
    )
    return result
