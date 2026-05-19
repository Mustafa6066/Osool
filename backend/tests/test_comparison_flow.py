"""
Tests for the free-path compound comparison funnel.

Three layers:
- Intent extraction (extract_entities, is_comparison_intent) — pure.
- Comparison service (compare_compounds, best_deals_in_compound) — DB-mocked.
- Comparison dialog state machine — drives sessions through realistic turns.

The router-level "no session_id → upsell" guard and the comparison_used
re-entry are also exercised here since they sit one call above the dialog.
"""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ai_engine import comparison_dialog
from app.ai_engine.comparison_service import (
    best_deals_in_compound,
    compare_compounds,
)
from app.ai_engine.flagship_compounds import (
    DEVELOPER_TO_COMPOUNDS,
    resolve_to_compound,
)
from app.ai_engine.local_intent import local_intent_extractor
from app.ai_engine.local_router import local_router
from app.models import FreePathSession


# ─── Intent extraction ──────────────────────────────────────────────────────


def test_extract_entities_parses_three_developers_arabic():
    """User's canonical example: 'best price between Lavista, Hassan Allam, Sodic'."""
    result = local_intent_extractor.extract_entities(
        "احسن سعر بين لافيستا و حسن علام و سوديك"
    )
    names = [n for n, _ in result]
    kinds = [k for _, k in result]
    assert names == ["La Vista", "Hassan Allam", "Sodic"]
    assert kinds == ["developer", "developer", "developer"]


def test_extract_entities_normalizes_arabic_spelling_variants():
    """'لا فيستا' (with space) and 'لافيستا' (no space) should both resolve."""
    spaced = local_intent_extractor.extract_entities("اريد لا فيستا")
    joined = local_intent_extractor.extract_entities("اريد لافيستا")
    assert spaced and joined
    assert spaced[0][0] == joined[0][0] == "La Vista"


def test_extract_entities_dedups_and_preserves_order():
    """Naming Sodic twice (or via two aliases) should yield one entry, first-occurrence ordered."""
    result = local_intent_extractor.extract_entities(
        "compare hyde park, sodic and sodic east"
    )
    names = [n for n, _ in result]
    # "Sodic" developer comes before "Sodic East" in the source string, so Sodic
    # is recorded first; "Sodic East" is a distinct canonical name so both appear.
    assert "Hyde Park" in names
    assert "Sodic" in names
    assert "Sodic East" in names
    assert len(names) == len(set(names))


def test_extract_entities_returns_empty_when_no_match():
    """A generic Arabic ask with no compound/developer names yields nothing."""
    result = local_intent_extractor.extract_entities(
        "ممكن تقولي ايه احسن سعر في كمبوندات التجمع"
    )
    assert result == []


def test_is_comparison_intent_triggers_on_best_price_phrase():
    assert local_intent_extractor.is_comparison_intent("احسن سعر بين كذا و كذا")
    assert local_intent_extractor.is_comparison_intent("best price between X and Y")


def test_is_comparison_intent_triggers_when_two_entities_named():
    """No comparison verb needed — naming 2+ entities is enough signal."""
    assert local_intent_extractor.is_comparison_intent("سراي و هايد بارك")


def test_is_comparison_intent_false_for_unrelated_query():
    """ROI question with no entities should not trigger comparison."""
    assert not local_intent_extractor.is_comparison_intent("عايز اعرف ROI")


# ─── Flagship resolution ────────────────────────────────────────────────────


def _mock_db_with_count(count: int) -> AsyncMock:
    """Build an AsyncSession mock whose `execute` returns the given scalar count."""
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one.return_value = count
    db.execute.return_value = result
    return db


def test_resolve_to_compound_picks_first_stocked():
    """The first compound in DEVELOPER_TO_COMPOUNDS with ≥5 rows wins."""
    db = _mock_db_with_count(10)  # every compound queried looks stocked
    resolved = asyncio.run(resolve_to_compound("La Vista", db))
    assert resolved == DEVELOPER_TO_COMPOUNDS["La Vista"][0]


def test_resolve_to_compound_returns_compound_as_is_when_unknown():
    """An unknown name (e.g., a direct compound name) passes through unchanged."""
    db = _mock_db_with_count(0)
    resolved = asyncio.run(resolve_to_compound("Sarai", db))
    assert resolved == "Sarai"


