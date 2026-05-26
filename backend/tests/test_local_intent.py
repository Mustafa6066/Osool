"""
Deterministic intent parsing tests for the zero-token local path.
"""

from app.ai_engine.local_intent import local_intent_extractor


def test_extract_intent_new_cairo_budget_and_rooms():
    intent = local_intent_extractor.extract_intent(
        "I am looking for an apartment in Tagamoa with 3 rooms and my budget is 8 million"
    )

    assert intent["intent"] == "SEARCH"
    assert intent["area"] == "new cairo"
    assert intent["property_type"] == "apartment"
    assert intent["max_budget"] == 8_000_000
    assert intent["rooms"] == 3


def test_extract_intent_arabic_digits_and_budget_range():
    intent = local_intent_extractor.extract_intent(
        "عايز شقة في القاهرة الجديدة ٣ غرف ب ٥ إلى ٨ مليون"
    )

    assert intent["intent"] == "SEARCH"
    assert intent["area"] == "new cairo"
    assert intent["property_type"] == "apartment"
    assert intent["max_budget"] == 8_000_000
    assert intent["rooms"] == 3


def test_extract_intent_complex_forecast_trigger():
    intent = local_intent_extractor.extract_intent(
        "What is the ROI and inflation hedge outlook for this property?"
    )

    assert intent["intent"] == "COMPLEX"
