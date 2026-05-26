"""
Deterministic Normalization Service
-------------------------------------
Zero-token replacement for llm_normalizer.py.

Handles real Nawy.com field names as observed live:
  - Compound units:  id, slug, compound.slug, area.name, developer.name,
                     min_unit_area, min_price, number_of_bedrooms, number_of_bathrooms,
                     finishing ("semi_finished"), min_ready_by (ISO), property_type.name,
                     resale (bool), financing (bool)
  - Nawy Now units:  unitArea, readyBy, imageUrl, propertyType (str), paymentPlan.*,
                     compound.slug, compoundSlug, areaName, developerName, saleType
  - Featured units:  flat camelCase: compoundSlug, areaName, developerName, coverImage,
                     minPrice, unitArea, installmentYears, downPaymentValue

No API calls. No tokens consumed. Never raises on missing fields.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Egyptian Location Zone Mapping
# ─────────────────────────────────────────────────────────────────────────────

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
    "6th of October City": "6th October",
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
    "Katameya": "New Cairo",
    "El Katameya": "New Cairo",
}

CANONICAL_ZONES = sorted(set(LOCATION_ZONE_MAP.values()))

# ─────────────────────────────────────────────────────────────────────────────
# Pydantic v2 Schemas (identical public API to llm_normalizer)
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
    nawy_url: str = Field(..., description="Full Nawy.com compound/unit URL")
    nawy_reference: Optional[str] = Field(None)
    title: str
    type: PropertyType
    location: str = Field(..., description="Canonical Egyptian market zone")
    compound: Optional[str] = None
    developer: Optional[str] = None
    price: float = Field(..., ge=0)
    size_sqm: int = Field(..., ge=0)
    finishing: FinishingStatus
    description: Optional[str] = None
    price_per_sqm: Optional[float] = Field(None, ge=0)
    bedrooms: int = Field(0, ge=0)
    bathrooms: Optional[int] = Field(None, ge=0)
    delivery_date: Optional[str] = None
    down_payment_percentage: Optional[int] = Field(None, ge=0, le=100)
    installment_years: Optional[int] = Field(None, ge=0)
    monthly_installment: Optional[float] = Field(None, ge=0)
    image_url: Optional[str] = None
    sale_type: Optional[str] = None
    is_nawy_now: bool = False
    is_delivered: bool = False
    is_cash_only: bool = False
    land_area: Optional[int] = Field(None, ge=0)
    maintenance_fee_pct: Optional[int] = Field(None, ge=0, le=100)
    delivery_payment: Optional[float] = Field(None, ge=0)

    @field_validator("price", "size_sqm", mode="before")
    @classmethod
    def coerce_positive_numeric(cls, v: Any) -> Any:
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
        return LOCATION_ZONE_MAP.get(v.strip(), v.strip())

    @model_validator(mode="after")
    def derive_price_per_sqm(self) -> "NormalizedProperty":
        if self.price_per_sqm is None and self.price > 0 and self.size_sqm > 0:
            self.price_per_sqm = round(self.price / self.size_sqm, 2)
        return self


class NormalizationResult(BaseModel):
    properties: List[NormalizedProperty] = Field(default_factory=list)
    skipped_count: int = 0
    errors: List[str] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Type & Finishing Lookup Maps
# ─────────────────────────────────────────────────────────────────────────────

_TYPE_MAP: dict[str, str] = {
    # English
    "apartment": "Apartment", "flat": "Apartment",
    "villa": "Villa", "standalone villa": "Villa", "ivilla": "Villa",
    "i-villa": "Villa", "s-villa": "Villa", "standalone": "Villa",
    "townhouse": "Townhouse", "town house": "Townhouse", "townhome": "Townhouse",
    "twinhouse": "Twin House", "twin house": "Twin House", "twin-house": "Twin House",
    "studio": "Studio",
    "duplex": "Duplex",
    "penthouse": "Penthouse", "roof": "Penthouse",
    "chalet": "Chalet",
    "office": "Office",
    "retail": "Retail", "shop": "Retail",
    "mixed use": "Mixed Use", "mixed-use": "Mixed Use",
    "ground floor": "Apartment", "semi-detached": "Villa",
    # Arabic
    "شقة": "Apartment", "فيلا": "Villa", "تاون هاوس": "Townhouse",
    "توين هاوس": "Twin House", "استوديو": "Studio", "دوبلكس": "Duplex",
    "بنتهاوس": "Penthouse", "شاليه": "Chalet", "مكتب": "Office", "محل": "Retail",
}

_FINISHING_MAP: dict[str, str] = {
    # snake_case (real Nawy API values)
    "semi_finished": "Semi-Finished",
    "fully_finished": "Fully Finished",
    "core_shell": "Core & Shell",
    "core_and_shell": "Core & Shell",
    "not_finished": "Core & Shell",
    "furnished": "Furnished",
    "fully_furnished": "Furnished",
    # English natural language
    "core & shell": "Core & Shell",
    "core and shell": "Core & Shell",
    "core shell": "Core & Shell",
    "semi finished": "Semi-Finished",
    "semi-finished": "Semi-Finished",
    "semi finishing": "Semi-Finished",
    "half finished": "Semi-Finished",
    "fully finished": "Fully Finished",
    "full finishing": "Fully Finished",
    "finished": "Fully Finished",
    # Arabic
    "كور وشيل": "Core & Shell",
    "نص تشطيب": "Semi-Finished",
    "نصف تشطيب": "Semi-Finished",
    "تشطيب كامل": "Fully Finished",
    "تشطيب": "Fully Finished",
    "مفروشة": "Furnished",
    "مفروش": "Furnished",
}

# ─────────────────────────────────────────────────────────────────────────────
# Field Extraction Helpers
# ─────────────────────────────────────────────────────────────────────────────

_QUARTER_RE = re.compile(r"q([1-4])[^0-9]*(\d{4})", re.IGNORECASE)
_YEAR_MONTH_RE = re.compile(r"(\d{4})-(\d{2})-\d{2}")
_YEAR_RE = re.compile(r"\b(20\d{2})\b")


def _coerce_float(v: Any) -> float:
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return max(float(v), 0.0)
    s = str(v).replace(",", "").replace("EGP", "").replace("%", "").strip()
    try:
        return max(float(s), 0.0)
    except (ValueError, TypeError):
        return 0.0


def _coerce_int(v: Any) -> int:
    return int(_coerce_float(v))


def _first(*values: Any) -> Any:
    for v in values:
        if v is not None and v != "" and v != 0 and v is not False:
            return v
    return None


def _normalize_type(raw: Any) -> str:
    if not raw:
        return "Other"
    key = str(raw).strip().lower()
    return _TYPE_MAP.get(key, "Other")


def _normalize_finishing(raw: Any) -> str:
    if not raw:
        return "Unknown"
    key = str(raw).strip().lower()
    if key in _FINISHING_MAP:
        return _FINISHING_MAP[key]
    for pattern, value in _FINISHING_MAP.items():
        if pattern in key:
            return value
    return "Unknown"


def _normalize_location(raw: Any) -> str:
    if not raw:
        return "New Cairo"
    s = str(raw).strip()
    return LOCATION_ZONE_MAP.get(s, s)


def _extract_delivery_date(unit: dict) -> Optional[str]:
    if unit.get("isDelivered") or unit.get("is_delivered"):
        return "Delivered"

    raw = _first(
        unit.get("deliveryDate"), unit.get("delivery_date"),
        unit.get("min_ready_by"), unit.get("readyBy"), unit.get("ready_by"),
        unit.get("handoverDate"), unit.get("expectedDelivery"),
    )
    if not raw:
        return None

    raw_str = str(raw).strip()
    if re.match(r"Q[1-4]\s+20\d{2}", raw_str, re.IGNORECASE):
        return raw_str
    if raw_str.lower() in ("immediate", "delivered", "ready"):
        return "Delivered"

    # ISO datetime: "2023-10-31T00:00:00.000Z" or "2026-08-31"
    m = _YEAR_MONTH_RE.match(raw_str)
    if m:
        year = int(m.group(1))
        month = int(m.group(2))
        quarter = (month - 1) // 3 + 1
        return f"Q{quarter} {year}"

    m = _QUARTER_RE.search(raw_str)
    if m:
        return f"Q{m.group(1)} {m.group(2)}"

    m = _YEAR_RE.search(raw_str)
    if m:
        return m.group(1)

    return raw_str[:20] if len(raw_str) <= 20 else None


def _extract_developer(unit: dict) -> Optional[str]:
    # Context-injected flat fields
    direct = _first(
        unit.get("_developer_name"), unit.get("developerName"),
        unit.get("developer_name"),
    )
    if direct and isinstance(direct, str):
        return direct.strip() or None

    # Nested object
    dev_obj = unit.get("developer") or {}
    if isinstance(dev_obj, dict):
        name = _first(dev_obj.get("name"), dev_obj.get("en"), dev_obj.get("ar"))
        if name:
            return str(name).strip() or None

    # Last resort: string
    dev = unit.get("developer")
    if isinstance(dev, str) and dev.strip():
        return dev.strip()

    return None


def _extract_compound_name(unit: dict) -> Optional[str]:
    direct = _first(
        unit.get("_compound_name"), unit.get("compoundName"), unit.get("compound_name"),
    )
    if direct and isinstance(direct, str):
        return direct.strip() or None

    compound = unit.get("compound")
    if isinstance(compound, str) and compound.strip():
        return compound.strip()
    if isinstance(compound, dict):
        name = _first(compound.get("name"), compound.get("en"))
        if name:
            return str(name).strip() or None

    return None


def _extract_compound_slug(unit: dict) -> Optional[str]:
    """Get the compound slug for URL construction."""
    direct = _first(
        unit.get("_compound_slug"), unit.get("compoundSlug"), unit.get("compound_slug"),
    )
    if direct and isinstance(direct, str):
        return direct.strip() or None

    compound = unit.get("compound")
    if isinstance(compound, dict):
        slug = compound.get("slug")
        if slug:
            return str(slug).strip() or None

    return None


def _extract_location(unit: dict) -> str:
    # Flat context-injected field
    area_name = _first(unit.get("_area_name"), unit.get("areaName"), unit.get("area_name"))
    if area_name and isinstance(area_name, str):
        return _normalize_location(area_name)

    # Nested area object
    area = unit.get("area")
    if isinstance(area, dict):
        name = _first(area.get("name"), area.get("en"))
        if name:
            return _normalize_location(name)

    # Other location fields
    raw = _first(unit.get("location"), unit.get("zone"), unit.get("city"), unit.get("district"))
    if isinstance(raw, dict):
        raw = _first(raw.get("name"), raw.get("en"), raw.get("ar"))
    return _normalize_location(raw)


def _extract_type(unit: dict) -> str:
    # Nawy uses property_type.name (nested) or propertyType (string)
    pt = unit.get("property_type")
    if isinstance(pt, dict):
        name = _first(pt.get("name"), pt.get("en"))
        if name:
            return _normalize_type(name)

    raw = _first(
        unit.get("propertyType"),
        unit.get("type"), unit.get("unitType"), unit.get("unit_type"),
        unit.get("property_type") if isinstance(unit.get("property_type"), str) else None,
        unit.get("category"),
    )
    if isinstance(raw, dict):
        raw = _first(raw.get("name"), raw.get("en"))

    return _normalize_type(raw)


def _extract_image_url(unit: dict) -> Optional[str]:
    direct = _first(
        unit.get("image"), unit.get("imageUrl"), unit.get("image_url"),
        unit.get("coverImage"), unit.get("thumbnail"), unit.get("cover"),
    )
    if direct and isinstance(direct, str):
        return direct.strip()

    for key in ("images", "photos", "gallery"):
        imgs = unit.get(key)
        if isinstance(imgs, list) and imgs:
            first = imgs[0]
            if isinstance(first, str):
                return first.strip()
            if isinstance(first, dict):
                url = _first(first.get("url"), first.get("src"), first.get("path"))
                if url:
                    return str(url).strip()

    return None


def _extract_nawy_url(unit: dict) -> str:
    """
    Construct the canonical Nawy URL.
    Prefer /compound/{compound_slug}/property/{unit_slug} pattern.
    """
    unit_slug = unit.get("slug")
    compound_slug = _extract_compound_slug(unit)

    if unit_slug and compound_slug:
        return f"https://www.nawy.com/compound/{compound_slug}/property/{unit_slug}"

    # Direct URL fields
    direct = _first(unit.get("url"), unit.get("nawy_url"), unit.get("nawyUrl"), unit.get("link"))
    if direct and isinstance(direct, str):
        url = direct.strip()
        if url.startswith("http"):
            return url
        if url.startswith("/"):
            return f"https://www.nawy.com{url}"

    # Slug-only fallback
    if unit_slug:
        return f"https://www.nawy.com/property/{unit_slug}"

    # Meta source URL
    meta_url = (unit.get("_meta") or {}).get("source_url", "")
    return meta_url


def _extract_sale_type(unit: dict) -> Optional[str]:
    sale_type = unit.get("saleType") or unit.get("sale_type") or ""
    if "nawy_now" in str(sale_type).lower():
        return "Nawy Now"
    if unit.get("isNawyNow") or unit.get("is_nawy_now"):
        return "Nawy Now"
    if unit.get("isResale") or unit.get("is_resale") or unit.get("resale"):
        return "Resale"
    raw = _first(unit.get("saleType"), unit.get("sale_type"), unit.get("listingType"))
    if raw:
        raw_lower = str(raw).lower()
        if "nawy" in raw_lower:
            return "Nawy Now"
        if "resale" in raw_lower:
            return "Resale"
        if "developer" in raw_lower:
            return "Developer"
    return "Developer"


def _extract_price(unit: dict) -> float:
    # Direct price fields
    v = _first(
        unit.get("price"), unit.get("min_price"), unit.get("minPrice"),
        unit.get("starting_price"), unit.get("startingPrice"), unit.get("startingFrom"),
    )
    if v:
        return _coerce_float(v)

    # Nawy Now: price lives in paymentPlan.minPrice
    plan = unit.get("paymentPlan") or {}
    if isinstance(plan, dict):
        plan_price = _first(plan.get("minPrice"), plan.get("price"))
        if plan_price:
            return _coerce_float(plan_price)

    return 0.0


def _extract_size(unit: dict) -> int:
    """Extract built-up area. Checks min_unit_area / unitArea BEFORE 'area' (which is a location object)."""
    v = _first(
        unit.get("min_unit_area"), unit.get("minUnitArea"),
        unit.get("unitArea"), unit.get("unit_area"),
        unit.get("builtUpArea"), unit.get("built_up_area"), unit.get("bua"),
        unit.get("size"), unit.get("size_sqm"),
        unit.get("max_unit_area"),  # fallback to max if no min
    )
    return _coerce_int(v)


def _extract_down_payment(unit: dict) -> Optional[int]:
    v = _first(
        unit.get("_down_payment_percentage"),
        unit.get("downPaymentPercentage"), unit.get("down_payment_percentage"),
        unit.get("downPayment"), unit.get("down_payment"),
    )
    # Nawy Now: paymentPlan.downPaymentPercentage
    if v is None:
        plan = unit.get("paymentPlan") or {}
        if isinstance(plan, dict):
            v = plan.get("downPaymentPercentage")

    if v is None:
        return None
    f = _coerce_float(v)
    if 0 < f <= 1:
        f = f * 100
    result = int(round(f))
    return max(0, min(100, result)) if result > 0 else None


def _extract_installment_years(unit: dict) -> Optional[int]:
    raw = _first(
        unit.get("installmentYears"), unit.get("installment_years"),
        unit.get("paymentYears"), unit.get("years"),
        unit.get("minInstallmentYears"),
    )
    # Nawy Now: paymentPlan.numberOfInstallmentYears
    if raw is None:
        plan = unit.get("paymentPlan") or {}
        if isinstance(plan, dict):
            raw = plan.get("numberOfInstallmentYears")
    if raw is None:
        return None
    v = _coerce_int(raw)
    return v if v > 0 else None


def _extract_monthly_installment(unit: dict) -> Optional[float]:
    raw = _first(
        unit.get("monthlyInstallment"), unit.get("monthly_installment"),
        unit.get("installment"), unit.get("equalInstallmentsValue"),
    )
    # Nawy Now: paymentPlan.minInstallment
    if raw is None:
        plan = unit.get("paymentPlan") or {}
        if isinstance(plan, dict):
            raw = plan.get("minInstallment")
    if raw is None:
        return None
    v = _coerce_float(raw)
    return v if v > 0 else None


def _extract_title(unit: dict, prop_type: str, location: str, compound_name: Optional[str]) -> str:
    raw = _first(unit.get("title"), unit.get("name"), unit.get("unitTitle"))
    if raw and isinstance(raw, str):
        return raw.strip()
    return f"{prop_type} in {compound_name or location}"


# ─────────────────────────────────────────────────────────────────────────────
# Core Deterministic Normalizer
# ─────────────────────────────────────────────────────────────────────────────

def _deterministic_normalize(unit: dict) -> NormalizedProperty:
    """
    Pure Python extraction from a Nawy JSON unit object.
    Handles compound page units, Nawy Now listing units, and featured units.
    """
    prop_type = _extract_type(unit)
    location = _extract_location(unit)
    compound_name = _extract_compound_name(unit)
    developer = _extract_developer(unit)
    price = _extract_price(unit)
    size_sqm = _extract_size(unit)

    finishing_raw = _first(
        unit.get("finishing"), unit.get("finishingType"), unit.get("finishing_type"),
    )
    finishing = _normalize_finishing(finishing_raw)

    title = _extract_title(unit, prop_type, location, compound_name)
    nawy_url = _extract_nawy_url(unit)
    nawy_reference = str(unit["id"]) if unit.get("id") is not None else None

    bedrooms = _coerce_int(_first(
        unit.get("number_of_bedrooms"), unit.get("numberOfBedrooms"),
        unit.get("bedrooms"), unit.get("beds"),
    ))
    bathrooms_raw = _first(
        unit.get("number_of_bathrooms"), unit.get("numberOfBathrooms"),
        unit.get("bathrooms"), unit.get("baths"),
    )
    bathrooms = _coerce_int(bathrooms_raw) if bathrooms_raw is not None else None

    delivery_date = _extract_delivery_date(unit)
    down_payment_percentage = _extract_down_payment(unit)
    monthly_installment = _extract_monthly_installment(unit)
    installment_years = _extract_installment_years(unit)
    image_url = _extract_image_url(unit)
    sale_type = _extract_sale_type(unit)

    sale_type_lower = (sale_type or "").lower()
    is_nawy_now = bool(
        unit.get("isNawyNow") or unit.get("is_nawy_now")
        or "nawy" in sale_type_lower
        or str(unit.get("saleType", "")).lower() == "nawy_now"
    )
    is_delivered = bool(unit.get("isDelivered") or unit.get("is_delivered"))
    is_cash_only = bool(
        unit.get("isCashOnly") or unit.get("is_cash_only") or unit.get("cashOnly")
        or (unit.get("paymentPlan") or {}).get("isCash")
    )

    land_area_raw = _first(unit.get("landArea"), unit.get("land_area"), unit.get("plotArea"))
    land_area = _coerce_int(land_area_raw) if land_area_raw else None

    maint_raw = _first(
        unit.get("maintenanceFee"), unit.get("maintenance_fee"),
        unit.get("maintenanceFeePercentage"), unit.get("maintenance_fee_pct"),
    )
    maintenance_fee_pct = _coerce_int(maint_raw) if maint_raw else None

    delivery_payment_raw = _first(
        unit.get("deliveryPayment"), unit.get("delivery_payment"),
        unit.get("wadea"), unit.get("wadeea"), unit.get("handoverPayment"),
    )
    delivery_payment = _coerce_float(delivery_payment_raw) if delivery_payment_raw else None

    description = _first(unit.get("description"), unit.get("about"), unit.get("subtitle"))
    if description:
        description = str(description)[:2000]

    return NormalizedProperty(
        nawy_url=nawy_url,
        nawy_reference=nawy_reference,
        title=title,
        type=prop_type,
        location=location,
        compound=compound_name,
        developer=developer,
        price=price,
        size_sqm=size_sqm,
        finishing=finishing,
        description=description,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        delivery_date=delivery_date,
        down_payment_percentage=down_payment_percentage,
        installment_years=installment_years,
        monthly_installment=monthly_installment,
        image_url=image_url,
        sale_type=sale_type,
        is_nawy_now=is_nawy_now,
        is_delivered=is_delivered,
        is_cash_only=is_cash_only,
        land_area=land_area,
        maintenance_fee_pct=maintenance_fee_pct,
        delivery_payment=delivery_payment,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Unit Discovery (unchanged from llm_normalizer — pure Python)
# ─────────────────────────────────────────────────────────────────────────────

def _find_units_in_json(data: Any, max_depth: int = 6) -> list[dict]:
    """
    Recursively searches for the array of unit/property dicts inside the
    raw __NEXT_DATA__ or XHR payload.

    Primary Nawy structure:
      data["props"]["pageProps"]["availablePropertyTypes"][*]["properties"]
    """
    _PRICE_KEYS = {"price", "minPrice", "max_price", "min_price", "startingFrom",
                   "starting_price", "min_unit_area", "unitArea"}
    _SIZE_KEYS = {"area", "size", "built_up_area", "bua", "size_sqm", "builtUpArea",
                  "min_unit_area", "unitArea"}

    def _is_property_like(obj: Any) -> bool:
        if not isinstance(obj, dict):
            return False
        keys_lower = {k.lower() for k in obj}
        has_price = bool(keys_lower & {k.lower() for k in _PRICE_KEYS})
        has_size = bool(keys_lower & {k.lower() for k in _SIZE_KEYS})
        # Nawy units always have id + slug
        has_id = "id" in obj and "slug" in obj
        return (has_price or has_size) and has_id

    # Primary: availablePropertyTypes[*].properties (compound detail page)
    page_props = (data.get("props") or {}).get("pageProps") or {}
    apt = page_props.get("availablePropertyTypes")
    if isinstance(apt, list) and apt:
        units = []
        for group in apt:
            if isinstance(group, dict):
                units.extend(group.get("properties", []))
        if units and _is_property_like(units[0]):
            return units

    def _search(node: Any, depth: int) -> list[dict] | None:
        if depth <= 0:
            return None
        if isinstance(node, list):
            if node and all(_is_property_like(item) for item in node[:3]):
                return [item for item in node if isinstance(item, dict)]
            if len(node) <= 20:
                for item in node:
                    if isinstance(item, dict):
                        candidate = _search(item, depth - 1)
                        if candidate:
                            return candidate
        if isinstance(node, dict):
            for key in ("units", "compounds", "properties", "listings", "results", "data"):
                if key in node:
                    candidate = _search(node[key], depth - 1)
                    if candidate:
                        return candidate
            for val in node.values():
                candidate = _search(val, depth - 1)
                if candidate:
                    return candidate
        return None

    result = _search(data, max_depth)
    return result if result is not None else []


def _flatten_compound_as_unit(raw: dict, source_url: str) -> dict:
    return {**raw, "_source_url": source_url, "_is_compound_level": True}


# ─────────────────────────────────────────────────────────────────────────────
# Public Batch Normalizer — drop-in replacement for llm_normalizer
# ─────────────────────────────────────────────────────────────────────────────

MAX_UNITS_PER_COMPOUND = int(__import__("os").getenv("MAX_UNITS_PER_COMPOUND", "500"))


async def normalize_properties(raw_compound_json: dict) -> NormalizationResult:
    """
    Batch normalizer for one compound's raw scraped JSON.
    Drop-in replacement for llm_normalizer.normalize_properties.
    Zero tokens. Synchronous underneath — async signature for API compatibility.
    """
    result = NormalizationResult()
    source_url = raw_compound_json.get("_meta", {}).get("source_url", "unknown")

    units = _find_units_in_json(raw_compound_json)

    if not units:
        logger.warning("[normalizer] No unit array found for %s — trying compound-level", source_url)
        units = [_flatten_compound_as_unit(raw_compound_json, source_url)]

    # Inject compound-level context (set by scraper before calling this)
    page_props = (raw_compound_json.get("props") or {}).get("pageProps") or {}
    compound_data = page_props.get("compound") or {}
    compound_context: dict = {}
    if compound_data.get("name"):
        compound_context["_compound_name"] = compound_data["name"]
    if compound_data.get("slug"):
        compound_context["_compound_slug"] = compound_data["slug"]
    if compound_data.get("developerName"):
        compound_context["_developer_name"] = compound_data["developerName"]
    if compound_data.get("areaName"):
        compound_context["_area_name"] = compound_data["areaName"]
    payment_plans = compound_data.get("paymentPlans") or []
    if payment_plans:
        min_dp = min((p.get("downPaymentPercentage") or 100) for p in payment_plans)
        if min_dp < 100:
            compound_context["_down_payment_percentage"] = min_dp
    if compound_context:
        for unit in units:
            if isinstance(unit, dict):
                # Only set if not already present in unit
                for k, v in compound_context.items():
                    if k not in unit:
                        unit[k] = v

    if len(units) > MAX_UNITS_PER_COMPOUND:
        logger.info("[normalizer] Capping %d → %d units for %s", len(units), MAX_UNITS_PER_COMPOUND, source_url)
        units = units[:MAX_UNITS_PER_COMPOUND]

    logger.info("[normalizer] Normalizing %d units for %s (0 tokens)", len(units), source_url)

    for i, unit in enumerate(units):
        try:
            normalized = _deterministic_normalize(unit)
            result.properties.append(normalized)
        except Exception as exc:
            msg = f"Unit {i + 1} at {source_url}: {exc}"
            logger.error("[normalizer] Failed — %s", msg)
            result.skipped_count += 1
            result.errors.append(msg)

    logger.info("[normalizer] Done %s — normalized=%d skipped=%d", source_url, len(result.properties), result.skipped_count)
    return result


def normalize_unit_list(units: list[dict], source_url: str = "direct") -> NormalizationResult:
    """
    Normalize a flat list of unit dicts directly (no NEXT_DATA wrapper).
    Used by the v3 scraper for Nawy Now pagination results.
    """
    result = NormalizationResult()
    for i, unit in enumerate(units):
        try:
            normalized = _deterministic_normalize(unit)
            result.properties.append(normalized)
        except Exception as exc:
            msg = f"Unit {i + 1} at {source_url}: {exc}"
            logger.error("[normalizer] Failed — %s", msg)
            result.skipped_count += 1
            result.errors.append(msg)
    return result
