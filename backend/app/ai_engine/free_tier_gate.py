"""
Free-tier conversion gate utilities.

Extracts exactly one high-signal anomaly to create a give-to-get teaser.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.ai_engine.local_intent import local_intent_extractor
from app.models import Property


_ARABIC_TEXT_RE = re.compile(r"[\u0600-\u06FF]")
_ARABIC_DIGITS_MAP = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_ARABIC_AREA_LABELS = {
    "new cairo": "القاهرة الجديدة / التجمع",
    "sheikh zayed": "الشيخ زايد",
    "6th of october": "6 أكتوبر",
    "north coast": "الساحل الشمالي",
    "new capital": "العاصمة الإدارية",
}
_AREA_SQL_PATTERNS = {
    "new cairo": [
        "new cairo",
        "fifth settlement",
        "5th settlement",
        "tagamoa",
        "tagamo3",
        "tagamo3a",
        "cairo festival",
        "التجمع",
        "القاهرة الجديدة",
    ],
    "sheikh zayed": ["sheikh zayed", "zayed", "زايد", "الشيخ زايد"],
    "6th of october": ["6th of october", "6 october", "october", "اكتوبر", "أكتوبر"],
    "north coast": ["north coast", "sahel", "الساحل", "الساحل الشمالي"],
    "new capital": ["new capital", "capital", "العاصمة", "العاصمة الادارية", "العاصمة الإدارية"],
}
_TYPE_LABELS_AR = {
    "apartment": "شقة",
    "villa": "فيلا",
    "townhouse": "تاون هاوس",
    "twinhouse": "توين هاوس",
    "duplex": "دوبلكس",
    "studio": "استوديو",
}
_FILTER_LABELS_AR = {
    "bedrooms": "عدد الغرف",
    "property_type": "نوع الوحدة",
    "area": "المنطقة",
    "compound": "الكمبوند/المطور",
}
_FILTER_LABELS_EN = {
    "bedrooms": "bedrooms",
    "property_type": "property type",
    "area": "area",
    "compound": "compound/developer",
}


def _contains_arabic(text: str) -> bool:
    return bool(text and _ARABIC_TEXT_RE.search(text))


def _resolve_chat_language(requested_language: str, message: str) -> str:
    requested = (requested_language or "auto").lower()
    if requested in {"ar", "en"}:
        return requested
    return "ar" if _contains_arabic(message or "") else "en"


def _format_egp(value: float | int | None, language: str) -> str:
    try:
        amount = float(value or 0)
    except (TypeError, ValueError):
        amount = 0.0

    if language == "ar":
        return f"{amount:,.0f} ج.م"
    return f"{amount:,.0f} EGP"


def _extract_bedroom_options(message: str, fallback_room: Optional[int]) -> list[int]:
    normalized = (message or "").translate(_ARABIC_DIGITS_MAP).lower()
    options: list[int] = []

    range_with_unit = re.search(
        r"(\d+)\s*(?:-|to|or|او|أو|الى|إلى|/)\s*(\d+)\s*(?:bed(?:room)?s?|غرف|غرفة|غرفه)",
        normalized,
    )
    if range_with_unit:
        options.extend([int(range_with_unit.group(1)), int(range_with_unit.group(2))])

    all_units = re.findall(r"(\d+)\s*(?:bed(?:room)?s?|غرف|غرفة|غرفه)", normalized)
    for val in all_units:
        options.append(int(val))

    if fallback_room and fallback_room > 0:
        options.append(int(fallback_room))

    deduped: list[int] = []
    for room in options:
        if room > 0 and room not in deduped:
            deduped.append(room)
    return deduped


def _studio_requested(message: str, extracted_type: Optional[str]) -> bool:
    if extracted_type == "studio":
        return True
    normalized = (message or "").lower()
    return any(token in normalized for token in ("studio", "استوديو", "ستوديو"))


def _build_criteria_text(criteria: dict[str, Any], language: str) -> str:
    parts: list[str] = []
    if language == "ar":
        if criteria.get("area"):
            area_label = _ARABIC_AREA_LABELS.get(criteria["area"], criteria["area"])
            parts.append(f"المنطقة: {area_label}")
        if criteria.get("compound"):
            parts.append(f"الكمبوند/المطور: {criteria['compound']}")
        if criteria.get("property_type"):
            parts.append(f"النوع: {_TYPE_LABELS_AR.get(criteria['property_type'], criteria['property_type'])}")
        if criteria.get("studio"):
            parts.append("الوحدة: استوديو")
        elif criteria.get("bedrooms"):
            beds = " أو ".join(str(v) for v in criteria["bedrooms"])
            parts.append(f"الغرف: {beds}")
        return " | ".join(parts)

    if criteria.get("area"):
        parts.append(f"area={criteria['area']}")
    if criteria.get("compound"):
        parts.append(f"compound/developer={criteria['compound']}")
    if criteria.get("property_type"):
        parts.append(f"type={criteria['property_type']}")
    if criteria.get("studio"):
        parts.append("unit=studio")
    elif criteria.get("bedrooms"):
        beds = " or ".join(str(v) for v in criteria["bedrooms"])
        parts.append(f"bedrooms={beds}")
    return " | ".join(parts)


def _is_filter_active(criteria: dict[str, Any], field: str) -> bool:
    if field == "bedrooms":
        return bool(criteria.get("bedrooms"))
    if field == "property_type":
        return bool(criteria.get("property_type")) or bool(criteria.get("studio"))
    if field == "area":
        return bool(criteria.get("area"))
    if field == "compound":
        return bool(criteria.get("compound"))
    return False


def _relax_field(criteria: dict[str, Any], field: str) -> dict[str, Any]:
    relaxed = dict(criteria)
    if field == "bedrooms":
        relaxed["bedrooms"] = []
    elif field == "property_type":
        relaxed["property_type"] = None
        relaxed["studio"] = False
    elif field == "area":
        relaxed["area"] = None
    elif field == "compound":
        relaxed["compound"] = None
    return relaxed


def _build_relaxation_plan(criteria: dict[str, Any]) -> list[tuple[dict[str, Any], list[str]]]:
    # Progressive one-way relaxation: preserve as many user filters as possible.
    plan_fields = ["bedrooms", "property_type", "area", "compound"]
    variants: list[tuple[dict[str, Any], list[str]]] = []
    current = dict(criteria)
    removed: list[str] = []

    for field in plan_fields:
        if not _is_filter_active(current, field):
            continue
        current = _relax_field(current, field)
        removed = [*removed, field]
        variants.append((dict(current), list(removed)))

    return variants


def _render_removed_filters(removed_filters: list[str], language: str) -> str:
    if not removed_filters:
        return ""
    labels = _FILTER_LABELS_AR if language == "ar" else _FILTER_LABELS_EN
    translated = [labels.get(field, field) for field in removed_filters]
    separator = "، " if language == "ar" else ", "
    return separator.join(translated)


def _build_pivot_marketing_text(
    language: str,
    strict_criteria: dict[str, Any],
    pivot_criteria: dict[str, Any],
    removed_filters: list[str],
    property_card: dict[str, Any],
) -> str:
    strict_text = _build_criteria_text(strict_criteria, language)
    pivot_text = _build_criteria_text(pivot_criteria, language)
    base_text = _build_best_price_text(language, property_card, pivot_criteria)
    removed_text = _render_removed_filters(removed_filters, language)

    if language == "ar":
        intro = ""
        if strict_text:
            intro = f"ما لقيتش تطابق كامل لكل الشروط ({strict_text}). "
        pivot_note = ""
        if removed_text:
            pivot_note = f"عملت Pivot ذكي بتخفيف: {removed_text}. "
        elif pivot_text:
            pivot_note = f"عملت Pivot ذكي لأقرب اختيار ({pivot_text}). "
        return f"{intro}{pivot_note}{base_text}"

    intro = ""
    if strict_text:
        intro = f"No exact match for all strict criteria ({strict_text}). "
    pivot_note = ""
    if removed_text:
        pivot_note = f"I made a smart pivot by relaxing: {removed_text}. "
    elif pivot_text:
        pivot_note = f"I made a smart pivot to the nearest criteria set ({pivot_text}). "
    return f"{intro}{pivot_note}{base_text}"


def _serialize_best_price_property(
    prop: Property,
    resale_price: float,
    developer_avg: float,
    savings_egp: float,
) -> dict[str, Any]:
    savings_pct = (savings_egp / developer_avg * 100.0) if developer_avg else None
    return {
        "id": prop.id,
        "title": prop.title,
        "location": prop.location or "Unknown",
        "compound": prop.compound,
        "developer": prop.developer,
        "price": float(resale_price),
        "market_price": float(developer_avg),
        "resale_price": float(resale_price),
        "developer_avg_price": float(developer_avg),
        "savings_egp": float(savings_egp),
        "savings_pct": float(savings_pct) if savings_pct is not None else None,
        "price_per_sqm": float(prop.price_per_sqm) if prop.price_per_sqm is not None else None,
        "size_sqm": prop.size_sqm,
        "bedrooms": prop.bedrooms,
        "type": prop.type,
        "image_url": prop.image_url,
        "sale_type": prop.sale_type,
        "comparison": {
            "resale_price": float(resale_price),
            "developer_avg_price": float(developer_avg),
            "savings_egp": float(savings_egp),
            "savings_pct": float(savings_pct) if savings_pct is not None else None,
        },
    }


def _build_best_price_text(
    language: str,
    property_card: dict[str, Any],
    criteria: dict[str, Any],
) -> str:
    title = property_card.get("title") or "Selected Property"
    criteria_text = _build_criteria_text(criteria, language)
    resale_text = _format_egp(property_card.get("resale_price"), language)
    developer_text = _format_egp(property_card.get("developer_avg_price"), language)
    savings_text = _format_egp(property_card.get("savings_egp"), language)

    if language == "ar":
        prefix = f"أحسن سعر مطابق لطلبك ({criteria_text})" if criteria_text else "أحسن سعر مطابق لطلبك"
        return (
            f"{prefix}: {title}. "
            f"سعر إعادة البيع: {resale_text}. "
            f"متوسط سعر المطور لنفس النوع: {developer_text}. "
            f"التوفير لصالحك: {savings_text}."
        )

    prefix = f"Best matched lowest price ({criteria_text})" if criteria_text else "Best matched lowest price"
    return (
        f"{prefix}: {title}. "
        f"Resale price: {resale_text}. "
        f"Average developer price for the same type: {developer_text}. "
        f"Your savings: {savings_text}."
    )


async def _fetch_best_price_candidate(
    db: AsyncSession,
    criteria: dict[str, Any],
    *,
    require_positive_savings: bool,
) -> Optional[dict[str, Any]]:
    sale_type_text = func.lower(func.coalesce(Property.sale_type, ""))
    resale_price_expr = func.coalesce(
        Property.resale_price,
        case((sale_type_text.like("%resale%"), Property.price), else_=None),
        Property.price,
    )

    resale_eligible = or_(
        Property.resale_price.is_not(None),
        sale_type_text.like("%resale%"),
        sale_type_text.like("%nawy now%"),
        sale_type_text == "",
    )

    benchmark_model = aliased(Property)
    benchmark_sale_type = func.lower(func.coalesce(benchmark_model.sale_type, ""))
    developer_price_expr = func.coalesce(
        benchmark_model.developer_price,
        case((benchmark_sale_type.like("%developer%"), benchmark_model.price), else_=None),
    )

    developer_avg_same_compound_type_expr = (
        select(func.avg(developer_price_expr))
        .where(
            benchmark_model.is_available.is_(True),
            benchmark_model.compound.is_not(None),
            benchmark_model.compound == Property.compound,
            func.lower(func.coalesce(benchmark_model.type, ""))
            == func.lower(func.coalesce(Property.type, "")),
            developer_price_expr.is_not(None),
        )
        .correlate(Property)
        .scalar_subquery()
    )

    developer_avg_same_compound_expr = (
        select(func.avg(developer_price_expr))
        .where(
            benchmark_model.is_available.is_(True),
            benchmark_model.compound.is_not(None),
            benchmark_model.compound == Property.compound,
            developer_price_expr.is_not(None),
        )
        .correlate(Property)
        .scalar_subquery()
    )

    developer_avg_same_developer_type_expr = (
        select(func.avg(developer_price_expr))
        .where(
            benchmark_model.is_available.is_(True),
            benchmark_model.developer.is_not(None),
            benchmark_model.developer == Property.developer,
            func.lower(func.coalesce(benchmark_model.type, ""))
            == func.lower(func.coalesce(Property.type, "")),
            developer_price_expr.is_not(None),
        )
        .correlate(Property)
        .scalar_subquery()
    )

    own_developer_price_expr = func.coalesce(
        Property.developer_price,
        case((sale_type_text.like("%developer%"), Property.price), else_=None),
    )

    developer_avg_expr = func.coalesce(
        developer_avg_same_compound_type_expr,
        developer_avg_same_compound_expr,
        developer_avg_same_developer_type_expr,
        own_developer_price_expr,
    )

    savings_expr = developer_avg_expr - resale_price_expr

    stmt = (
        select(
            Property,
            resale_price_expr.label("resale_price_effective"),
            developer_avg_expr.label("developer_avg_price"),
            savings_expr.label("savings_egp"),
        )
        .where(
            Property.is_available.is_(True),
            resale_eligible,
            ~sale_type_text.like("%developer%"),
            resale_price_expr.is_not(None),
            resale_price_expr > 0,
            developer_avg_expr.is_not(None),
        )
    )

    if criteria.get("area"):
        area_key = criteria["area"]
        area_patterns = _AREA_SQL_PATTERNS.get(area_key, [area_key])
        area_predicates = []
        for pattern in area_patterns:
            like_pattern = f"%{pattern}%"
            area_predicates.extend(
                [
                    Property.location.ilike(like_pattern),
                    Property.title.ilike(like_pattern),
                    Property.compound.ilike(like_pattern),
                ]
            )
        if area_predicates:
            stmt = stmt.where(or_(*area_predicates))

    if criteria.get("compound"):
        pattern = f"%{criteria['compound']}%"
        stmt = stmt.where(
            or_(
                Property.compound.ilike(pattern),
                Property.developer.ilike(pattern),
                Property.title.ilike(pattern),
            )
        )

    normalized_type = (criteria.get("property_type") or "").lower().strip()
    if criteria.get("studio"):
        stmt = stmt.where(
            or_(
                func.lower(func.coalesce(Property.type, "")).like("%studio%"),
                Property.bedrooms.in_([0, 1]),
            )
        )
    elif normalized_type:
        stmt = stmt.where(
            func.lower(func.coalesce(Property.type, "")).like(f"%{normalized_type}%")
        )

    bedrooms = criteria.get("bedrooms") or []
    if bedrooms and not criteria.get("studio"):
        stmt = stmt.where(Property.bedrooms.is_not(None), Property.bedrooms.in_(bedrooms))

    if require_positive_savings:
        stmt = stmt.where(savings_expr > 0)

    stmt = stmt.order_by(
        resale_price_expr.asc(),
        savings_expr.desc(),
        Property.id.asc(),
    ).limit(1)

    row = (await db.execute(stmt)).first()
    if not row:
        return None

    prop, resale_price, developer_avg, savings_egp = row
    return {
        "property": prop,
        "resale_price": float(resale_price or 0),
        "developer_avg": float(developer_avg or 0),
        "savings_egp": float(savings_egp or 0),
    }


async def _fetch_pivot_candidate(
    db: AsyncSession,
    strict_criteria: dict[str, Any],
) -> Optional[dict[str, Any]]:
    for relaxed_criteria, removed_filters in _build_relaxation_plan(strict_criteria):
        candidate = await _fetch_best_price_candidate(
            db,
            relaxed_criteria,
            require_positive_savings=True,
        )
        used_positive_savings = True
        if not candidate:
            used_positive_savings = False
            candidate = await _fetch_best_price_candidate(
                db,
                relaxed_criteria,
                require_positive_savings=False,
            )
        if candidate:
            candidate["criteria"] = relaxed_criteria
            candidate["removed_filters"] = removed_filters
            candidate["used_positive_savings"] = used_positive_savings
            return candidate
    return None


async def build_best_price_free_payload(
    db: AsyncSession,
    message: str,
    requested_language: str,
) -> dict[str, Any]:
    """
    Zero-token free-path dispatcher.

    Classifies the user's message and routes it to the right deterministic
    handler so a free user gets the correct *shape* of answer:

      * appreciation / growth-over-time  → price-trend handler (CAGR + total %)
      * 2-3 named developers/compounds   → cross-entity developer-price comparison
      * everything else                  → single best resale-vs-developer match

    Both /api/v1/chat and /api/chat/stream call this function, so both inherit
    the routing. Lazy import of the router avoids any import-time cycle.
    """
    # Lazy import: free_pricing_router pulls in analytical_engine; importing it
    # at module scope risks a cycle through free_tier_gate's many importers.
    from app.ai_engine import free_pricing_router

    kind = free_pricing_router.classify_free_intent(message or "")
    if kind == "appreciation":
        return free_pricing_router.build_appreciation_payload(message or "", requested_language)
    if kind == "compare":
        comparison = await free_pricing_router.build_comparison_payload(
            db, message or "", requested_language
        )
        if comparison is not None:
            return comparison
        # Fewer than two entities actually resolved — fall through to best price.

    return await _build_best_price_match_payload(db, message, requested_language)


async def _build_best_price_match_payload(
    db: AsyncSession,
    message: str,
    requested_language: str,
) -> dict[str, Any]:
    """
    Build a strict free-tier payload that returns one best (lowest) resale offer
    matching the user's criteria, plus developer-vs-resale comparison.
    """
    language = _resolve_chat_language(requested_language, message)
    intent = local_intent_extractor.extract_intent(message or "")

    criteria = {
        "area": intent.get("area"),
        "compound": intent.get("compound"),
        "property_type": intent.get("property_type"),
        "studio": _studio_requested(message or "", intent.get("property_type")),
        "bedrooms": _extract_bedroom_options(message or "", intent.get("rooms")),
    }

    candidate = await _fetch_best_price_candidate(
        db,
        criteria,
        require_positive_savings=True,
    )
    used_positive_savings = True
    if not candidate:
        used_positive_savings = False
        candidate = await _fetch_best_price_candidate(
            db,
            criteria,
            require_positive_savings=False,
        )

    if not candidate:
        pivot_candidate = await _fetch_pivot_candidate(db, criteria)
        if pivot_candidate:
            pivot_criteria = pivot_candidate["criteria"]
            removed_filters = pivot_candidate["removed_filters"]
            property_card = _serialize_best_price_property(
                pivot_candidate["property"],
                pivot_candidate["resale_price"],
                pivot_candidate["developer_avg"],
                pivot_candidate["savings_egp"],
            )
            response_text = _build_pivot_marketing_text(
                language,
                criteria,
                pivot_criteria,
                removed_filters,
                property_card,
            )
            if not pivot_candidate["used_positive_savings"]:
                if language == "ar":
                    response_text += " ملاحظة: هذا أقرب سعر متاح حتى لو لم يكن أقل من متوسط سعر المطور."
                else:
                    response_text += " Note: this is the nearest available match even when it is not below the developer average."

            return {
                "response": response_text,
                "properties": [property_card],
                "ui_actions": [
                    {
                        "type": "price_comparison",
                        "data": {
                            "resale_price": property_card["resale_price"],
                            "developer_avg_price": property_card["developer_avg_price"],
                            "savings_egp": property_card["savings_egp"],
                            "savings_pct": property_card["savings_pct"],
                        },
                    },
                    {
                        "type": "pivot_notice",
                        "data": {
                            "removed_filters": removed_filters,
                            "strict_criteria": criteria,
                            "pivot_criteria": pivot_criteria,
                        },
                    },
                ],
                "ui_primitive_descriptor": "free_best_price_pivot_match",
                "primitive_data": {
                    "intent": intent,
                    "criteria": criteria,
                    "pivot_criteria": pivot_criteria,
                    "removed_filters": removed_filters,
                    "pivot_applied": True,
                    "result_count": 1,
                    "comparison_basis": "resale_vs_developer_avg_same_compound_type",
                    "used_positive_savings": pivot_candidate["used_positive_savings"],
                },
                "response_type": "free_best_price_pivot",
                "showing_strategy": "FREE_BEST_PRICE_PIVOT",
                "show_upsell": False,
                "upsell_reason": None,
                "lead_score": 24,
                "readiness_score": 24,
                "detected_language": language,
                "suggestions": [],
                "cta_actions": [],
            }

        criteria_text = _build_criteria_text(criteria, language)
        if language == "ar":
            response_text = (
                "لم أجد وحدة مطابقة للشروط الحالية ولا حتى بعد البحث عن أقرب Pivot متاح. "
                "من فضلك عدّل معيارًا واحدًا وسأرجع لك أقل سعر مع مقارنة المطور فورًا."
            )
            if criteria_text:
                response_text = f"المعايير الحالية: {criteria_text}. {response_text}"
        else:
            response_text = (
                "I could not find an exact match or a viable nearest pivot match with the current criteria. "
                "Please relax one filter and I will return the lowest matched resale price with developer comparison."
            )
            if criteria_text:
                response_text = f"Current criteria: {criteria_text}. {response_text}"

        return {
            "response": response_text,
            "properties": [],
            "ui_actions": [],
            "ui_primitive_descriptor": "free_best_price_no_match",
            "primitive_data": {
                "intent": intent,
                "criteria": criteria,
                "result_count": 0,
            },
            "response_type": "free_best_price",
            "showing_strategy": "FREE_BEST_PRICE",
            "show_upsell": False,
            "upsell_reason": None,
            "lead_score": 15,
            "readiness_score": 15,
            "detected_language": language,
            "suggestions": [],
            "cta_actions": [],
        }

    property_card = _serialize_best_price_property(
        candidate["property"],
        candidate["resale_price"],
        candidate["developer_avg"],
        candidate["savings_egp"],
    )

    response_text = _build_best_price_text(language, property_card, criteria)
    if not used_positive_savings:
        if language == "ar":
            response_text += " ملاحظة: السعر المعروض هو الأقل المتاح حاليًا حتى لو لم يكن أقل من متوسط سعر المطور."
        else:
            response_text += " Note: this is the lowest available match even when it is not below the developer average."

    return {
        "response": response_text,
        "properties": [property_card],
        "ui_actions": [
            {
                "type": "price_comparison",
                "data": {
                    "resale_price": property_card["resale_price"],
                    "developer_avg_price": property_card["developer_avg_price"],
                    "savings_egp": property_card["savings_egp"],
                    "savings_pct": property_card["savings_pct"],
                },
            }
        ],
        "ui_primitive_descriptor": "free_best_price_match",
        "primitive_data": {
            "intent": intent,
            "criteria": criteria,
            "result_count": 1,
            "comparison_basis": "resale_vs_developer_avg_same_compound_type",
            "used_positive_savings": used_positive_savings,
        },
        "response_type": "free_best_price",
        "showing_strategy": "FREE_BEST_PRICE",
        "show_upsell": False,
        "upsell_reason": None,
        "lead_score": 30,
        "readiness_score": 30,
        "detected_language": language,
        "suggestions": [],
        "cta_actions": [],
    }


class FreeTierConversionGate:
    @staticmethod
    async def extract_one_anomaly(
        db: AsyncSession,
        *,
        location_filter: Optional[str] = None,
        compound_filter: Optional[str] = None,
    ) -> dict:
        query = (
            select(Property)
            .where(
                Property.is_available.is_(True),
                Property.osool_score.is_not(None),
                Property.bargain_percentage.is_not(None),
                Property.osool_score >= 80,
                Property.bargain_percentage > 0,
            )
            .order_by(Property.osool_score.desc(), Property.bargain_percentage.desc())
        )

        if location_filter:
            query = query.where(Property.location.ilike(f"%{location_filter}%"))
        if compound_filter:
            query = query.where(Property.compound.ilike(f"%{compound_filter}%"))

        row = (await db.execute(query.limit(1))).scalar_one_or_none()
        if not row:
            return {
                "error": "No high-signal anomaly found for the current filters."
            }

        market_avg_price = (
            await db.execute(
                select(func.avg(Property.price))
                .where(
                    Property.is_available.is_(True),
                    Property.location == row.location,
                )
            )
        ).scalar()

        return {
            "property_id": row.id,
            "location": row.location,
            "compound": row.compound,
            "asking_price": float(row.price),
            "market_avg_price": float(market_avg_price) if market_avg_price else None,
            "osool_score": float(row.osool_score),
            "bargain_percentage": float(row.bargain_percentage),
            "why_this_is_a_hook": (
                f"Top anomaly: score={row.osool_score:.1f} with +{row.bargain_percentage:.1f}% potential edge"
            ),
        }


def build_value_sandwich(hook: dict, language: str = "ar") -> str:
    if hook.get("error"):
        return hook["error"]

    if language.lower().startswith("ar"):
        return (
            f"هذه الوحدة في {hook.get('location') or 'المنطقة المحددة'} تبدو أقل من متوسط السوق بنمط غير عادي. "
            f"متوسطنا الإحصائي يشير إلى فرصة محتملة (+{hook['bargain_percentage']:.1f}%). "
            "لو تريد كامل المقارنة وخطة التفاوض وخيارات أقوى بديلة، كمل إلى الاستشارة الموجهة."
        )

    return (
        f"This unit in {hook.get('location') or 'the selected area'} is an outlier versus market norms. "
        f"Our model estimates a potential edge of +{hook['bargain_percentage']:.1f}%. "
        "To unlock full comparables, negotiation plan, and broker-ready alternatives, continue to guided consultation."
    )
