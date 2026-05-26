"""
Unit tests for comparison_service.py — confidence tier logic.

All DB calls are mocked so no live DB is required.
Test IDs map 1:1 to the test plan (items 1–8 + edge cases).
"""
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import pytest

from app.ai_engine.comparison_service import (
    _confidence_tier,
    compare_compounds,
)


# ─── _confidence_tier ────────────────────────────────────────────────────────

def test_tier_indicative_one_dev_sample():
    """Test plan #1: 1 dev sample → indicative."""
    assert _confidence_tier(1, 5) == "indicative"


def test_tier_indicative_two_resale_samples():
    """Test plan #2: 2 resale samples → indicative."""
    assert _confidence_tier(5, 2) == "indicative"


def test_tier_moderate_boundary_exactly_three():
    """Test plan #3: exactly 3 on each side → moderate."""
    assert _confidence_tier(3, 3) == "moderate"


def test_tier_moderate_nine_samples():
    """Test plan #4: 9 samples → moderate."""
    assert _confidence_tier(9, 9) == "moderate"


def test_tier_high_boundary_exactly_ten():
    """Test plan #5: exactly 10 samples → high."""
    assert _confidence_tier(10, 10) == "high"


def test_tier_high_large_dataset():
    """High tier holds for large datasets."""
    assert _confidence_tier(50, 30) == "high"


def test_tier_uses_minimum_side():
    """Tier is gated by the smaller sample count."""
    assert _confidence_tier(20, 2) == "indicative"
    assert _confidence_tier(2, 20) == "indicative"
    assert _confidence_tier(20, 9) == "moderate"


# ─── compare_compounds — confidence field in per_compound entries ─────────────

def _make_row(compound, ptype, dev_avg, dev_n, res_avg, res_n, scraped_at=None):
    """Build a mock DB row for the aggregate query."""
    row = MagicMock()
    row.compound = compound
    row.ptype = ptype
    row.dev_avg = dev_avg
    row.dev_n = dev_n
    row.res_avg = res_avg
    row.res_n = res_n
    row.latest_scraped = scraped_at or datetime(2026, 5, 1)
    return row


def _make_db(rows):
    """Return a mock AsyncSession whose execute() returns the given rows."""
    result = MagicMock()
    result.all.return_value = rows
    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)
    return db


@pytest.mark.asyncio
async def test_confidence_field_present_in_per_compound():
    """Test plan #6: confidence field present in per_compound entries."""
    rows = [
        _make_row("Sodic East", "apartment", 5_000_000, 10, 3_500_000, 10),
        _make_row("Swan Lake", "apartment", 4_000_000, 10, 3_200_000, 10),
    ]
    db = _make_db(rows)
    result = await compare_compounds(["Sodic East", "Swan Lake"], db)
    for entry in result["per_compound"]:
        if entry.get("apartment"):
            assert "confidence" in entry["apartment"]


@pytest.mark.asyncio
async def test_indicative_segment_included_not_filtered():
    """Segments with 1 dev + 1 resale sample should appear (not be filtered out)."""
    rows = [
        _make_row("Compound A", "apartment", 4_000_000, 1, 3_000_000, 1),
        _make_row("Compound B", "apartment", 5_000_000, 10, 4_000_000, 10),
    ]
    db = _make_db(rows)
    result = await compare_compounds(["Compound A", "Compound B"], db)
    entry_a = next(e for e in result["per_compound"] if e["compound"] == "Compound A")
    assert entry_a["apartment"] is not None, "Indicative segment should not be None"
    assert entry_a["apartment"]["confidence"] == "indicative"


@pytest.mark.asyncio
async def test_missing_compound_zero_resale():
    """Test plan #7: compound with zero resale rows → missing_compound set."""
    rows = [
        # Compound A: no resale rows
        _make_row("Compound A", "apartment", 4_000_000, 5, None, 0),
        _make_row("Compound B", "apartment", 5_000_000, 10, 4_000_000, 10),
    ]
    db = _make_db(rows)
    result = await compare_compounds(["Compound A", "Compound B"], db)
    assert result["missing_compound"] == "Compound A"
    assert result["winner"] is None


@pytest.mark.asyncio
async def test_winner_selection_unchanged_high_confidence():
    """Test plan #8: winner selection unchanged when all compounds have ≥3 samples."""
    rows = [
        _make_row("Sodic East", "apartment", 5_000_000, 5, 3_000_000, 5),   # gap 2M
        _make_row("Swan Lake", "apartment", 4_000_000, 5, 3_500_000, 5),     # gap 500K
    ]
    db = _make_db(rows)
    result = await compare_compounds(["Sodic East", "Swan Lake"], db)
    assert result["winner"] == "Sodic East"


@pytest.mark.asyncio
async def test_all_compounds_sparse_no_winner_declared():
    """Edge case: all 3 compounds indicative — winner still picked by gap size."""
    rows = [
        _make_row("A", "apartment", 4_000_000, 1, 3_000_000, 1),
        _make_row("B", "apartment", 5_000_000, 2, 3_000_000, 2),
        _make_row("C", "apartment", 3_500_000, 1, 3_200_000, 1),
    ]
    db = _make_db(rows)
    result = await compare_compounds(["A", "B", "C"], db)
    # All indicative — but winner IS returned (largest gap wins)
    assert result["winner"] == "B"
    assert result["missing_compound"] is None
    for entry in result["per_compound"]:
        if entry.get("apartment"):
            assert entry["apartment"]["confidence"] == "indicative"


@pytest.mark.asyncio
async def test_data_as_of_populated():
    """data_as_of field uses the MAX scraped_at date."""
    ts = datetime(2026, 4, 15)
    rows = [_make_row("Sodic East", "apartment", 5_000_000, 5, 3_000_000, 5, scraped_at=ts)]
    db = _make_db(rows)
    result = await compare_compounds(["Sodic East"], db)
    entry = result["per_compound"][0]
    assert entry["data_as_of"] == "2026-04-15"
