"""
Tests for the compound canonicalizer (Bottleneck #2: dedup compounds fed under
different names/languages). Pure stdlib — no DB, no network.
"""
from __future__ import annotations

import os

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-minimum-32-chars-long")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-key")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")

from app.ingestion.compound_canonicalizer import (  # noqa: E402
    arabic_normalize,
    canonicalize_compound,
)


def test_english_and_arabic_collapse_to_same_canonical():
    en = canonicalize_compound("Mountain View iCity")
    ar = canonicalize_compound("ماونتن فيو")
    assert en == ar == "Mountain View iCity"


def test_case_and_whitespace_insensitive():
    assert canonicalize_compound("  mountain   view  icity ") == "Mountain View iCity"


def test_arabic_spelling_variant_maps():
    # alternate transliteration spelling should still resolve
    assert canonicalize_compound("ماونتين فيو") == "Mountain View iCity"


def test_canonical_is_idempotent():
    once = canonicalize_compound("Palm Hills")
    assert canonicalize_compound(once) == once


def test_unknown_compound_cleaned_and_idempotent():
    cleaned = canonicalize_compound("  some  NEW  compound ")
    assert cleaned == "Some New Compound"
    # feeding the cleaned value back yields the same value (stable dedup key)
    assert canonicalize_compound(cleaned) == cleaned


def test_empty_or_blank_returns_none():
    assert canonicalize_compound("") is None
    assert canonicalize_compound(None) is None
    assert canonicalize_compound("    ") is None


def test_arabic_normalize_strips_diacritics_and_unifies_alef():
    # tanwin (U+064B) stripped; hamza-on-alef (U+0623) unified to bare alef
    assert "ً" not in arabic_normalize("مً")
    assert arabic_normalize("أ") == "ا"
