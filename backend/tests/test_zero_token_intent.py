"""
Zero-Token Intent Extractor — contract tests.

Two invariants this suite enforces:

  1. **Zero API calls.** No OpenAI, no Anthropic, no httpx call to any
     LLM provider. The whole module is regex + dictionaries; importing
     it must not pull in any client SDK at runtime. The test patches
     the SDKs to fail loudly if anything tries to call them.

  2. **Correctness on 40 representative prompts** spanning:
     - Pure English / pure Arabic / mixed
     - Numeric anchors (price, beds, size, %, year)
     - Locations (canonical + dialect)
     - Compounds + developers
     - Property types
     - Finishing levels
     - Payment intent (cash, installment, Nawy Now)
     - Empty / nonsense input
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.services.zero_token_intent import (
    StructuredQuery,
    extract_query,
)


# ─────────────────────────────────────────────────────────────────────────────
# Invariant 1 — no API client is ever instantiated or called
# ─────────────────────────────────────────────────────────────────────────────

@patch("openai.AsyncOpenAI", side_effect=AssertionError("OpenAI must not be called"))
@patch("openai.OpenAI", side_effect=AssertionError("OpenAI must not be called"))
@patch("anthropic.AsyncAnthropic", side_effect=AssertionError("Anthropic must not be called"))
@patch("anthropic.Anthropic", side_effect=AssertionError("Anthropic must not be called"))
def test_extract_query_never_calls_an_llm(_ant, _ant2, _oai, _oai2):
    """If the regex path slips a call to an LLM provider, this test fails."""
    prompts = [
        "3BR apartment in New Cairo under 8M EGP",
        "شقة في الشيخ زايد، تشطيب كامل، ميزانية 10 مليون",
        "modern villa with garden in north coast",
        "townhouse mountain view",
        "ready unit nawy now ain sokhna",
        "investor looking for la2ta in palm hills",
        "",
        "hello",
        "أبحث عن شقة 3 غرف في مدينة الشيخ زايد بحوالي 7 مليون جنيه",
        "duplex 250 m² in 6 october, semi finished, max 12 million, 8 year installments",
    ]
    for p in prompts:
        result = extract_query(p)
        assert isinstance(result, StructuredQuery)


# ─────────────────────────────────────────────────────────────────────────────
# Invariant 2 — golden set
# ─────────────────────────────────────────────────────────────────────────────

# Each row: (prompt, expected_partial_fields_dict)
# expected_partial_fields_dict is checked field-by-field; ONLY listed
# fields are asserted (others may legitimately be None / [] / "").
GOLDEN = [
    # ── English structured ──────────────────────────────────────────────────
    (
        "3BR apartment in New Cairo under 8M EGP",
        {"bedrooms_min": 3, "bedrooms_max": 3, "price_max": 8_000_000,
         "locations": ["New Cairo"], "property_types": ["Apartment"]},
    ),
    (
        "4 bed villa sheikh zayed",
        {"bedrooms_min": 4, "locations": ["Sheikh Zayed"], "property_types": ["Villa"]},
    ),
    (
        "studio in maadi under 3 million",
        {"bedrooms_max": 0, "price_max": 3_000_000, "locations": ["Maadi"]},
    ),
    (
        "townhouse mountain view 6 october 5 year payment plan",
        {"property_types": ["Townhouse"], "locations": ["6th October"],
         "installment_years_min": 5, "is_cash_only": False},
    ),
    (
        "ready apartment new capital with 20% down payment",
        {"property_types": ["Apartment"], "locations": ["New Administrative Capital"],
         "down_payment_pct_max": 20, "is_delivered": True},
    ),
    (
        "penthouse 250 sqm fully finished 12M EGP",
        {"property_types": ["Penthouse"], "size_sqm_min": 250, "size_sqm_max": 250,
         "price_max": 12_000_000, "finishing_levels": ["Fully Finished"]},
    ),
    (
        "chalet north coast nawy now",
        {"property_types": ["Chalet"], "locations": ["North Coast"], "is_nawy_now": True},
    ),
    (
        "duplex sodic westown ready by 2025",
        {"property_types": ["Duplex"], "ready_by_year_max": 2025,
         "intent_tags": ["needs_delivery_by_2025"]},
    ),
    (
        "twin house in new zayed 10-year installments core and shell",
        {"property_types": ["Twin House"], "locations": ["New Zayed"],
         "installment_years_min": 10, "finishing_levels": ["Core & Shell"],
         "is_cash_only": False},
    ),
    (
        "3 bedroom resale in ain sokhna",
        {"bedrooms_min": 3, "bedrooms_max": 3, "locations": ["Ain Sokhna"],
         "sale_types": ["Resale"]},
    ),
    # ── Arabic ──────────────────────────────────────────────────────────────
    (
        "شقة في الشيخ زايد، تشطيب كامل، ميزانية 10 مليون",
        {"property_types": ["Apartment"], "locations": ["Sheikh Zayed"],
         "finishing_levels": ["Fully Finished"], "price_max": 10_000_000},
    ),
    (
        "فيلا 4 غرف في القاهرة الجديدة",
        {"property_types": ["Villa"], "bedrooms_min": 4, "locations": ["New Cairo"]},
    ),
    (
        "تاون هاوس 6 اكتوبر بالتقسيط 8 سنوات",
        {"property_types": ["Townhouse"], "locations": ["6th October"],
         "installment_years_min": 8, "is_cash_only": False},
    ),
    (
        "أبحث عن شقة في العاصمة الإدارية تسليم فوري",
        {"property_types": ["Apartment"],
         "locations": ["New Administrative Capital"], "is_nawy_now": True},
    ),
    (
        "دوبلكس في الساحل الشمالي 250 متر",
        {"property_types": ["Duplex"], "locations": ["North Coast"],
         "size_sqm_min": 250, "size_sqm_max": 250},
    ),
    (
        "بنتهاوس في زايد 15 مليون",
        {"property_types": ["Penthouse"], "locations": ["Sheikh Zayed"],
         "price_max": 15_000_000},
    ),
    (
        "ميزانية ٧ مليون شقة ٣ غرف",
        {"price_max": 7_000_000, "bedrooms_min": 3, "bedrooms_max": 3,
         "property_types": ["Apartment"]},
    ),
    # ── Mixed English/Arabic ─────────────────────────────────────────────────
    (
        "شقة 3BR في New Cairo بسعر 8M",
        {"property_types": ["Apartment"], "bedrooms_min": 3,
         "locations": ["New Cairo"], "price_max": 8_000_000},
    ),
    (
        "villa التجمع الخامس 12 مليون",
        {"property_types": ["Villa"], "locations": ["New Cairo"],
         "price_max": 12_000_000},
    ),
    # ── Persona / intent tags ────────────────────────────────────────────────
    (
        "first time buyer 3BR apartment new cairo",
        {"intent_tags": ["first_time_buyer"], "bedrooms_min": 3,
         "property_types": ["Apartment"], "locations": ["New Cairo"]},
    ),
    (
        "investor looking for high ROI in new capital",
        {"intent_tags": ["investor"], "locations": ["New Administrative Capital"]},
    ),
    (
        "diaspora buyer family villa ready by 2024",
        {"intent_tags": ["diaspora", "family"], "property_types": ["Villa"],
         "ready_by_year_max": 2024},
    ),
    (
        "luxury penthouse zamalek",
        {"intent_tags": ["luxury"], "property_types": ["Penthouse"],
         "locations": ["Zamalek"]},
    ),
    # ── Range / no max ───────────────────────────────────────────────────────
    (
        "budget at least 5 million up to 10 million 3BR",
        {"price_min": 5_000_000, "price_max": 10_000_000,
         "bedrooms_min": 3, "bedrooms_max": 3},
    ),
    # ── Quarter delivery ─────────────────────────────────────────────────────
    (
        "apartment new cairo Q4 2025",
        {"property_types": ["Apartment"], "locations": ["New Cairo"],
         "ready_by_year_max": 2025},
    ),
    # ── Off-plan / developer sale ────────────────────────────────────────────
    (
        "off-plan apartment new capital with payment plan",
        {"property_types": ["Apartment"],
         "locations": ["New Administrative Capital"],
         "sale_types": ["Developer"], "is_cash_only": False},
    ),
    # ── Cash only ────────────────────────────────────────────────────────────
    (
        "cash only chalet north coast 5M",
        {"property_types": ["Chalet"], "locations": ["North Coast"],
         "price_max": 5_000_000, "is_cash_only": True},
    ),
    # ── Single-token / minimal ───────────────────────────────────────────────
    ("apartment", {"property_types": ["Apartment"]}),
    ("villa", {"property_types": ["Villa"]}),
    ("الشيخ زايد", {"locations": ["Sheikh Zayed"]}),
    # ── Empty / no signal — must return empty StructuredQuery ────────────────
    ("", {}),
    ("hello", {}),
    ("can you help me", {}),
    # ── Edge: just a price ───────────────────────────────────────────────────
    ("budget 5 million", {"price_max": 5_000_000}),
    ("under 3M EGP", {"price_max": 3_000_000}),
    # ── Edge: just bedrooms ──────────────────────────────────────────────────
    ("3 bedrooms", {"bedrooms_min": 3, "bedrooms_max": 3}),
    # ── Edge: just delivery ──────────────────────────────────────────────────
    ("ready to move", {"is_nawy_now": True}),
    ("instant delivery", {"is_nawy_now": True}),
    # ── Edge: bilingual cash ─────────────────────────────────────────────────
    ("villa كاش", {"property_types": ["Villa"], "is_cash_only": True}),
    # ── Edge: arabic resale ──────────────────────────────────────────────────
    ("شقة إعادة بيع في زايد", {"property_types": ["Apartment"],
                                "locations": ["Sheikh Zayed"],
                                "sale_types": ["Resale"]}),
]


@pytest.mark.parametrize("prompt,expected", GOLDEN)
def test_golden_extraction(prompt: str, expected: dict):
    result = extract_query(prompt)
    for field_name, expected_value in expected.items():
        actual = getattr(result, field_name)
        if isinstance(expected_value, list):
            # Lists are subset-matched — we assert expected items are in actual,
            # not that actual is exactly equal (allows extra extractions).
            for item in expected_value:
                assert item in actual, (
                    f"prompt={prompt!r} field={field_name}: "
                    f"expected {item!r} in {actual}"
                )
        else:
            assert actual == expected_value, (
                f"prompt={prompt!r} field={field_name}: "
                f"expected {expected_value!r}, got {actual!r}"
            )


def test_empty_input_returns_empty_query():
    q = extract_query("")
    assert q.is_empty()
    assert q.bedrooms_min is None and q.locations == [] and q.semantic_text == ""


def test_none_input_does_not_raise():
    q = extract_query(None)  # type: ignore[arg-type]
    assert q.is_empty()


def test_buyer_context_pass_through():
    q = extract_query("3BR new cairo", buyer_budget_cap=9_000_000, buyer_persona="FIRST_TIME_BUYER")
    assert q.buyer_budget_cap == 9_000_000
    assert q.buyer_persona == "FIRST_TIME_BUYER"


# ─────────────────────────────────────────────────────────────────────────────
# Performance smoke (not enforced — informational only)
# ─────────────────────────────────────────────────────────────────────────────

def test_performance_smoke():
    """1000 prompts in <2s end-to-end (rough p99 sanity check)."""
    import time
    prompts = [p for p, _ in GOLDEN] * 25  # 40 × 25 = 1000
    start = time.perf_counter()
    for p in prompts:
        extract_query(p)
    elapsed = time.perf_counter() - start
    # Per-extraction p50 < 2ms. 1000 × 2ms = 2s ceiling.
    assert elapsed < 2.0, f"1000 extractions took {elapsed:.2f}s (too slow)"