def test_resolve_to_compound_returns_none_when_no_flagship_stocked():
    """All known compounds for the developer have <5 rows → None."""
    db = _mock_db_with_count(0)
    resolved = asyncio.run(resolve_to_compound("La Vista", db))
    assert resolved is None


# ─── Comparison service (compare_compounds) ─────────────────────────────────


def _stub_grouped_rows(rows: list[tuple]) -> MagicMock:
    """Wrap a list of named-tuple-like rows as if returned by db.execute(...).all()."""
    result = MagicMock()
    result.all.return_value = rows
    return result


def test_compare_compounds_picks_largest_gap_winner():
    """Three compounds; the one with the biggest dev−resale gap wins."""
    db = AsyncMock()
    # (compound, ptype, dev_avg, dev_n, res_avg, res_n)
    rows = [
        SimpleNamespace(compound="A", ptype="apartment", dev_avg=5_000_000, dev_n=10, res_avg=4_500_000, res_n=10),
        SimpleNamespace(compound="A", ptype="villa",     dev_avg=12_000_000, dev_n=5, res_avg=11_000_000, res_n=5),
        SimpleNamespace(compound="B", ptype="apartment", dev_avg=6_000_000, dev_n=8, res_avg=4_000_000, res_n=8),  # gap 2M — winner
        SimpleNamespace(compound="C", ptype="apartment", dev_avg=4_000_000, dev_n=4, res_avg=3_900_000, res_n=4),
    ]
    db.execute.return_value = _stub_grouped_rows(rows)

    result = asyncio.run(compare_compounds(["A", "B", "C"], db))
    assert result["missing_compound"] is None
    assert result["winner"] == "B"
    winning = next(c for c in result["per_compound"] if c["compound"] == "B")
    assert winning["max_gap_egp"] == 2_000_000


def test_compare_compounds_flags_compound_with_no_resale():
    """Compound D has no resale rows at all → missing_compound is set, no winner."""
    db = AsyncMock()
    rows = [
        SimpleNamespace(compound="A", ptype="apartment", dev_avg=5_000_000, dev_n=5, res_avg=4_000_000, res_n=5),
        # B has zero rows — absent from the grouped result entirely
        SimpleNamespace(compound="C", ptype="apartment", dev_avg=4_000_000, dev_n=5, res_avg=3_500_000, res_n=5),
    ]
    db.execute.return_value = _stub_grouped_rows(rows)

    result = asyncio.run(compare_compounds(["A", "B", "C"], db))
    assert result["missing_compound"] == "B"
    assert result["winner"] is None


def test_compare_compounds_drops_low_sample_buckets():
    """A bucket with <3 rows on either side is ignored (gap not computed)."""
    db = AsyncMock()
    rows = [
        # A apartment has only 2 dev rows — too few to count.
        SimpleNamespace(compound="A", ptype="apartment", dev_avg=5_000_000, dev_n=2, res_avg=4_000_000, res_n=5),
        # A villa is fully stocked.
        SimpleNamespace(compound="A", ptype="villa",     dev_avg=12_000_000, dev_n=5, res_avg=10_000_000, res_n=5),
        SimpleNamespace(compound="B", ptype="apartment", dev_avg=6_000_000, dev_n=5, res_avg=5_500_000, res_n=5),
    ]
    db.execute.return_value = _stub_grouped_rows(rows)

    result = asyncio.run(compare_compounds(["A", "B"], db))
    a = next(c for c in result["per_compound"] if c["compound"] == "A")
    # Apartment bucket dropped, villa bucket kept.
    assert a["apartment"] is None
    assert a["villa"] is not None
    # A's villa gap (2M) beats B's apartment gap (500K) → A wins.
    assert result["winner"] == "A"


# ─── Comparison service (best_deals_in_compound) ────────────────────────────


