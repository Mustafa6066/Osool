"""
Nawy.com extraction via Scrapling.

Nawy is a Next.js site — the canonical strategy is to parse the embedded
__NEXT_DATA__ JSON blob from each compound page rather than scrape DOM
elements directly. Falls back to DOM scraping (with Scrapling's adaptive
selectors) only when __NEXT_DATA__ is missing or malformed.

Output dicts are shaped to match the field names the deterministic
normalizer in app.ingestion.deterministic_normalizer already understands.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Optional

from settings import SELECTORS_DIR

logger = logging.getLogger(__name__)

try:
    from scrapling.parser import Adaptor
    _SCRAPLING_OK = True
except ImportError:  # only happens outside the Docker image
    Adaptor = None  # type: ignore
    _SCRAPLING_OK = False
    logger.warning("Scrapling not importable — nawy_selectors will return empty results")

_NEXT_DATA_RE = re.compile(
    r'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>',
    re.DOTALL,
)


def _parse_next_data(html: str) -> Optional[dict]:
    m = _NEXT_DATA_RE.search(html)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError as exc:
        logger.warning("Nawy __NEXT_DATA__ JSON decode failed: %s", exc)
        return None


def _build_adaptor(html: str, url: str):
    if not _SCRAPLING_OK:
        return None
    return Adaptor(
        body=html,
        url=url,
        auto_match=True,
        storage_file=str(SELECTORS_DIR / "nawy.db"),
    )


def extract_compound_page(html: str, url: str) -> dict:
    """
    Returns the raw __NEXT_DATA__ dict suitable for
    deterministic_normalizer.normalize_properties().

    Falls back to a minimal DOM scrape if __NEXT_DATA__ is missing.
    """
    next_data = _parse_next_data(html)
    if next_data:
        next_data.setdefault("_meta", {})["source_url"] = url
        return next_data

    logger.warning("[nawy] __NEXT_DATA__ not found at %s — falling back to DOM", url)
    return {"_meta": {"source_url": url}, "_dom_units": _extract_units_from_dom(html, url)}


def _extract_units_from_dom(html: str, url: str) -> list[dict]:
    """
    Last-resort DOM scrape using Scrapling. Used only when __NEXT_DATA__
    is absent. Selectors are text/attribute-anchored so they survive class
    renames; auto_match learns the mapping on first success.
    """
    adaptor = _build_adaptor(html, url)
    if adaptor is None:
        return []

    units: list[dict] = []
    cards = adaptor.css(
        "article, [data-testid*='property'], [class*='PropertyCard']",
        auto_save=True,
        adaptor_arguments={"auto_match": True},
    )
    for i, card in enumerate(cards):
        unit = _extract_card(card, url, i)
        if unit:
            units.append(unit)
    return units


def _extract_card(card, source_url: str, idx: int) -> Optional[dict]:
    """Pull the fields the normalizer cares about out of a single card."""
    try:
        title = _first_text(card, ["h2", "h3", "[class*='title']", "[class*='Title']"])
        price_text = _first_text(card, ["[class*='price']", "[class*='Price']", ".price"])
        location = _first_text(card, ["[class*='location']", "[class*='area']", "[class*='zone']"])
        area_text = _first_text(card, ["[class*='area-value']", "[class*='sqm']", "[class*='size']"])

        link = card.css_first("a::attr(href)")
        if link and not link.startswith("http"):
            link = f"https://www.nawy.com{link}"

        if not title or not price_text:
            return None

        return {
            "id": f"nawy-dom-{idx}",
            "title": title.strip(),
            "price": _parse_price(price_text),
            "min_unit_area": _parse_int(area_text),
            "areaName": location,
            "nawy_url": link or f"{source_url}#card-{idx}",
        }
    except Exception as exc:
        logger.debug("[nawy] card extract failed: %s", exc)
        return None


def _first_text(node, selectors: list[str]) -> Optional[str]:
    for sel in selectors:
        el = node.css_first(sel)
        if el:
            txt = el.text
            if txt and txt.strip():
                return txt.strip()
    return None


_NUM_RE = re.compile(r"[\d,]+")


def _parse_price(s: Optional[str]) -> float:
    if not s:
        return 0.0
    cleaned = s.replace(",", "").replace("EGP", "").strip()
    m = _NUM_RE.search(cleaned)
    return float(m.group()) if m else 0.0


def _parse_int(s: Optional[str]) -> int:
    if not s:
        return 0
    m = _NUM_RE.search(s.replace(",", ""))
    return int(m.group()) if m else 0
