"""
Tests for flagship_compounds.py — N+1 fix and resolve_to_compound behaviour.

Test plan items 13–15.
"""
from unittest.mock import AsyncMock, MagicMock, call

import pytest

from app.ai_engine.flagship_compounds import resolve_to_compound


def _make_db_with_stocked(stocked_compounds: list[str]):
    """
    Return a mock DB where execute() returns rows for the given compounds only.
    Each row has .compound and .cnt attributes.
    """
    rows = []
    for name in stocked_compounds:
        row = MagicMock()
        row.compound = name
        row.cnt = 10  # any value ≥ _MIN_ROWS_FOR_FLAGSHIP
        rows.append(row)

    result = MagicMock()
    result.all.return_value = rows

    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)
    return db


# ─── Test #13: Single DB round-trip ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_resolve_to_compound_single_db_query():
    """
    Test plan #13: developer with 4 compounds → single DB round-trip.
    db.execute should be called exactly once (no N+1 sequential queries).
    """
    db = _make_db_with_stocked(["Sodic East"])
    result = await resolve_to_compound("Sodic", db)
    assert result == "Sodic East"
    assert db.execute.call_count == 1, "Expected exactly one DB round-trip, got N+1"


# ─── Test #14: Developer with no stocked compounds → returns None ─────────────

@pytest.mark.asyncio
async def test_resolve_to_compound_no_stocked_returns_none():
    """
    Test plan #14: developer with no stocked compounds → returns None.
    """
    db = _make_db_with_stocked([])  # nothing stocked
    result = await resolve_to_compound("Sodic", db)
    assert result is None


# ─── Test #15: Unknown string → returns unchanged ────────────────────────────

@pytest.mark.asyncio
async def test_resolve_to_compound_unknown_string_unchanged():
    """
    Test plan #15: unknown string (compound name, not developer) →
    returns same string unchanged without hitting the DB.
    """
    db = AsyncMock()
    result = await resolve_to_compound("ZED East", db)
    assert result == "ZED East"
    # Should not have touched the DB — it's not a tracked developer.
    db.execute.assert_not_called()


# ─── Flagship order preserved ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_resolve_respects_flagship_order():
    """
    When multiple compounds are stocked, the first in the DEVELOPER_TO_COMPOUNDS
    list should be returned (flagship priority).
    """
    # Palm Hills: ["Palm Hills New Cairo", "Palm Hills Katameya", "Badya"]
    # Make all three stocked but in DB response order (not priority order).
    db = _make_db_with_stocked(["Badya", "Palm Hills New Cairo", "Palm Hills Katameya"])
    result = await resolve_to_compound("Palm Hills", db)
    assert result == "Palm Hills New Cairo"  # first in flagship list wins
