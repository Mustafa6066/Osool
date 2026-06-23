"""
Free-path (zero-token) intent router.

The live free path used to funnel EVERY logged-in free user message into a
single "best resale price vs. developer average" answer. That collapsed three
distinct user questions into one card:

  1. "best price" / "developer price for X"        → single best-price match  (handled elsewhere)
  2. "compare developer price across A, B, C"      → MULTI-ENTITY comparison  (here)
  3. "how much did Sodic appreciate over 5 years"  → APPRECIATION / growth     (here)

This module adds zero-LLM classification + two new deterministic handlers so a
free user gets the *right shape* of answer. Everything is SQL + hardcoded
market tables — no Anthropic/OpenAI tokens are spent.

Wiring: `free_tier_gate.build_best_price_free_payload` calls `classify_free_intent`
first and dispatches here. Both /api/v1/chat and /api/chat/stream inherit the
routing for free because both already call `build_best_price_free_payload`.

Payload shape: every dict returned here carries the FULL free-payload key set
(see `_base_payload`). The streaming endpoint reads several of these keys
directly (`free_payload["ui_actions"]`, `["suggestions"]`, `["lead_score"]`, …)
so a missing key would KeyError the SSE stream.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Optional

logger = logging.getLogger(__name__)

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_engine.analytical_engine import (
    AREA_PRICE_HISTORY,
    DEVELOPER_PRICE_HISTORY,
)
from app.ai_engine.flagship_compounds import (
    DEVELOPER_TO_COMPOUNDS,
    get_delivery_track_record,
)
from app.ai_engine.local_intent import local_intent_extractor
from app.models import Property


# ── Language / formatting helpers (kept local to avoid a free_tier_gate cycle) ──
_ARABIC_TEXT_RE = re.compile(r"[؀-ۿ]")
_YEARS_RE = re.compile(r"(\d+)\s*(?:سنين|سنوات|سنه|years?|yrs?|yr)")

# Map the intent extractor's canonical area keys → the history-table keys.
_AREA_CANON_TO_HISTORY = {
    "new cairo": "New Cairo",
    "sheikh zayed": "Sheikh Zayed",
    "6th of october": "6th October",
    "north coast": "North Coast",
    "new capital": "New Capital",
    "madinaty": "Madinaty",
    "rehab": "Rehab",
    "maadi": "Maadi",
}
_AREA_LABEL_AR = {
    "new cairo": "القاهرة الجديدة / التجمع",
    "sheikh zayed": "الشيخ زايد",
    "6th of october": "6 أكتوبر",
    "north coast": "الساحل الشمالي",
    "new capital": "العاصمة الإدارية",
    "madinaty": "مدينتي",
    "rehab": "الرحاب",
    "maadi": "المعادي",
}
# Same area→SQL-pattern dictionary the best-price path uses, so the comparison
# honours an area filter consistently.
_AREA_SQL_PATTERNS = {
    "new cairo": [
        "new cairo", "fifth settlement", "5th settlement", "tagamoa", "tagamo3",
        "tagamo3a", "cairo festival", "التجمع", "القاهرة الجديدة",
    ],
    "sheikh zayed": ["sheikh zayed", "zayed", "زايد", "الشيخ زايد"],
    "6th of october": ["6th of october", "6 october", "october", "اكتوبر", "أكتوبر"],
    "north coast": ["north coast", "sahel", "الساحل", "الساحل الشمالي"],
    "new capital": ["new capital", "capital", "العاصمة", "العاصمة الادارية", "العاصمة الإدارية"],
    "mostakbal city": ["mostakbal", "mostaqbal", "future city", "مستقبل", "المستقبل"],
    "capital gardens": ["capital gardens", "كابيتال جاردنز", "كابيتال"],
    "october gardens": ["october gardens", "حدائق اكتوبر", "حدائق أكتوبر"],
    "ain sokhna": ["ain sokhna", "sokhna", "السخنة", "العين السخنة"],
    "el gouna": ["el gouna", "gouna", "الجونة"],
}
_TYPE_LABELS_AR = {
    "apartment": "شقة", "villa": "فيلا", "townhouse": "تاون هاوس",
    "twinhouse": "توين هاوس", "duplex": "دوبلكس", "studio": "استوديو",
    "chalet": "شاليه", "penthouse": "بنتهاوس",
}
_DISPLAY_NAME_AR = {
    "Mountain View": "ماونتن فيو", "Hassan Allam": "حسن علام", "Sodic": "سوديك",
    "Palm Hills": "بالم هيلز", "La Vista": "لافيستا", "Emaar": "إعمار", "ORA": "أورا",
    "Tatweer Misr": "تطوير مصر", "Madinet Masr": "مدينة مصر", "Hyde Park": "هايد بارك",
    "Sarai": "سراي", "ZED East": "زيد إيست", "Marassi": "مراسي",
    "Uptown Cairo": "أبتاون القاهرة", "Taj City": "تاج سيتي", "Badya": "بادية",
    "New Giza": "نيو جيزة", "Cairo Festival City": "كايرو فيستيفال سيتي",
    "Bloomfields": "بلومفيلدز", "Fouka Bay": "فوكا باي", "Waterway": "واتر واي",
    "Mountain View iCity": "ماونتن فيو آي سيتي",
}

# Appreciation triggers — already in normalized form (ة→ه, no diacritics) so
# they match `local_intent._normalize_query` output directly.
_APPRECIATION_KEYWORDS = [
    # Arabic
    "زياده", "ارتفاع", "نمو", "زاد", "تغير", "اتغير", "ارتفع", "معدل الزياده",
    # English
    "appreciat", "growth", "grew", "grown", "grow", "increase", "increased",
    "rise", "rose", "went up", "gone up", "cagr", "yoy", "year over year",
    "year-on-year", "how much has", "price trend", "price history",
]


def _contains_arabic(text: str) -> bool:
    return bool(text and _ARABIC_TEXT_RE.search(text))


def _resolve_language(requested_language: str, message: str) -> str:
    requested = (requested_language or "auto").lower()
    if requested in {"ar", "en"}:
        return requested
    return "ar" if _contains_arabic(message or "") else "en"


def _format_egp(value: Optional[float], language: str) -> str:
    try:
        amount = float(value or 0)
    except (TypeError, ValueError):
        amount = 0.0
    return f"{amount:,.0f} ج.م" if language == "ar" else f"{amount:,.0f} EGP"


def _format_psm(value: Optional[float], language: str) -> str:
    try:
        amount = float(value or 0)
    except (TypeError, ValueError):
        amount = 0.0
    return f"{amount:,.0f} ج.م/م²" if language == "ar" else f"{amount:,.0f} EGP/m²"


def _display_name(name: str, language: str) -> str:
    return _DISPLAY_NAME_AR.get(name, name) if language == "ar" else name


def _type_label(ptype: Optional[str], language: str) -> str:
    pt = (ptype or "").lower()
    if language == "ar":
        return _TYPE_LABELS_AR.get(pt, ptype or "")
    return (ptype or "").title()


def _base_payload(language: str) -> dict[str, Any]:
    """Full free-payload skeleton. Handlers override the meaningful fields.

    Mirrors the key set returned by `free_tier_gate.build_best_price_free_payload`
    so the streaming endpoint's direct key access never KeyErrors.
    """
    return {
        "response": "",
        "properties": [],
        "ui_actions": [],
        "show_upsell": False,
        "upsell_reason": None,
        "ui_primitive_descriptor": None,
        "primitive_data": {},
        "response_type": "free_local",
        "showing_strategy": "FREE_LOCAL",
        "lead_score": 20,
        "readiness_score": 20,
        "detected_language": language,
        "suggestions": [],
        "cta_actions": [],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Intent classification
# ─────────────────────────────────────────────────────────────────────────────

def classify_free_intent(message: str) -> str:
    """Return one of: "appreciation" | "compare" | "best_price".

    Priority: appreciation (growth/trend over time) beats comparison beats the
    default best-price match. Pure string + entity matching, zero tokens.
    """
    norm = local_intent_extractor._normalize_query(message or "")

    has_appreciation_kw = any(kw in norm for kw in _APPRECIATION_KEYWORDS)
    if has_appreciation_kw:
        # Guard against false positives ("increase my budget"): require a price
        # or time-window or a named entity/area to anchor it as a market query.
        intent = local_intent_extractor.extract_intent(message or "")
        anchored = (
            _YEARS_RE.search(norm) is not None
            or "سعر" in norm
            or "price" in norm
            or bool(intent.get("area"))
            or bool(intent.get("compound"))
            or len(local_intent_extractor.extract_entities(message or "")) >= 1
        )
        if anchored:
            return "appreciation"

    # Two or more named developers/compounds → cross-entity comparison.
    if len(local_intent_extractor.extract_entities(message or "")) >= 2:
        return "compare"

    return "best_price"


# ─────────────────────────────────────────────────────────────────────────────
# Appreciation handler (zero DB — hardcoded 2021-2026 market history)
# ─────────────────────────────────────────────────────────────────────────────

def _extract_years_window(message: str) -> int:
    norm = local_intent_extractor._normalize_query(message or "")
    m = _YEARS_RE.search(norm)
    if m:
        try:
            n = int(m.group(1))
            if 1 <= n <= 10:
                return n
        except (TypeError, ValueError):
            pass
    return 5  # default horizon


def _developer_series(developer_canonical: str, area_key: Optional[str]) -> Optional[dict[int, float]]:
    """Average the yearly per-sqm series across all DEVELOPER_PRICE_HISTORY
    entries whose key contains the developer name. Prefer entries matching the
    requested area when one is supplied."""
    token = developer_canonical.lower()
    area_history = _AREA_CANON_TO_HISTORY.get(area_key or "")
    matches: list[dict] = []
    for key, data in DEVELOPER_PRICE_HISTORY.items():
        if token in key.lower():
            matches.append(data)
    if not matches:
        return None
    if area_history:
        area_filtered = [d for d in matches if d.get("area") == area_history]
        if area_filtered:
            matches = area_filtered

    years = [y for y in range(2021, 2027)]
    series: dict[int, float] = {}
    for y in years:
        vals = [float(d[y]) for d in matches if isinstance(d.get(y), (int, float))]
        if vals:
            series[y] = sum(vals) / len(vals)
    return series or None


def _compound_to_developer(compound_canonical: str) -> Optional[str]:
    for dev, compounds in DEVELOPER_TO_COMPOUNDS.items():
        if compound_canonical in compounds:
            return dev
    return None


def _resolve_appreciation_series(message: str) -> Optional[dict[str, Any]]:
    """Resolve the best price series for the named subject.

    Returns {"label_en", "label_ar", "series": {year: psm}, "basis"} or None.
    Resolution order: named developer → compound's developer → named area →
    None (caller falls back to a market-wide default).
    """
    intent = local_intent_extractor.extract_intent(message or "")
    area_key = intent.get("area")
    entities = local_intent_extractor.extract_entities(message or "")

    # 1) A named developer with a history series.
    for name, kind in entities:
        if kind == "developer":
            series = _developer_series(name, area_key)
            if series and len(series) >= 2:
                return {
                    "label_en": name,
                    "label_ar": _display_name(name, "ar"),
                    "series": series,
                    "basis": "developer",
                }

    # 2) A named compound → resolve its developer → series.
    for name, kind in entities:
        if kind == "compound":
            dev = _compound_to_developer(name)
            if dev:
                series = _developer_series(dev, area_key)
                if series and len(series) >= 2:
                    return {
                        "label_en": name,
                        "label_ar": _display_name(name, "ar"),
                        "series": series,
                        "basis": "compound_via_developer",
                    }

    # 3) Fall back to the area's own price history.
    area_history = _AREA_CANON_TO_HISTORY.get(area_key or "")
    if area_history and area_history in AREA_PRICE_HISTORY:
        return {
            "label_en": area_history,
            "label_ar": _AREA_LABEL_AR.get(area_key or "", area_history),
            "series": {int(k): float(v) for k, v in AREA_PRICE_HISTORY[area_history].items()},
            "basis": "area",
        }

    return None


def build_appreciation_payload(message: str, requested_language: str) -> dict[str, Any]:
    """Deterministic price-growth answer (total % + CAGR) over the requested
    horizon, computed from the hardcoded 2021-2026 market history tables."""
    language = _resolve_language(requested_language, message)
    payload = _base_payload(language)
    payload["response_type"] = "free_appreciation"
    payload["showing_strategy"] = "FREE_APPRECIATION"
    payload["ui_primitive_descriptor"] = "free_appreciation"

    resolved = _resolve_appreciation_series(message)
    if not resolved:
        if language == "ar":
            payload["response"] = (
                "محتاج تحدد المطور أو الكمبوند أو المنطقة عشان أحسبلك معدل زيادة السعر. "
                "مثال: «معدل زيادة سعر سوديك في التجمع آخر 5 سنين»."
            )
        else:
            payload["response"] = (
                "Tell me the developer, compound, or area and I'll compute the price-growth rate. "
                "For example: \"Sodic price appreciation in New Cairo over the last 5 years\"."
            )
        payload["primitive_data"] = {"reason": "unresolved_subject"}
        payload["lead_score"] = 18
        payload["readiness_score"] = 18
        return payload

    series = resolved["series"]
    years_sorted = sorted(series.keys())
    end_year = years_sorted[-1]
    n = _extract_years_window(message)
    start_year = max(years_sorted[0], end_year - n)
    # Snap start to an available year.
    if start_year not in series:
        candidates = [y for y in years_sorted if y >= start_year]
        start_year = candidates[0] if candidates else years_sorted[0]

    start_psm = series[start_year]
    end_psm = series[end_year]
    span = max(1, end_year - start_year)

    total_growth_pct = (end_psm / start_psm - 1.0) * 100.0 if start_psm else 0.0
    cagr_pct = ((end_psm / start_psm) ** (1.0 / span) - 1.0) * 100.0 if start_psm else 0.0
    multiple = (end_psm / start_psm) if start_psm else 0.0

    label = resolved["label_ar"] if language == "ar" else resolved["label_en"]
    start_txt = _format_psm(start_psm, language)
    end_txt = _format_psm(end_psm, language)

    if language == "ar":
        response = (
            f"📈 معدل زيادة سعر {label} خلال آخر {span} سنين:\n"
            f"• إجمالي الزيادة: حوالي +{total_growth_pct:,.0f}% "
            f"(من {start_txt} سنة {start_year} إلى {end_txt} سنة {end_year}).\n"
            f"• معدل سنوي مركّب (CAGR): حوالي {cagr_pct:,.0f}% في السنة — "
            f"يعني السعر اتضاعف حوالي {multiple:,.1f} مرة.\n"
            f"• المصدر: متوسط أسعار السوق للمتر (تقديري — للأرقام الرسمية راجع السجل)."
        )
    else:
        response = (
            f"📈 {label} price appreciation over the last {span} years:\n"
            f"• Total growth: about +{total_growth_pct:,.0f}% "
            f"(from {start_txt} in {start_year} to {end_txt} in {end_year}).\n"
            f"• Compound annual growth (CAGR): about {cagr_pct:,.0f}% per year — "
            f"roughly {multiple:,.1f}× over the period.\n"
            f"• Source: market average price/m² (indicative — verify against the registry)."
        )

    payload["response"] = response
    payload["primitive_data"] = {
        "subject": resolved["label_en"],
        "basis": resolved["basis"],
        "start_year": start_year,
        "end_year": end_year,
        "start_price_per_sqm": round(start_psm, 2),
        "end_price_per_sqm": round(end_psm, 2),
        "total_growth_pct": round(total_growth_pct, 1),
        "cagr_pct": round(cagr_pct, 1),
        "series": {str(y): round(series[y], 2) for y in years_sorted},
    }
    payload["ui_actions"] = [
        {
            "type": "price_trend",
            "data": {
                "label": resolved["label_en"],
                "points": [{"year": y, "price_per_sqm": round(series[y], 2)} for y in years_sorted],
                "total_growth_pct": round(total_growth_pct, 1),
                "cagr_pct": round(cagr_pct, 1),
            },
        }
    ]

    # Forward-looking teaser (zero-token): run the scientific forecast engine on the
    # SAME resolved series (pure-compute, no DB). Free users see direction + a single
    # 12-month % + a confidence label; the full curve is premium. Never breaks the
    # backward-looking answer if the engine errors.
    try:
        from datetime import date as _date
        from app.ai_engine.price_forecast_engine import compute_forecast, SeriesPoint

        _loc = resolved["label_en"] if resolved["basis"] == "area" else ""
        _pts = [SeriesPoint(_date(int(y), 1, 1), float(series[y]), "analytical_engine_seed_2026")
                for y in years_sorted]
        _fc = compute_forecast(
            entity=resolved["label_en"], level=resolved["basis"],
            own_points=_pts, location=_loc, horizons=(12,),
        )
        if _fc.get("headline_12mo_pct") is not None:
            _hp = _fc["headline_12mo_pct"]
            if language == "ar":
                response += (
                    f"\n\n🔮 توقع تقريبي للـ 12 شهر القادمة: "
                    f"{'+' if _hp > 0 else ''}{_hp}% (استرشادي). "
                    f"المنحنى الكامل (6/12/24 شهر) متاح في الباقة المدفوعة."
                )
            else:
                response += (
                    f"\n\n🔮 Indicative 12-month outlook: "
                    f"{'+' if _hp > 0 else ''}{_hp}%. "
                    f"The full 6/12/24-month curve is available on premium."
                )
            payload["response"] = response
        payload["ui_actions"].append({
            "type": "forecast_teaser",
            "data": {
                "entity": _fc["entity"],
                "level": _fc["level"],
                "trend_direction": _fc.get("trend_direction"),
                "headline_12mo_pct": _fc.get("headline_12mo_pct"),
                "confidence_label": _fc.get("confidence_tier"),
                "base_price_per_m2": _fc.get("base_price_per_m2"),
                "disclaimer": _fc.get("disclaimer"),
                "locked": True,
                "upsell": {
                    "sku_options": [
                        {"sku": "single_compound", "price_egp": 99},
                        {"sku": "premium_monthly", "price_egp": 299},
                    ],
                },
            },
        })
    except Exception:
        logger.warning("forecast teaser skipped (non-fatal)", exc_info=True)

    payload["lead_score"] = 28
    payload["readiness_score"] = 28
    return payload


# ─────────────────────────────────────────────────────────────────────────────
# Multi-entity comparison handler (best price per developer / per compound)
# ─────────────────────────────────────────────────────────────────────────────

def _price_exprs():
    """developer_price / resale_price expressions that fall back to
    sale_type+price when the split columns are NULL — so the comparison works
    on freshly-scraped rows that predate the ingestion split fix."""
    sale_type_l = func.lower(func.coalesce(Property.sale_type, ""))
    developer_price_expr = func.coalesce(
        Property.developer_price,
        case(
            (
                or_(sale_type_l.like("%developer%"), sale_type_l.like("%nawy now%")),
                Property.price,
            ),
            else_=None,
        ),
    )
    resale_price_expr = func.coalesce(
        Property.resale_price,
        case((sale_type_l.like("%resale%"), Property.price), else_=None),
    )
    return developer_price_expr, resale_price_expr


def _entity_filter(name: str, kind: str):
    pattern = f"%{name}%"
    if kind == "developer":
        clauses = [Property.developer.ilike(pattern), Property.compound.ilike(pattern)]
        flagship = DEVELOPER_TO_COMPOUNDS.get(name)
        if flagship:
            clauses.append(Property.compound.in_(flagship))
        return or_(*clauses)
    return or_(
        Property.compound.ilike(pattern),
        Property.developer.ilike(pattern),
        Property.title.ilike(pattern),
    )


def _criteria_clauses(message: str) -> tuple[list, dict[str, Any]]:
    """Build optional area/type/bedroom filters from the query so the
    cross-entity comparison is apples-to-apples (e.g. New Cairo, 2BR apartment)."""
    intent = local_intent_extractor.extract_intent(message or "")
    clauses: list = []
    meta: dict[str, Any] = {"area": intent.get("area"), "property_type": intent.get("property_type")}

    area_key = intent.get("area")
    if area_key:
        patterns = _AREA_SQL_PATTERNS.get(area_key, [area_key])
        area_predicates = []
        for p in patterns:
            like = f"%{p}%"
            area_predicates.extend(
                [Property.location.ilike(like), Property.title.ilike(like), Property.compound.ilike(like)]
            )
        if area_predicates:
            clauses.append(or_(*area_predicates))

    ptype = (intent.get("property_type") or "").lower().strip()
    if ptype == "studio":
        clauses.append(
            or_(func.lower(func.coalesce(Property.type, "")).like("%studio%"), Property.bedrooms.in_([0, 1]))
        )
    elif ptype:
        clauses.append(func.lower(func.coalesce(Property.type, "")).like(f"%{ptype}%"))

    # Bedrooms — reuse the intent extractor's room count when present.
    rooms = intent.get("rooms")
    bedrooms: list[int] = []
    norm = local_intent_extractor._normalize_query(message or "")
    for val in re.findall(r"(\d+)\s*(?:bed(?:room)?s?|غرف|غرفه)", norm):
        try:
            b = int(val)
            if b > 0 and b not in bedrooms:
                bedrooms.append(b)
        except (TypeError, ValueError):
            pass
    if rooms and rooms not in bedrooms:
        bedrooms.append(int(rooms))
    if bedrooms and ptype != "studio":
        clauses.append(Property.bedrooms.is_not(None))
        clauses.append(Property.bedrooms.in_(bedrooms))
    meta["bedrooms"] = bedrooms
    return clauses, meta


async def _aggregate_entity(
    db: AsyncSession, name: str, kind: str, criteria_clauses: list
) -> dict[str, Any]:
    dev_expr, res_expr = _price_exprs()
    stmt = select(
        func.avg(dev_expr).label("dev_avg"),
        func.min(dev_expr).label("dev_min"),
        func.count(dev_expr).label("dev_n"),
        func.avg(res_expr).label("res_avg"),
        func.min(res_expr).label("res_min"),
        func.count(res_expr).label("res_n"),
    ).where(
        Property.is_available.is_(True),
        _entity_filter(name, kind),
        *criteria_clauses,
    )
    row = (await db.execute(stmt)).first()

    def _f(v):
        return float(v) if v is not None else None

    dev_avg = _f(row.dev_avg) if row else None
    res_avg = _f(row.res_avg) if row else None
    gap = (dev_avg - res_avg) if (dev_avg is not None and res_avg is not None) else None
    return {
        "name": name,
        "kind": kind,
        "dev_avg": dev_avg,
        "dev_min": _f(row.dev_min) if row else None,
        "dev_n": int(row.dev_n or 0) if row else 0,
        "res_avg": res_avg,
        "res_min": _f(row.res_min) if row else None,
        "res_n": int(row.res_n or 0) if row else 0,
        "gap_egp": gap,
    }


def _entity_card(entry: dict[str, Any], language: str, *, best: bool, locked: bool) -> dict[str, Any]:
    name = entry["name"]
    # Headline price for the card: the cheapest concrete price we can show.
    price = entry.get("dev_min") or entry.get("res_min") or entry.get("dev_avg") or 0.0
    card = {
        "id": f"entity:{name}",
        "title": _display_name(name, language),
        "location": name,
        "compound": name if entry["kind"] == "compound" else None,
        "developer": name if entry["kind"] == "developer" else None,
        "price": float(price or 0.0),
        "developer_avg_price": entry.get("dev_avg"),
        "developer_min_price": entry.get("dev_min"),
        "resale_avg_price": entry.get("res_avg"),
        "resale_min_price": entry.get("res_min"),
        "resale_price": entry.get("res_min") or entry.get("res_avg"),
        "market_price": entry.get("dev_avg"),
        "savings_egp": entry.get("gap_egp"),
        "sample_size": entry.get("dev_n", 0) + entry.get("res_n", 0),
        "tags": (["أفضل-سعر"] if language == "ar" else ["best-price"]) if best else [],
        "locked": locked,
    }
    if locked:
        card["lock_reason"] = "premium_required"
    return card


def _entity_line(entry: dict[str, Any], language: str) -> str:
    name = _display_name(entry["name"], language)
    parts: list[str] = []
    if entry.get("dev_avg") is not None:
        if language == "ar":
            parts.append(f"متوسط سعر المطور {_format_egp(entry['dev_avg'], language)}")
            if entry.get("dev_min") is not None:
                parts.append(f"أقل سعر مطور {_format_egp(entry['dev_min'], language)}")
        else:
            parts.append(f"avg developer price {_format_egp(entry['dev_avg'], language)}")
            if entry.get("dev_min") is not None:
                parts.append(f"lowest developer {_format_egp(entry['dev_min'], language)}")
    if entry.get("res_min") is not None:
        parts.append(
            (f"أرخص resale {_format_egp(entry['res_min'], language)}")
            if language == "ar"
            else f"cheapest resale {_format_egp(entry['res_min'], language)}"
        )
    if not parts:
        return (
            f"• {name}: لا توجد بيانات سعر كافية حاليًا."
            if language == "ar"
            else f"• {name}: not enough price data yet."
        )
    sep = "؛ " if language == "ar" else "; "
    return f"• {name}: " + sep.join(parts) + "."


async def build_comparison_payload(
    db: AsyncSession, message: str, requested_language: str
) -> Optional[dict[str, Any]]:
    """Compare developer (and resale) prices across 2-3 named developers/compounds.

    Returns None if fewer than two distinct entities resolve, so the caller can
    fall back to the single best-price path.
    """
    language = _resolve_language(requested_language, message)
    entities = local_intent_extractor.extract_entities(message or "")

    # Dedupe by canonical name, keep order, cap at 3.
    seen: set[str] = set()
    deduped: list[tuple[str, str]] = []
    for name, kind in entities:
        if name not in seen:
            seen.add(name)
            deduped.append((name, kind))
    deduped = deduped[:3]
    if len(deduped) < 2:
        return None

    criteria_clauses, meta = _criteria_clauses(message)
    results = [await _aggregate_entity(db, name, kind, criteria_clauses) for name, kind in deduped]

    # Entities with any developer price data are "rankable" on developer price.
    priced = [r for r in results if r.get("dev_avg") is not None]

    payload = _base_payload(language)
    payload["response_type"] = "free_comparison"
    payload["showing_strategy"] = "FREE_COMPARISON"
    payload["ui_primitive_descriptor"] = "free_price_comparison"
    payload["lead_score"] = 32
    payload["readiness_score"] = 32

    if not priced:
        names = "، ".join(_display_name(r["name"], language) for r in results) if language == "ar" \
            else ", ".join(r["name"] for r in results)
        payload["response"] = (
            f"قارنت {names} بس مفيش بيانات سعر كافية بالشروط دي دلوقتي. "
            f"جرب تشيل شرط (المنطقة أو عدد الغرف) أو غيّر الأسماء."
            if language == "ar"
            else f"I compared {names} but there isn't enough price data under these filters. "
                 f"Try removing a filter (area or bedrooms) or changing the names."
        )
        payload["properties"] = [_entity_card(r, language, best=False, locked=False) for r in results]
        payload["primitive_data"] = {"entities": results, "criteria": meta, "result": "insufficient_data"}
        return payload

    # Winner on developer price = the cheapest average developer price ("best
    # price per developer/compound"). Ranking is ascending on dev_avg.
    priced.sort(key=lambda r: r["dev_avg"])
    winner = priced[0]
    # Secondary signal: biggest resale gap (where you save most vs. developer).
    gapped = [r for r in results if r.get("gap_egp") is not None and r["gap_egp"] > 0]
    gapped.sort(key=lambda r: r["gap_egp"], reverse=True)
    best_gap = gapped[0] if gapped else None

    # Criteria label for the headline.
    crit_bits: list[str] = []
    if meta.get("area"):
        crit_bits.append(
            _AREA_LABEL_AR.get(meta["area"], meta["area"]) if language == "ar"
            else meta["area"].title()
        )
    if meta.get("property_type"):
        crit_bits.append(_type_label(meta["property_type"], language))
    if meta.get("bedrooms"):
        beds = " أو ".join(str(b) for b in meta["bedrooms"]) if language == "ar" \
            else " or ".join(str(b) for b in meta["bedrooms"])
        crit_bits.append((f"{beds} غرف") if language == "ar" else f"{beds}BR")
    crit_label = ("، ".join(crit_bits) if language == "ar" else ", ".join(crit_bits))

    lines = [_entity_line(r, language) for r in results]
    win_name = _display_name(winner["name"], language)

    if language == "ar":
        header = (
            f"📊 مقارنة سعر المطور بين {len(results)} "
            + (f"({crit_label}):" if crit_label else "مطورين/كمبوندات:")
        )
        verdict = f"🏆 الأوفر في سعر المطور: {win_name} بمتوسط {_format_egp(winner['dev_avg'], language)}."
        if best_gap and best_gap["name"] != winner["name"]:
            verdict += (
                f"\n💡 أكبر فرصة resale تحت سعر المطور: {_display_name(best_gap['name'], language)} "
                f"بفرق حوالي {_format_egp(best_gap['gap_egp'], language)} لصالحك."
            )
    else:
        header = (
            f"📊 Developer-price comparison across {len(results)} "
            + (f"({crit_label}):" if crit_label else "developers/compounds:")
        )
        verdict = f"🏆 Cheapest developer price: {win_name} at avg {_format_egp(winner['dev_avg'], language)}."
        if best_gap and best_gap["name"] != winner["name"]:
            verdict += (
                f"\n💡 Biggest resale gap below developer pricing: {best_gap['name']} "
                f"— about {_format_egp(best_gap['gap_egp'], language)} in your favor."
            )

    delivery = get_delivery_track_record(winner["name"])
    if delivery:
        if language == "ar":
            verdict += f"\n📦 سجل تسليم {win_name}: {delivery['on_time_pct']}% في الموعد."
        else:
            verdict += f"\n📦 {winner['name']} delivery record: {delivery['on_time_pct']}% on time."

    payload["response"] = "\n".join([header, *lines, verdict])

    # Cards: winner first (unlocked), the rest as concrete cards too (free path
    # shows the full comparison; this is the product's core free value).
    ordered = [winner] + [r for r in results if r["name"] != winner["name"]]
    payload["properties"] = [
        _entity_card(r, language, best=(r["name"] == winner["name"]), locked=False) for r in ordered
    ]
    payload["ui_actions"] = [
        {
            "type": "price_comparison_multi",
            "data": {
                "entities": [
                    {
                        "name": r["name"],
                        "developer_avg_price": r["dev_avg"],
                        "developer_min_price": r["dev_min"],
                        "resale_avg_price": r["res_avg"],
                        "resale_min_price": r["res_min"],
                        "gap_egp": r["gap_egp"],
                    }
                    for r in results
                ],
                "winner": winner["name"],
                "criteria": meta,
            },
        }
    ]
    payload["primitive_data"] = {
        "entities": results,
        "winner": winner["name"],
        "best_resale_gap": best_gap["name"] if best_gap else None,
        "criteria": meta,
        "comparison_basis": "developer_price_avg_with_resale_gap",
    }
    return payload
