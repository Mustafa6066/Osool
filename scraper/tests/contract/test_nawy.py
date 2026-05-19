"""Contract test — nawy_selectors must extract __NEXT_DATA__ correctly."""
from __future__ import annotations

from pathlib import Path

import pytest

from extractors.nawy_selectors import extract_compound_page

FIXTURE = Path(__file__).parent / "fixtures" / "nawy_compound_minimal.html"


def test_extract_compound_page_returns_next_data():
    html = FIXTURE.read_text(encoding="utf-8")
    envelope = extract_compound_page(html, "https://www.nawy.com/compound/test")

    page_props = envelope["props"]["pageProps"]
    assert page_props["compound"]["slug"] == "mountain-view-icity"

    units = page_props["availablePropertyTypes"][0]["properties"]
    assert len(units) == 1
    unit = units[0]

    assert unit["id"] == 12345
    assert unit["min_price"] == 9_500_000
    assert unit["min_unit_area"] == 180
    assert unit["number_of_bedrooms"] == 3
    assert unit["finishing"] == "semi_finished"


def test_extract_compound_page_missing_next_data_falls_back():
    envelope = extract_compound_page(
        "<html><body><p>no script</p></body></html>",
        "https://www.nawy.com/compound/broken",
    )
    # When __NEXT_DATA__ is missing we still return a dict the adapter can handle.
    assert envelope["_meta"]["source_url"].endswith("/broken")
    assert "_dom_units" in envelope
