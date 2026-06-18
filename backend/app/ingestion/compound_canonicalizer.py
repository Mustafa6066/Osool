"""
Compound Canonicalizer — entity resolution for compound names.
----------------------------------------------------------------
Multiple scrapers feed the same compound under different spellings and
languages: "Mountain View iCity", "mountain view icity", "ماونتن فيو اي سيتي",
"ماونتين فيو". Stored raw, these fragment the DB, the market-analysis layer,
and (worst) the vector store — the same compound gets several embeddings and
several price baselines.

This module collapses all variants to ONE canonical name BEFORE upsert and
embedding, so dedup happens at the source.

Strategy (deterministic, zero-token):
  1. Normalize: NFKC, strip Arabic diacritics + tatweel, unify alef/ya/hamza/
     ta-marbuta, drop punctuation, collapse whitespace, lowercase.
  2. Exact match against the curated alias table (reused from the perception
     layer's COMPOUND_ALIASES — single source of truth, AR + EN).
  3. Whole-phrase containment (alias appears as contiguous words in the name).
  4. Fuzzy match against known canonical names (difflib, high cutoff).
  5. Unknown compound -> a cleaned, consistently-cased form so even unmapped
     names dedupe against their own variants (whitespace/case only).

Pure stdlib. Never raises (returns the cleaned input on any failure).
"""
from __future__ import annotations

import difflib
import logging
import re
import unicodedata
from functools import lru_cache
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Arabic diacritics (harakat U+064B-U+0652, Quranic marks U+0610-U+061A),
# superscript alef (U+0670), and tatweel/kashida (U+0640).
_AR_DIACRITICS = re.compile("[ؐ-ًؚ-ْٰـ]")
# Zero-width chars (U+200B-U+200F), bidi marks (U+202A-U+202E), BOM (U+FEFF).
_ZERO_WIDTH = re.compile("[​-‏‪-‮﻿]")

# Alef/ya/hamza/ta-marbuta unification so spelling variants collapse.
# Keyed by codepoint to avoid any literal-glyph ambiguity.
_AR_UNIFY = {
    0x0623: "ا",  # أ -> ا
    0x0625: "ا",  # إ -> ا
    0x0622: "ا",  # آ -> ا
    0x0671: "ا",  # ٱ -> ا
    0x0649: "ي",  # ى -> ي
    0x0626: "ي",  # ئ -> ي
    0x0624: "و",  # ؤ -> و
    0x0629: "ه",  # ة -> ه
}

# Minimal fallback map used only if the perception layer can't be imported
# (keeps this module independently testable). The live source of truth is
# perception_layer.COMPOUND_ALIASES.
_FALLBACK_ALIASES: Dict[str, Tuple[str, str]] = {
    "mountain view": ("Mountain View iCity", "New Cairo"),
    "ماونتن فيو": ("Mountain View iCity", "New Cairo"),       # ماونتن فيو
    "ماونتين فيو": ("Mountain View iCity", "New Cairo"),  # ماونتين فيو
    "mountain view icity": ("Mountain View iCity", "New Cairo"),
    "palm hills": ("Palm Hills New Cairo", "New Cairo"),
    "بالم هيلز": ("Palm Hills New Cairo", "New Cairo"),  # بالم هيلز
    "hyde park": ("Hyde Park", "New Cairo"),
    "هايد بارك": ("Hyde Park", "New Cairo"),  # هايد بارك
    "sodic": ("Sodic East", "New Cairo"),
    "سوديك": ("Sodic East", "New Cairo"),  # سوديك
    "mivida": ("Mivida", "New Cairo"),
    "ميفيدا": ("Mivida", "New Cairo"),  # ميفيدا
}


def arabic_normalize(s: str) -> str:
    """NFKC + strip diacritics/tatweel + unify alef/ya/hamza/ta-marbuta."""
    s = unicodedata.normalize("NFKC", s)
    s = _AR_DIACRITICS.sub("", s)
    s = _ZERO_WIDTH.sub("", s)
    return s.translate(_AR_UNIFY)


def _norm_key(s: str) -> str:
    """Aggressive normalization used only for matching (not for storage)."""
    s = arabic_normalize((s or "").strip().lower())
    # Replace any non-word / non-Arabic char with a space, then collapse.
    s = re.sub("[^\\w؀-ۿ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _title_clean(raw: str) -> str:
    """Stable display form for unmapped compounds: trimmed, single-spaced,
    Latin words title-cased (Arabic left as-is). Ensures variants that differ
    only by case/whitespace still collapse to one stored value."""
    s = _ZERO_WIDTH.sub("", unicodedata.normalize("NFKC", raw or "")).strip()
    s = re.sub(r"\s+", " ", s)
    return " ".join(
        (w.capitalize() if re.search(r"[a-zA-Z]", w) else w) for w in s.split()
    )


@lru_cache(maxsize=1)
def _alias_tables() -> Tuple[Dict[str, str], Dict[str, str]]:
    """Build (normalized_alias -> canonical, normalized_canonical -> canonical).

    Reuses perception_layer.COMPOUND_ALIASES (curated AR+EN) as the single
    source of truth; falls back to a minimal built-in map if that import fails.
    Cached — built once per process.
    """
    try:
        from app.ai_engine.perception_layer import COMPOUND_ALIASES as src
    except Exception:  # pragma: no cover — import guard
        src = _FALLBACK_ALIASES

    alias_to_canonical: Dict[str, str] = {}
    canonical_norm: Dict[str, str] = {}
    for alias, value in src.items():
        canonical = value[0] if isinstance(value, (tuple, list)) else str(value)
        ak = _norm_key(alias)
        ck = _norm_key(canonical)
        if ak:
            alias_to_canonical[ak] = canonical
        if ck:
            alias_to_canonical.setdefault(ck, canonical)
            canonical_norm[ck] = canonical
    return alias_to_canonical, canonical_norm


def canonicalize_compound(raw: Optional[str]) -> Optional[str]:
    """Resolve a raw compound name to its canonical form.

    Returns None for empty input. Never raises — on any internal failure it
    returns a cleaned version of the input so ingestion is never blocked.
    """
    if not raw or not str(raw).strip():
        return None
    try:
        alias_to_canonical, canonical_norm = _alias_tables()
        key = _norm_key(str(raw))
        if not key:
            return _title_clean(str(raw))

        # 1. exact normalized match (alias or canonical)
        if key in alias_to_canonical:
            return alias_to_canonical[key]

        # 2. whole-phrase containment (avoid substring-within-word false hits)
        padded = f" {key} "
        for ak, canonical in alias_to_canonical.items():
            if len(ak) >= 3 and f" {ak} " in padded:
                return canonical

        # 3. fuzzy against known canonical names
        match = difflib.get_close_matches(key, list(canonical_norm.keys()), n=1, cutoff=0.86)
        if match:
            return canonical_norm[match[0]]

        # 4. unknown — stable cleaned form (case/whitespace dedup)
        return _title_clean(str(raw))
    except Exception as e:  # pragma: no cover — safety net
        logger.warning("canonicalize_compound failed for %r: %s", raw, e)
        return _title_clean(str(raw))


__all__ = ["canonicalize_compound", "arabic_normalize"]