def test_best_deals_in_compound_returns_top_k_sorted_by_gap():
    """Three resale listings — the one with the biggest gap (dev_avg − price) ranks first."""
    db = AsyncMock()

    # First .execute() — dev-price averages per type.
    dev_rows = [SimpleNamespace(ptype="apartment", dev_avg=5_000_000, dev_n=10)]
    dev_result = MagicMock()
    dev_result.all.return_value = dev_rows

    # Second .execute() — resale listings.
    listings = [
        SimpleNamespace(
            id=1, title="Small unit", type="Apartment", size_sqm=120,
            resale_price=4_800_000, nawy_url="https://x/1", compound="X", is_available=True,
        ),
        SimpleNamespace(
            id=2, title="Big discount", type="Apartment", size_sqm=140,
            resale_price=4_200_000, nawy_url="https://x/2", compound="X", is_available=True,
        ),
        SimpleNamespace(
            id=3, title="Medium", type="Apartment", size_sqm=130,
            resale_price=4_600_000, nawy_url="https://x/3", compound="X", is_available=True,
        ),
    ]
    listings_result = MagicMock()
    listings_result.scalars.return_value.all.return_value = listings

    db.execute.side_effect = [dev_result, listings_result]

    result = asyncio.run(best_deals_in_compound("X", db, top_k=3))
    assert result["missing"] is False
    gaps = [d["gap_egp"] for d in result["top_listings"]]
    # Sorted descending: 800K, 400K, 200K
    assert gaps == [800_000, 400_000, 200_000]
    assert result["top_listings"][0]["property_id"] == 2


def test_best_deals_in_compound_marks_missing_when_no_dev_benchmark():
    db = AsyncMock()
    empty = MagicMock()
    empty.all.return_value = []
    db.execute.return_value = empty
    result = asyncio.run(best_deals_in_compound("Unknown Compound", db))
    assert result["missing"] == "no_dev_benchmark"
    assert result["top_listings"] == []


def test_best_deals_in_compound_marks_missing_when_no_resale_listings():
    db = AsyncMock()
    dev_rows = [SimpleNamespace(ptype="apartment", dev_avg=5_000_000, dev_n=10)]
    dev_result = MagicMock()
    dev_result.all.return_value = dev_rows
    empty_listings = MagicMock()
    empty_listings.scalars.return_value.all.return_value = []
    db.execute.side_effect = [dev_result, empty_listings]
    result = asyncio.run(best_deals_in_compound("X", db))
    assert result["missing"] == "no_resale_listings"
    assert result["top_listings"] == []


# ─── Dialog state machine ───────────────────────────────────────────────────


def _fresh_session() -> FreePathSession:
    return FreePathSession(
        session_id="test-session-1",
        state=comparison_dialog.STATE_AWAITING_NAMES,
        candidate_names=[],
        comparison_used=False,
    )


def test_dialog_redirects_when_user_asks_generic_question():
    """ROI question with no entities in AWAITING_NAMES → redirect prompt, state unchanged."""
    session = _fresh_session()
    db = AsyncMock()
    response = asyncio.run(
        comparison_dialog.handle_turn("عايز اعرف ROI في التجمع", session, db)
    )
    assert response["type"] == "clarification"
    assert response["show_upsell"] is False
    # Arabic copy contains the canonical opening phrase.
    assert "أنا هنا" in response["text"]
    assert session.state == comparison_dialog.STATE_AWAITING_NAMES


def test_dialog_rejects_too_many_entities():
    """4+ named entities → ask user to narrow down. State stays awaiting."""
    session = _fresh_session()
    db = AsyncMock()
    response = asyncio.run(
        comparison_dialog.handle_turn(
            "compare hyde park, sarai, bloomfields, marassi",
            session, db,
        )
    )
    assert response["type"] == "clarification"
    assert "اختار 3" in response["text"] or "Pick just 3" in response["text"]
    assert session.state == comparison_dialog.STATE_AWAITING_NAMES


def test_dialog_single_compound_runs_top_deals_and_terminates():
    """One compound named → SINGLE mode runs best_deals_in_compound and ends in DONE."""
    session = _fresh_session()
    db = AsyncMock()

    dev_result = MagicMock()
    dev_result.all.return_value = [
        SimpleNamespace(ptype="apartment", dev_avg=5_000_000, dev_n=10),
    ]
    listings_result = MagicMock()
    listings_result.scalars.return_value.all.return_value = [
        SimpleNamespace(
            id=1, title="Deal", type="Apartment", size_sqm=130,
            resale_price=4_200_000, nawy_url="https://x", compound="Sarai",
            is_available=True,
        ),
    ]
    db.execute.side_effect = [dev_result, listings_result]

    response = asyncio.run(
        comparison_dialog.handle_turn("احسن عرض في سراي", session, db)
    )
    assert response["type"] == "comparison"
    assert response["show_upsell"] is True
    assert response["upsell_reason"] == "comparison_used"
    assert session.state == comparison_dialog.STATE_DONE
    assert session.comparison_used is True
    assert session.mode == comparison_dialog.MODE_SINGLE


