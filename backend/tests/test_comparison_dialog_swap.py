"""
Tests for comparison_dialog.py — MISSING_DATA swap fix (CQ1).

Test plan items 9–12: ensures that when a compound triggers MISSING_DATA,
_handle_missing_data replaces the exact failing compound (not candidates[-1]).
"""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai_engine import comparison_dialog
from app.ai_engine.comparison_dialog import (
    STATE_AWAITING_NAMES,
    STATE_MISSING_DATA,
    handle_turn,
)


def _make_session(**kwargs):
    defaults = {
        "session_id": "test-session",
        "state": STATE_AWAITING_NAMES,
        "candidate_names": None,
        "mode": None,
        "property_type_filter": None,
        "comparison_used": False,
        "missing_compound": None,
        "has_shown_deal_cta": False,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _make_db():
    return AsyncMock()


# ─── Test #9: MISSING_DATA entered with correct missing_compound stored ───────

@pytest.mark.asyncio
async def test_missing_data_stores_missing_compound_name():
    """
    Test plan #9: 3-compound comparison; middle compound missing →
    MISSING_DATA entered AND session.missing_compound = middle compound name.
    """
    session = _make_session(
        state=STATE_AWAITING_NAMES,
        candidate_names=["Sodic East", "Swan Lake", "Mivida"],
    )

    compare_result = {
        "per_compound": [
            {"compound": "Sodic East", "apartment": {"gap_egp": 1_000_000, "dev_avg": 5e6, "res_avg": 4e6, "dev_n": 5, "res_n": 5, "confidence": "moderate"}, "villa": None, "max_gap_egp": 1_000_000, "data_as_of": None},
            {"compound": "Swan Lake", "apartment": None, "villa": None, "max_gap_egp": None, "data_as_of": None},
            {"compound": "Mivida", "apartment": {"gap_egp": 500_000, "dev_avg": 4e6, "res_avg": 3.5e6, "dev_n": 3, "res_n": 3, "confidence": "moderate"}, "villa": None, "max_gap_egp": 500_000, "data_as_of": None},
        ],
        "winner": None,
        "missing_compound": "Swan Lake",
    }

    similar = ["Palm Hills New Cairo", "Marassi", "Bloomfields"]

    with (
        patch("app.ai_engine.comparison_dialog.compare_compounds", return_value=compare_result),
        patch("app.ai_engine.comparison_dialog.similar_compounds", return_value=similar),
        patch("app.ai_engine.local_intent.local_intent_extractor.extract_entities",
              return_value=[("Sodic East", "compound"), ("Swan Lake", "compound"), ("Mivida", "compound")]),
        patch("app.ai_engine.local_intent.local_intent_extractor.is_comparison_intent", return_value=True),
    ):
        db = _make_db()
        await handle_turn("قارن سوديك إيست وسوان ليك وميفيدا", session, db)

    assert session.state == STATE_MISSING_DATA
    assert session.missing_compound == "Swan Lake"


# ─── Test #10: Replacement goes to the correct position ──────────────────────

@pytest.mark.asyncio
async def test_replacement_replaces_missing_not_last():
    """
    Test plan #10: user replaces compound; session.missing_compound compound is
    replaced, NOT the last candidate (which is what the old bug did).
    """
    # Middle compound (Swan Lake, index 1) was missing; Mivida (index 2) should survive.
    session = _make_session(
        state=STATE_MISSING_DATA,
        candidate_names=["Sodic East", "Swan Lake", "Mivida"],
        missing_compound="Swan Lake",
        mode="MULTI",
    )

    compare_result_ok = {
        "per_compound": [
            {"compound": "Sodic East", "apartment": {"gap_egp": 1_000_000, "dev_avg": 5e6, "res_avg": 4e6, "dev_n": 5, "res_n": 5, "confidence": "moderate"}, "villa": None, "max_gap_egp": 1_000_000, "data_as_of": None},
            {"compound": "Palm Hills New Cairo", "apartment": {"gap_egp": 200_000, "dev_avg": 4e6, "res_avg": 3.8e6, "dev_n": 4, "res_n": 4, "confidence": "moderate"}, "villa": None, "max_gap_egp": 200_000, "data_as_of": None},
            {"compound": "Mivida", "apartment": {"gap_egp": 500_000, "dev_avg": 4e6, "res_avg": 3.5e6, "dev_n": 3, "res_n": 3, "confidence": "moderate"}, "villa": None, "max_gap_egp": 500_000, "data_as_of": None},
        ],
        "winner": "Sodic East",
        "missing_compound": None,
    }

    captured_names = []

    async def _fake_compare(compound_names, db, **kwargs):
        captured_names.extend(compound_names)
        return compare_result_ok

    with (
        patch("app.ai_engine.comparison_dialog.compare_compounds", side_effect=_fake_compare),
        patch("app.ai_engine.local_intent.local_intent_extractor.extract_entities",
              return_value=[("Palm Hills New Cairo", "compound")]),
    ):
        db = _make_db()
        await handle_turn("بالم هيلز التجمع", session, db)

    # The replacement should have landed at index 1 (Swan Lake's slot).
    # Mivida should still be at index 2.
    assert "Palm Hills New Cairo" in captured_names
    assert "Mivida" in captured_names
    assert "Swan Lake" not in captured_names


# ─── Test #11: Replacement compound also missing → re-enter MISSING_DATA ──────

@pytest.mark.asyncio
async def test_replacement_also_missing_re_enters_missing_data():
    """
    Test plan #11: replacement compound also has zero resale →
    MISSING_DATA re-entered with new missing_compound.
    """
    session = _make_session(
        state=STATE_MISSING_DATA,
        candidate_names=["Sodic East", "Swan Lake", "Mivida"],
        missing_compound="Swan Lake",
        mode="MULTI",
    )

    compare_result_also_missing = {
        "per_compound": [
            {"compound": "Sodic East", "apartment": {"gap_egp": 1e6, "dev_avg": 5e6, "res_avg": 4e6, "dev_n": 5, "res_n": 5, "confidence": "moderate"}, "villa": None, "max_gap_egp": 1e6, "data_as_of": None},
            {"compound": "Palm Hills Katameya", "apartment": None, "villa": None, "max_gap_egp": None, "data_as_of": None},
            {"compound": "Mivida", "apartment": {"gap_egp": 5e5, "dev_avg": 4e6, "res_avg": 3.5e6, "dev_n": 3, "res_n": 3, "confidence": "moderate"}, "villa": None, "max_gap_egp": 5e5, "data_as_of": None},
        ],
        "winner": None,
        "missing_compound": "Palm Hills Katameya",
    }

    with (
        patch("app.ai_engine.comparison_dialog.compare_compounds", return_value=compare_result_also_missing),
        patch("app.ai_engine.comparison_dialog.similar_compounds", return_value=[]),
        patch("app.ai_engine.local_intent.local_intent_extractor.extract_entities",
              return_value=[("Palm Hills Katameya", "compound")]),
    ):
        db = _make_db()
        await handle_turn("بالم هيلز القطامية", session, db)

    assert session.state == STATE_MISSING_DATA
    assert session.missing_compound == "Palm Hills Katameya"


# ─── Test #12: No entity in MISSING_DATA → stay and re-prompt ────────────────

@pytest.mark.asyncio
async def test_no_entity_in_missing_data_stays_missing():
    """
    Test plan #12: MISSING_DATA with no entity in user reply →
    stays in MISSING_DATA state, re-prompts.
    """
    session = _make_session(
        state=STATE_MISSING_DATA,
        candidate_names=["Sodic East", "Swan Lake"],
        missing_compound="Swan Lake",
        mode="MULTI",
    )

    with patch("app.ai_engine.local_intent.local_intent_extractor.extract_entities", return_value=[]):
        db = _make_db()
        response = await handle_turn("مش عارف", session, db)

    assert session.state == STATE_MISSING_DATA
    assert response["type"] == "clarification"
