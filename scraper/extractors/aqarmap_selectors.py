"""
Aqarmap.com.eg extraction via Scrapling.

Aqarmap is a classifieds-style listing site. Two page types:
  - Listing-index page: paginated cards linking to detail pages
  - Listing-detail page: full property attributes

Both return dicts shaped for app.ingestion.deterministic_normalizer's
_deterministic_normalize() (uses the same loose field-name matcher as Nawy).
"""
from __future__ import annotations

import hashlib
import logging
import re
from typing import Optional

from settings import SELECTORS_DIR

logger = logging.getLogger(__name__)

try:
    from scrapling.parser import Adaptor
    _SCRAPLING_OK = True
except ImportError:
    Adaptor = None  # type: ignore
    _SCRAPLING_OK = False
    logger.warning("Scrapling not importable — aqarmap_selectors will return empty results")


def _build_adaptor(html: str, url: str):
    if not _SCRAPLING_OK:
        return None
    return Adaptor(
        body=html,
        url=url,
        auto_match=True,
        storage_file=str(SELECTORS_DIR / "aqarmap.db"),
    )


def extract_listing_links(html: str, url: str) -> list[str]:
    """Returns absolute URLs of detail pages found on a listing-index page."""
    adaptor = _build_adaptor(html, url)
    if adaptor is None:
        return []

    anchors = adaptor.css(
        "a[href*='/listing/'], a[class*='ListingCard'], a[data-testid*='listing-card']",
        auto_save=True,
    )

    seen: set[str] = set()
    out: list[str] = []
    for a in anchors:
        href = a.attrib.get("href") if hasattr(a, "attrib") else a.css_first("::attr(href)")
        if not href:
            continue
        if href.startswith("/"):
            href = f"https://aqarmap.com.eg{href}"
        if "/listing/" not in href:
            continue
        if href in seen:
            continue
        seen.add(href)
        out.append(href)
    return out


def extract_detail_page(html: str, url: str) -> Optional[dict]:
    """
    Returns a dict matching the normalizer's expected shape, or None if
    the page is too sparse to be a real listing.
    """
    adaptor = _build_adaptor(html, url)
    if adaptor is None:
        return None

    title = _first_text(adaptor, [
        "h1",
        "[data-testid='listing-title']",
        "[class*='ListingTitle']",
        "[class*='listing-title']",
    ])
    price_text = _first_text(adaptor, [
        "[data-testid='listing-price']",
        "[class*='Price']",
        "[class*='price']",
    ])
    area_text = _first_attr_value(adaptor, "area") or _first_attr_value(adaptor, "size")
    bedrooms = _first_attr_value(adaptor, "bedroom") or _first_attr_value(adaptor, "bed")
    bathrooms = _first_attr_value(adaptor, "bathroom") or _first_attr_value(adaptor, "bath")
    finishing = _first_attr_value(adaptor, "finish") or _first_attr_value(adaptor, "تشطيب")
    location = _first_text(adaptor, [
        "[data-testid='listing-location']",
        "[class*='Location']",
        "[class*='breadcrumb']",
    ])
    developer = _first_text(adaptor, [
        "[data-testid='developer']",
        "[class*='Developer']",
    ])
    compound = _first_text(adaptor, [
        "[data-testid='compound']",
        "[class*='Compound']",
        "[class*='project-name']",
    ])
    image = _first_attr(adaptor, [
        "img[class*='Hero']",
        "img[class*='hero']",
        "[class*='Gallery'] img",
    ], "src")

    if not title or not price_text:
        return None

    price = _parse_price(price_text)
    if price <= 0:
        return None

    # Construct a stable id from the URL so re-scrapes hit the same upsert row.
    listing_id = _stable_id(url)

    return {
        # Fields the deterministic_normalizer recognizes
        "id": listing_id,
        "title": title.strip(),
        "price": price,
        "min_unit_area": _parse_int(area_text),
        "number_of_bedrooms": _parse_int(bedrooms),
        "number_of_bathrooms": _parse_int(bathrooms),
        "finishing": finishing.lower() if finishing else None,
        "areaName": location,
        "developerName": developer,
        "compoundName": compound,
        "imageUrl": image,
        # nawy_url is the unique upsert key — column is misnamed historically.
        "nawy_url": url,
        # Signal source so downstream can distinguish
        "saleType": "Resale",
        "_source": "aqarmap",
    }


# ── helpers ─────────────────────────────────────────────────────────────────

_NUM_RE = re.compile(r"[\d,]+(?:\.\d+)?")


def _first_text(adaptor, selectors: list[str]) -> Optional[str]:
    for sel in selectors:
        try:
            el = adaptor.css_first(sel, auto_save=True)
        except Exception:
            el = None
        if el:
            txt = el.text
            if txt and txt.strip():
                return txt.strip()
    return None


def _first_attr(adaptor, selectors: list[str], attr: str) -> Optional[str]:
    for sel in selectors:
        try:
            el = adaptor.css_first(sel, auto_save=True)
        except Exception:
            el = None
        if el and hasattr(el, "attrib") and attr in el.attrib:
            return el.attrib[attr]
    return None


def _first_attr_value(adaptor, keyword: str) -> Optional[str]:
    """
    Aqarmap renders attribute pairs like `<dt>Area</dt><dd>180 sqm</dd>` or
    `<span class='label'>Bedrooms</span><span class='value'>3</span>`.
    This walks definition lists and finds the value next to a label matching `keyword`.
    """
    selectors = [
        f"dt:contains('{keyword}') + dd",
        f"[class*='label']:contains('{keyword}') + [class*='value']",
        f"li:contains('{keyword}')",
    ]
    for sel in selectors:
        try:
            el = adaptor.css_first(sel, auto_save=True)
        except Exception:
            el = None
        if el and el.text:
            return el.text.strip()
    return None


def _parse_price(s: Optional[str]) -> float:
    if not s:
        return 0.0
    cleaned = s.replace(",", "").replace("EGP", "").replace("ج.م", "").strip()
    m = _NUM_RE.search(cleaned)
    return float(m.group()) if m else 0.0


def _parse_int(s: Optional[str]) -> int:
    if not s:
        return 0
    cleaned = s.replace(",", "")
    m = _NUM_RE.search(cleaned)
    return int(float(m.group())) if m else 0


def _stable_id(url: str) -> str:
    return "aqarmap-" + hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
