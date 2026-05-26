"""
haggle_template.py
==================
Zero-LLM bilingual one-liner renderer for the FREE buyer haggle path.

The free tier intentionally burns no Claude tokens. This module renders
the haggle verdict from the negotiation_engine's HaggleRange output
using pure string interpolation. Premium calls swap this out for Wolf
narration with verifier protection.

Why zero tokens:
* Predictable cost on free tier (only DB + Redis).
* Sub-100ms latency (no network hop to Anthropic).
* Output is deterministic — perfect for snapshot tests + verifier tests.
"""
from __future__ import annotations

from typing import Final, Literal, Optional

from app.services.negotiation_engine import (
    ConfidenceTier,
    FairRangeEGP,
    HaggleRange,
)

Language = Literal["en", "ar"]


_CONFIDENCE_LABEL_EN: Final[dict[str, str]] = {
    "high": "high confidence",
    "moderate": "moderate confidence",
    "indicative": "indicative only",
}
_CONFIDENCE_LABEL_AR: Final[dict[str, str]] = {
    "high": "ثقة عالية",
    "moderate": "ثقة متوسطة",
    "indicative": "بيانات مبدئية",
}

_LEVERAGE_LABEL_EN: Final[dict[str, str]] = {
    "high": "strong leverage to negotiate",
    "moderate": "some leverage to negotiate",
    "low": "near market — limited room",
    "none": "at or below fair range — pay the asking",
}
_LEVERAGE_LABEL_AR: Final[dict[str, str]] = {
    "high": "عندك قوة تفاوض كبيرة",
    "moderate": "عندك مساحة تفاوض",
    "low": "قريب من السوق — مساحة تفاوض محدودة",
    "none": "السعر عادل أو أقل — لا داعي للتفاوض",
}


# ---------------------------------------------------------------------------
# Number formatting
# ---------------------------------------------------------------------------


def format_egp(amount: float, *, language: Language = "en") -> str:
    """
    Format an EGP amount for display.

    Above 1M: "3.5M EGP" / "3.5 مليون جنيه"
    Below 1M: "750,000 EGP" / "750,000 جنيه"
    """
    if amount >= 1_000_000:
        millions = amount / 1_000_000
        if language == "ar":
            return f"{millions:.2f} مليون جنيه".replace(".00", "")
        return f"{millions:.2f}M EGP".replace(".00", "")
    if language == "ar":
        return f"{int(amount):,} جنيه"
    return f"{int(amount):,} EGP"


def format_pct(value: float, *, language: Language = "en") -> str:
    """Format a signed proportion as 'X%' / '-X%'."""
    pct = round(value * 100)
    if language == "ar":
        # Arabic uses the same Arabic-Indic numerals or Western; keep Western
        # for consistency with the EGP formatting above.
        sign = "+" if pct > 0 else ""
        return f"{sign}{pct}%"
    sign = "+" if pct > 0 else ""
    return f"{sign}{pct}%"


# ---------------------------------------------------------------------------
# Public renderer
# ---------------------------------------------------------------------------


def render_free_verdict(
    haggle: HaggleRange,
    *,
    language: Language = "en",
) -> str:
    """
    Render the bilingual free-tier one-liner verdict.

    The output is a single short paragraph. It must be deterministic given
    the HaggleRange input — verifier snapshot tests depend on this.
    """
    if language == "ar":
        return _render_ar(haggle)
    return _render_en(haggle)


def render_both(haggle: HaggleRange) -> dict[str, str]:
    """Convenience: return {'en': ..., 'ar': ...} for surfaces that show both."""
    return {
        "en": render_free_verdict(haggle, language="en"),
        "ar": render_free_verdict(haggle, language="ar"),
    }


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _render_en(haggle: HaggleRange) -> str:
    fr: FairRangeEGP = haggle.fair_range_egp
    confidence = _CONFIDENCE_LABEL_EN.get(haggle.confidence_tier, haggle.confidence_tier)

    lines: list[str] = []
    lines.append(
        f"{haggle.compound} — {haggle.property_type.title()}, "
        f"{haggle.bedrooms}BR, {haggle.size_sqm:g}m²"
    )
    lines.append(
        f"Fair range: {format_egp(fr.low)} – {format_egp(fr.high)}. "
        f"Median: {format_egp(fr.median)}."
    )

    if haggle.listing_price_egp is not None and haggle.pct_vs_market is not None:
        leverage = _LEVERAGE_LABEL_EN.get(haggle.leverage_signal, "")
        lines.append(
            f"Listed at {format_egp(haggle.listing_price_egp)}: "
            f"{format_pct(haggle.pct_vs_market)} vs market — {leverage}."
        )

    lines.append(
        f"Based on {haggle.comps_used} closing"
        f"{'s' if haggle.comps_used != 1 else ''} "
        f"({confidence})."
    )
    return " ".join(lines)


def _render_ar(haggle: HaggleRange) -> str:
    fr: FairRangeEGP = haggle.fair_range_egp
    confidence = _CONFIDENCE_LABEL_AR.get(haggle.confidence_tier, haggle.confidence_tier)

    lines: list[str] = []
    lines.append(
        f"{haggle.compound} — {_ar_property_type(haggle.property_type)} "
        f"{haggle.bedrooms} غرف، {haggle.size_sqm:g} م²"
    )
    lines.append(
        f"السعر العادل: {format_egp(fr.low, language='ar')} – "
        f"{format_egp(fr.high, language='ar')}. "
        f"الوسيط: {format_egp(fr.median, language='ar')}."
    )

    if haggle.listing_price_egp is not None and haggle.pct_vs_market is not None:
        leverage = _LEVERAGE_LABEL_AR.get(haggle.leverage_signal, "")
        lines.append(
            f"السعر المعروض {format_egp(haggle.listing_price_egp, language='ar')}: "
            f"{format_pct(haggle.pct_vs_market, language='ar')} من السوق — "
            f"{leverage}."
        )

    lines.append(
        f"بناءً على {haggle.comps_used} صفقة ({confidence})."
    )
    return " ".join(lines)


_AR_PROPERTY_TYPE: Final[dict[str, str]] = {
    "apartment": "شقة",
    "villa": "فيلا",
    "townhouse": "تاون هاوس",
    "duplex": "دوبلكس",
    "penthouse": "بنتهاوس",
    "studio": "ستوديو",
}


def _ar_property_type(en: str) -> str:
    return _AR_PROPERTY_TYPE.get(en.lower(), en)