def test_dialog_multi_compound_runs_comparison_and_blurs_losers():
    """Two compounds named → MULTI mode, returns winner unblurred and the other blurred."""
    session = _fresh_session()
    db = AsyncMock()
    rows = [
        SimpleNamespace(compound="Sarai", ptype="apartment", dev_avg=6_000_000, dev_n=5, res_avg=4_000_000, res_n=5),
        SimpleNamespace(compound="Hyde Park", ptype="apartment", dev_avg=7_000_000, dev_n=5, res_avg=6_500_000, res_n=5),
    ]
    db.execute.return_value = _stub_grouped_rows(rows)

    response = asyncio.run(
        comparison_dialog.handle_turn("compare سراي و هايد بارك", session, db)
    )
    assert response["type"] == "comparison"
    assert session.state == comparison_dialog.STATE_DONE
    assert session.mode == comparison_dialog.MODE_MULTI
    # Winner has the bigger gap (Sarai: 2M vs Hyde Park: 500K).
    blurred = [p for p in response["properties"] if p.get("blurred")]
    unblurred = [p for p in response["properties"] if not p.get("blurred")]
    assert len(unblurred) == 1
    assert unblurred[0]["compound"] == "Sarai"
    assert len(blurred) == 1
    assert blurred[0]["compound"] == "Hyde Park"


def test_dialog_done_state_returns_upsell_on_next_turn():
    """Once comparison_used is set, the dialog returns the comparison_used upsell."""
    session = _fresh_session()
    session.state = comparison_dialog.STATE_DONE
    session.comparison_used = True

    db = AsyncMock()
    response = asyncio.run(
        comparison_dialog.handle_turn("any followup question", session, db)
    )
    assert response["type"] == "upsell"
    assert response["upsell_reason"] == "comparison_used"


def test_dialog_missing_resale_moves_to_missing_data_state():
    """When a named compound has no resale, dialog asks for a swap and stays open."""
    session = _fresh_session()
    db = AsyncMock()
    # Two compounds: B has zero rows entirely.
    rows = [
        SimpleNamespace(compound="A", ptype="apartment", dev_avg=5_000_000, dev_n=5, res_avg=4_000_000, res_n=5),
    ]
    db.execute.return_value = _stub_grouped_rows(rows)
    response = asyncio.run(
        comparison_dialog.handle_turn("compare سراي و هايد بارك", session, db)
    )
    assert response["type"] == "clarification"
    assert session.state == comparison_dialog.STATE_MISSING_DATA
    assert session.comparison_used is False


# ─── Router-level gating ────────────────────────────────────────────────────


def test_router_without_session_id_falls_back_to_upsell():
    """No session_id → can't persist state, so we send the user to upsell rather
    than trap them in a one-shot dialog."""
    db = AsyncMock()
    response = asyncio.run(
        local_router.process_query_async(
            query="any query",
            session_count=1,
            db=db,
            previous_queries=[],
            session_id=None,
        )
    )
    assert response["type"] == "upsell"
    assert response["show_upsell"] is True


def test_router_returns_comparison_used_upsell_when_session_flag_set():
    """If FreePathSession.comparison_used is already True, router short-circuits."""
    used_session = FreePathSession(
        session_id="sid-1",
        state=comparison_dialog.STATE_DONE,
        candidate_names=[],
        comparison_used=True,
    )

    # Build a db mock that returns the existing session on first .execute().
    db = AsyncMock()
    sess_result = MagicMock()
    sess_result.scalar_one_or_none.return_value = used_session
    db.execute.return_value = sess_result

    response = asyncio.run(
        local_router.process_query_async(
            query="another comparison?",
            session_count=1,
            db=db,
            previous_queries=[],
            session_id="sid-1",
        )
    )
    assert response["type"] == "upsell"
    assert response["upsell_reason"] == "comparison_used"


def test_router_hard_session_cap_still_wins():
    """The 5-message DEPTH_LIMIT cap remains the outermost guard."""
    db = AsyncMock()
    response = asyncio.run(
        local_router.process_query_async(
            query="anything",
            session_count=5,
            db=db,
            previous_queries=[],
            session_id="sid-cap",
        )
    )
    assert response["type"] == "upsell"
    assert response["upsell_reason"] == "depth_limit"
