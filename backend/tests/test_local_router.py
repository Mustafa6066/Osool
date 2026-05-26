"""
Free-path local-router tests.

The free path's only first-class behavior is now compound comparison.
`_merge_previous_intent` survives as a utility, but the old "ask for area +
budget, run tiered fallback, return a property card" tests are gone — replaced
by the comparison-flow suite in test_comparison_flow.py.
"""

from app.ai_engine.local_intent import local_intent_extractor
from app.ai_engine.local_router import local_router


def test_local_intent_merges_arabic_compound_context():
    """The intent merge utility still consolidates entities across turns,
    even though the free path itself no longer uses it. Kept for parity with
    paid-path callers that may still rely on it."""
    first_turn = "عن سعر شقة بالم هيلز التجمع"
    second_turn = "7 مليون"

    first_intent = local_intent_extractor.extract_intent(first_turn)
    second_intent = local_intent_extractor.extract_intent(second_turn)
    merged = local_router._merge_previous_intent(second_intent, [first_turn])

    assert first_intent["area"] == "new cairo"
    assert first_intent["compound"] == "Palm Hills"
    assert first_intent["property_type"] == "apartment"
    assert merged["area"] == "new cairo"
    assert merged["compound"] == "Palm Hills"
    assert merged["property_type"] == "apartment"
    assert merged["max_budget"] == 7_000_000
