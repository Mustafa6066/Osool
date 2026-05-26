"""Contract test — aqarmap_selectors must pull the expected fields."""
from __future__ import annotations

from pathlib import Path

import pytest

from extractors.aqarmap_selectors import extract_detail_page, extract_listing_links

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_extract_listing_links_dedups_and_filters():
    html = (FIXTURE_DIR / "aqarmap_listing_index_minimal.html").read_text(encoding="utf-8")
    links = extract_listing_links(html, "https://aqarmap.com.eg/en/for-sale/")
    assert all("/listing/" in url for url in links), links
    assert all(url.startswith("https://aqarmap.com.eg") for url in links)
    # /en/login must be filtered out
    assert not any("/login" in url for url in links)


def test_extract_detail_page_required_fields():
    html = (FIXTURE_DIR / "aqarmap_detail_minimal.html").read_text(encoding="utf-8")
    detail = extract_detail_page(html, "https://aqarmap.com.eg/en/listing/123-apartment-madinaty")
    assert detail is not None
    assert detail["title"].startswith("3-bedroom")
    assert detail["price"] == 6_250_000
    assert detail["min_unit_area"] == 165
    assert detail["number_of_bedrooms"] == 3
    assert detail["number_of_bathrooms"] == 2
    assert detail["compoundName"] == "Madinaty"
    assert detail["nawy_url"].endswith("/123-apartment-madinaty")
    assert detail["_source"] == "aqarmap"


def test_extract_detail_page_rejects_pages_missing_price():
    html = "<html><body><h1>No price here</h1></body></html>"
    assert extract_detail_page(html, "https://aqarmap.com.eg/en/listing/x") is None
