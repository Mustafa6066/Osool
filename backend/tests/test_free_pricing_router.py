"""
Tests for the zero-token free-path intent router.

Covers the three query shapes the screenshots exposed:
  * single entity / "developer price for X"      → best_price (unchanged)
  * 2-3 named developers/compounds               → compare
  * "price increase over N years"                → appreciation

Plus the ingestion split-derivation helper that keeps developer_price /
resale_price fresh on live scrapes.
"""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.ai_engine.free_pricing_router import (
    build_appreciation_payload,
    build_comparison_payload,
    classify_free_intent,
)
from app.ingestion.repository import _split_developer_resale


# ─── classification (pure) ──────────────────────────────────────────────────

def test_classify_single_entity_is_best_price():
    # Screenshot 1: one developer named, asking the developer price → best price.
    q = "سعر المطور او الشركه في ماونتن فيو في التجمع الخامس للشقه الغرفتين"
    assert classify_free_intent(q) == "best_price"


def test_classify_multi_developer_is_compare():
    # Screenshot 2: three developers named → cross-entity comparison.
    q = "سعر المطور في مشاريع ماونتن فيو و حسن علام سوديك في التجمع للشقه الغرفتين"
    assert classify_free_intent(q) == "compare"


def test_classify_appreciation_arabic():
    # Screenshot 3: "rate of Sodic price increase over last 5 years".
    q = "ما هو معدل زياده سعر سوديك آخر ٥ سنين"
    assert classify_free_intent(q) == "appreciation"


def test_classify_appreciation_english():
    assert (
        classify_free_intent("what is Sodic price appreciation over the last 5 years")
        == "appreciation"
    )


def test_classify_increase_without_anchor_is_not_appreciation():
    # "increase" with no price/time/entity anchor must not hijack the path.
    assert classify_free_intent("can you increase the limit please") == "best_price"


# ─── appreciation handler (pure — hardcoded market history) ──────────────────

def test_appreciation_sodic_growth_positive():
    payload = build_appreciation_payload("معدل زياده سعر سوديك آخر ٥ سنين", "ar")
    assert payload["response_type"] == "free_appreciation"
    pd = payload["primitive_data"]
    assert pd["cagr_pct"] > 0
    assert pd["total_growth_pct"] > 0
    assert pd["basis"] in ("developer", "compound_via_developer")
    assert pd["end_year"] == 2026
    assert "%" in payload["response"]
    # Full key set present for the streaming endpoint.
    for key in ("ui_actions", "suggestions", "lead_score", "readiness_score",
                "showing_strategy", "cta_actions", "detected_language"):
        assert key in payload


def test_appreciation_area_fallback_english():
    payload = build_appreciation_payload("price growth in New Cairo over 5 years", "en")
    pd = payload["primitive_data"]
    assert pd["basis"] in ("area", "developer")
    assert pd["end_year"] == 2026
    assert pd["total_growth_pct"] > 0


def test_appreciation_unresolved_subject_guides_user():
    payload = build_appreciation_payload("how much did prices grow", "en")
    assert payload["primitive_data"].get("reason") == "unresolved_subject"
    assert payload["response"]


def test_appreciation_respects_year_window():
    three = build_appreciation_payload("Sodic price growth over 3 years", "en")
    five = build_appreciation_payload("Sodic price growth over 5 years", "en")
    # A shorter window starts later → smaller total growth.
    assert three["primitive_data"]["start_year"] > five["primitive_data"]["start_year"]
    assert three["primitive_data"]["total_growth_pct"] < five["primitive_data"]["total_growth_pct"]


# ─── ingestion split derivation (pure) ──────────────────────────────────────

def test_split_developer():
    assert _split_developer_resale("Developer", 5_000_000) == (5_000_000.0, None)


def test_split_nawy_now_rolls_into_developer():
    assert _split_developer_resale("Nawy Now", 4_000_000) == (4_000_000.0, None)


def test_split_resale():
    assert _split_developer_resale("Resale", 3_000_000) == (None, 3_000_000.0)


def test_split_unknown_or_missing_price_is_none():
    assert _split_developer_resale("", 3_000_000) == (None, None)
    assert _split_developer_resale("Developer", None) == (None, None)


# ─── comparison handler (DB-mocked) ─────────────────────────────────────────

class _FakeResult:
    def __init__(self, row):
        self._row = row

    def first(self):
        return self._row


def _agg(dev_avg, dev_min, dev_n, res_avg, res_min, res_n):
    return SimpleNamespace(
        dev_avg=dev_avg, dev_min=dev_min, dev_n=dev_n,
        res_avg=res_avg, res_min=res_min, res_n=res_n,
    )


def test_comparison_picks_cheapest_developer_price():
    db = AsyncMock()
    # One aggregate row per entity, in extract_entities order: MV, Hassan Allam, Sodic.
    db.execute = AsyncMock(side_effect=[
        _FakeResult(_agg(13_800_000, 11_200_000, 20, 5_650_000, 5_650_000, 4)),   # Mountain View
        _FakeResult(_agg(15_000_000, 12_000_000, 10, None, None, 0)),             # Hassan Allam
        _FakeResult(_agg(19_300_000, 16_000_000, 8, 11_500_000, 11_500_000, 3)),  # Sodic
    ])
    q = "سعر المطور في مشاريع ماونتن فيو و حسن علام سوديك في التجمع للشقه الغرفتين"
    payload = asyncio.run(build_comparison_payload(db, q, "ar"))

    assert payload is not None
    assert payload["response_type"] == "free_comparison"
    # Cheapest average developer price wins.
    assert payload["primitive_data"]["winner"] == "Mountain View"
    assert len(payload["properties"]) == 3
    assert payload["properties"][0]["locked"] is False
    # The full comparison (all 3 entities) is surfaced in the structured action.
    assert len(payload["ui_actions"][0]["data"]["entities"]) == 3


def test_comparison_returns_none_for_single_entity():
    db = AsyncMock()
    payload = asyncio.run(build_comparison_payload(db, "best price in Sarai", "en"))
    assert payload is None


def test_comparison_insufficient_data_still_answers():
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        _FakeResult(_agg(None, None, 0, None, None, 0)),
        _FakeResult(_agg(None, None, 0, None, None, 0)),
    ])
    payload = asyncio.run(build_comparison_payload(db, "compare سراي و هايد بارك", "ar"))
    assert payload is not None
    assert payload["primitive_data"]["result"] == "insufficient_data"
    assert len(payload["properties"]) == 2
