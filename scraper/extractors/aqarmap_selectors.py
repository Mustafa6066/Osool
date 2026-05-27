"""
Aqarmap.com.eg extraction.

Strategy (rebuilt 2026-05-27):
  - Detail pages embed full `schema.org RealEstateListing` JSON-LD with price,
    address, geo, amenities, and the property type as the `@type`. We parse
    that as the primary path — it's a contract, not a CSS class.
  - Listing-index pages render `<article class="listing-card ...">` with
    nested `a[href*='/listing/']` anchors. Pure regex/string extraction is
    sufficient and survives Tailwind class churn.
  - Payment plan + delivery date aren't in JSON-LD on Aqarmap (it's a
    classifieds site — mostly resale). We surface a `description` block
    containing the seller's free-text so the downstream LLM/normalizer can
    still pull "down payment", "installments", etc. when they're stated.

Both shapes match the field names `app.ingestion.deterministic_normalizer`
already understands.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


# ── Index page: detail-URL extraction ───────────────────────────────────────

_LISTING_HREF_RE = re.compile(
    r'href="(/en/listing/(?:\d+)-[^"]+)"',
    re.IGNORECASE,
)


def extract_listing_links(html: str, url: str) -> list[str]:
    """
    Returns absolute URLs of detail pages found on a listing-index page.

    Uses regex against the raw HTML — Scrapling/Adaptor isn't needed for this
    pattern and the regex survives most class-name changes.
    """
    seen: set[str] = set()
    out: list[str] = []
    for m in _LISTING_HREF_RE.finditer(html or ""):
        path = m.group(1)
        absolute = f"https://aqarmap.com.eg{path}"
        if absolute in seen:
            continue
        seen.add(absolute)
        out.append(absolute)
    return out


# ── Detail page: JSON-LD extraction ─────────────────────────────────────────

_JSONLD_RE = re.compile(
    r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)

_PROPERTY_TYPES = {
    "apartment": "Apartment",
    "house": "Apartment",
    "singlefamilyresidence": "Villa",
    "singleresidence": "Villa",
    "villa": "Villa",
    "townhouse": "Townhouse",
    "twinhouse": "Twin House",
    "duplex": "Duplex",
    "penthouse": "Penthouse",
    "studio": "Studio",
    "chalet": "Chalet",
    "office": "Office",
    "retail": "Retail",
    "shop": "Retail",
    "store": "Retail",
}


def _collect_jsonld(html: str) -> list[dict]:
    """Return every parsed JSON-LD block from the page."""
    blocks: list[dict] = []
    for m in _JSONLD_RE.finditer(html or ""):
        raw = m.group(1).strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            blocks.append(obj)
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, dict):
                    blocks.append(item)
    return blocks


def _find_real_estate_listing(blocks: list[dict]) -> Optional[dict]:
    """Flatten through @graph and find the RealEstateListing entry."""
    for blk in blocks:
        # Direct hit
        if blk.get("@type") == "RealEstateListing":
            return blk
        # Inside @graph
        graph = blk.get("@graph")
        if isinstance(graph, list):
            for node in graph:
                if isinstance(node, dict) and node.get("@type") == "RealEstateListing":
                    return node
    return None


def _normalize_property_type(item_offered: dict) -> Optional[str]:
    raw = item_offered.get("@type") or ""
    key = str(raw).lower().replace(" ", "")
    return _PROPERTY_TYPES.get(key)


_NUM_RE = re.compile(r"[\d,]+(?:\.\d+)?")


def _parse_int(s) -> int:
    if s is None:
        return 0
    if isinstance(s, (int, float)):
        return int(s)
    m = _NUM_RE.search(str(s).replace(",", ""))
    return int(float(m.group())) if m else 0


def _parse_float(s) -> float:
    if s is None:
        return 0.0
    if isinstance(s, (int, float)):
        return float(s)
    m = _NUM_RE.search(str(s).replace(",", ""))
    return float(m.group()) if m else 0.0


# ── Optional free-text mining for payment plan / delivery ──────────────────

_DOWN_PAYMENT_RE = re.compile(
    r"(?:down\s*payment|مقدم|downpayment)[^0-9]{0,30}(\d{1,3})\s*%",
    re.IGNORECASE,
)
_INSTALLMENT_YEARS_RE = re.compile(
    r"(\d{1,2})\s*(?:years|year|سنه|سنة|سنين|yrs)",
    re.IGNORECASE,
)
_DELIVERY_YEAR_RE = re.compile(
    r"(?:delivery|delivered|handover|ready|تسليم)[^0-9]{0,30}(20\d{2})",
    re.IGNORECASE,
)
_DELIVERY_QUARTER_RE = re.compile(
    r"(?:delivery|handover|ready|تسليم)[^A-Za-z0-9]{0,20}(Q[1-4])[^0-9]{0,5}(20\d{2})",
    re.IGNORECASE,
)
_DESCRIPTION_RE = re.compile(
    r'<meta\s+name="description"\s+content="([^"]+)"',
    re.IGNORECASE,
)


def _mine_free_text(html: str) -> dict:
    """
    Aqarmap doesn't put payment-plan / delivery date in JSON-LD. Pick them
    out of the page description meta + body text when the seller stated them.
    Conservative — only returns fields when a pattern matched cleanly.
    """
    out: dict = {}

    desc_match = _DESCRIPTION_RE.search(html or "")
    description = desc_match.group(1) if desc_match else ""
    haystack = description + "\n" + (html or "")[:60000]  # cap to keep regex cheap

    dp = _DOWN_PAYMENT_RE.search(haystack)
    if dp:
        pct = int(dp.group(1))
        if 1 <= pct <= 90:
            out["downPaymentPercentage"] = pct

    iy = _INSTALLMENT_YEARS_RE.search(haystack)
    if iy:
        yrs = int(iy.group(1))
        if 1 <= yrs <= 20:
            out["installmentYears"] = yrs

    dq = _DELIVERY_QUARTER_RE.search(haystack)
    if dq:
        out["deliveryDate"] = f"{dq.group(1).upper()} {dq.group(2)}"
    else:
        dy = _DELIVERY_YEAR_RE.search(haystack)
        if dy:
            out["deliveryDate"] = dy.group(1)

    if description:
        out["description"] = description[:2000]
    return out


# ── Public entrypoint ───────────────────────────────────────────────────────

def extract_detail_page(html: str, url: str) -> Optional[dict]:
    """
    Returns a unit-dict matching the deterministic_normalizer's expected
    shape, or None when the page isn't recognizable as a listing.
    """
    blocks = _collect_jsonld(html)
    listing = _find_real_estate_listing(blocks)
    if not listing:
        return None

    offers = listing.get("offers") or {}
    item_offered = listing.get("itemOffered") or {}

    price = _parse_float(offers.get("price"))
    if price <= 0:
        return None

    floor_size = item_offered.get("floorSize") or {}
    size_sqm = _parse_int(floor_size.get("value"))

    address = item_offered.get("address") or {}
    geo = item_offered.get("geo") or {}

    # Aqarmap puts compound name in addressLocality and street address.
    compound_name = address.get("addressLocality") or address.get("addressRegion")
    # Construct location text: addressRegion is usually compound, streetAddress
    # carries area context. Prefer the broadest region matched in the breadcrumb.
    location_raw = address.get("addressRegion") or address.get("addressLocality") or ""
    # Strip trailing " Compound" / similar for cleaner zone matching downstream.
    location_clean = re.sub(r"\s+compound\b.*$", "", str(location_raw), flags=re.IGNORECASE).strip()

    images = listing.get("image") or []
    if isinstance(images, str):
        images = [images]
    first_image = images[0] if images else None

    free_text = _mine_free_text(html)

    listing_id = _stable_id(url)
    nawy_url = listing.get("url") or url

    # The deterministic_normalizer matches via _TYPE_MAP entries; both
    # 'Apartment', 'Villa', etc. are accepted. We pre-resolve so the
    # normalizer's _normalize_type sees a canonical string.
    prop_type = _normalize_property_type(item_offered)

    return {
        # Fields the deterministic_normalizer recognizes
        "id": listing_id,
        "title": listing.get("name") or item_offered.get("name") or "",
        "price": price,
        "min_unit_area": size_sqm,
        "number_of_bedrooms": _parse_int(item_offered.get("numberOfRooms")),
        "number_of_bathrooms": _parse_int(item_offered.get("numberOfBathroomsTotal")),
        "finishing": None,  # not in JSON-LD; left for description-mining downstream
        "areaName": location_clean,
        "developerName": None,  # aqarmap = classifieds, sellers are individuals
        "compoundName": compound_name,
        # Flat-string aliases for the input validator in
        # app/ingestion/scraper_schemas.py — it doesn't read the camelCase
        # variants and would reject every row on the
        # "at_least_location_or_compound" rule otherwise.
        "location": location_clean or None,
        "compound": compound_name or None,
        "developer": None,
        "area": float(size_sqm) if size_sqm else None,  # validator expects sqm as float
        "type": (prop_type or "Other"),
        "bedrooms": _parse_int(item_offered.get("numberOfRooms")) or None,
        "bathrooms": _parse_int(item_offered.get("numberOfBathroomsTotal")) or None,
        "imageUrl": first_image,
        "propertyType": prop_type or "Other",
        # nawy_url is the unique upsert key — column is misnamed historically.
        "nawy_url": nawy_url,
        # Signal source so downstream can distinguish.
        "saleType": "Resale",
        "_source": "aqarmap",
        # Optional payment-plan/delivery fields, only set when found.
        "downPaymentPercentage": free_text.get("downPaymentPercentage"),
        "installmentYears": free_text.get("installmentYears"),
        "deliveryDate": free_text.get("deliveryDate"),
        "description": free_text.get("description"),
        # Geo for map overlays — normalizer ignores extra fields.
        "latitude": geo.get("latitude"),
        "longitude": geo.get("longitude"),
    }


def _stable_id(url: str) -> str:
    return "aqarmap-" + hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
