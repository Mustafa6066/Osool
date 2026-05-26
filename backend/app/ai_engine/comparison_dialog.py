"""
Free-path conversation state machine.

Drives the AWAITING_NAMES → VALIDATING → MISSING_DATA → COMPARING → DONE
transitions defined in the plan. State is persisted in the
`free_path_sessions` table keyed by `session_id`.

The single public entry point is `handle_turn(query, session, db)`. It returns
a ChatResponse-compatible dict, identical in shape to what the legacy
`local_router.process_query_async` returned, so callers (and the frontend)
don't need any wire-format changes.
"""
from __future__ import annotations

import re
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_engine import free_path_prompt as copy
from app.ai_engine.comparison_service import (
    best_deals_in_compound,
    compare_compounds,
    similar_compounds,
)
from app.ai_engine.flagship_compounds import (
    get_delivery_track_record,
    list_developer_compounds,
    resolve_to_compound,
    suggest_comparison_names,
)
from app.ai_engine.local_intent import local_intent_extractor
from app.models import FreePathSession


# State constants — mirror the values stored in free_path_sessions.state.
STATE_AWAITING_NAMES = "AWAITING_NAMES"
STATE_VALIDATING = "VALIDATING"
STATE_MISSING_DATA = "MISSING_DATA"
STATE_COMPARING = "COMPARING"
STATE_DONE = "DONE"

MODE_SINGLE = "SINGLE"
MODE_MULTI = "MULTI"

_ARABIC_RE = re.compile(r"[؀-ۿ]")

_DISPLAY_NAME_AR = {
    # Major developers
    "La Vista": "لافيستا",
    "Hassan Allam": "حسن علام",
    "Sodic": "سوديك",
    "Palm Hills": "بالم هيلز",
    "Mountain View": "ماونتن فيو",
    "Hyde Park": "هايد بارك",
    "Sarai": "سراي",
    "ZED East": "زيد إيست",
    "ZED West": "زيد ويست",
    "Emaar": "إعمار",
    "ORA": "أورا",
    "Tatweer Misr": "تطوير مصر",
    "Madinet Masr": "مدينة مصر",
    "Misr Italia": "مصر إيطاليا",
    "Inertia": "إنيرشيا",
    "DM Development": "دي إم للتطوير",
    "City Edge": "سيتي إيدج",
    "New Giza": "نيو جيزة",
    "Dorra": "دورة",
    "Iwan Developments": "إيوان للتطوير",
    # Compounds — New Cairo
    "Swan Lake": "سوان ليك",
    "Hap Town": "هاب تاون",
    "Park View": "بارك فيو",
    "Sodic East": "سوديك إيست",
    "Sodic West": "سوديك ويست",
    "Caesar": "سيزار",
    "Villette": "فيليت",
    "La Vista City": "لافيستا سيتي",
    "Mivida": "ميفيدا",
    "Uptown Cairo": "أبتاون القاهرة",
    "Cairo Gate": "كايرو جيت",
    "Marassi": "مراسي",
    "Silver Sands": "سيلفر ساندز",
    "Bloomfields": "بلومفيلدز",
    "Fouka Bay": "فوكا باي",
    "IL Monte Galala": "إيل مونتي جلالة",
    "Palm Hills New Cairo": "بالم هيلز التجمع",
    "Palm Hills Katameya": "بالم هيلز القطامية",
    "Badya": "بادية",
    "Mountain View iCity": "ماونتن فيو آي سيتي",
    "Mountain View Hyde Park": "ماونتن فيو هايد بارك",
    "Mountain View Aliva": "ماونتن فيو أليفا",
    "Taj City": "تاج سيتي",
    "IL Bosco": "إيل بوسكو",
    "Vinci": "فينشي",
    "Jefaira": "جفيرة",
    "Soleya": "سوليا",
    "Joulz": "جولز",
    "New Alamein Towers": "أبراج العلمين الجديدة",
    "North Edge Towers": "نورث إيدج تاورز",
    "Al Maqsad": "المقصد",
    "Zahya": "زاهية",
    "Hyde Park New Cairo": "هايد بارك التجمع",
    "Hyde Park North Coast": "هايد بارك الساحل الشمالي",
    "La Vista Bay": "لافيستا باي",
    "La Vista Ras El Hekma": "لافيستا رأس الحكمة",
    "El Patio": "إيل باتيو",
    "ZED": "زيد",
    "Iwan": "إيوان",
}


def _is_arabic(text: str) -> bool:
    return bool(text and _ARABIC_RE.search(text))


def _format_egp(value: float) -> str:
    """Format an EGP amount with thousands separators, no decimals."""
    return f"{int(round(value)):,}"


def _fmt_price_short(value: float) -> str:
    """Short price formatter for headlines: 4,200,000 → '4.2M'."""
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.0f}K"
    return str(int(round(value)))


def _confidence_label(tier: str, is_arabic: bool) -> str:
    labels = {
        "high":       ("بيانات موثوقة", "High confidence"),
        "moderate":   ("بيانات متوسطة", "Moderate confidence"),
        "indicative": ("بيانات أولية", "Indicative"),
    }
    ar, en = labels.get(tier, ("", ""))
    return ar if is_arabic else en


def _delivery_track_record_line(developer_name: str, is_arabic: bool) -> str:
    """Return a one-line muted delivery note for the developer, or empty string."""
    record = get_delivery_track_record(developer_name)
    if not record:
        return ""
    pct = record["on_time_pct"]
    notable = record.get("notable", "")
    if is_arabic:
        return f"سجل التسليم: {pct}% في الموعد — {notable}"
    return f"Delivery record: {pct}% on time — {notable}"


def _cta_actions(is_arabic: bool) -> list[dict[str, str]]:
    consultant_label = "تواصل مع مستشار" if is_arabic else "Talk to Consultant"
    premium_label = "فتح الباقة المتقدمة" if is_arabic else "Unlock Premium"
    return [
        {"id": "talk_to_consultant", "label": consultant_label, "type": "consultant"},
        {"id": "unlock_premium", "label": premium_label, "type": "upgrade"},
    ]


def _plain_response(text: str) -> dict[str, Any]:
    """Non-upsell, non-comparison reply (clarifications, redirects, swaps)."""
    return {
        "type": "clarification",
        "response_type": "free_local",
        "text": text,
        "properties": [],
        "show_upsell": False,
        "upsell_reason": None,
        "cta_actions": [],
    }


def _display_name(name: str, is_arabic: bool) -> str:
    if is_arabic:
        return _DISPLAY_NAME_AR.get(name, name)
    return name


def _format_name_list(names: list[str], is_arabic: bool) -> str:
    return ("، " if is_arabic else ", ").join(_display_name(n, is_arabic) for n in names)


def _area_label(area: Optional[str], is_arabic: bool) -> str:
    if is_arabic:
        return copy.AREA_LABEL_AR.get(area or "", area or "")
    return copy.AREA_LABEL_EN.get(area or "", area or "")


def _names_redirect_response(query: str, is_arabic: bool) -> dict[str, Any]:
    intent = local_intent_extractor.extract_intent(query)
    area = intent.get("area")
    suggestions = suggest_comparison_names(area, limit=3)
    if area and suggestions:
        template = copy.FREE_PATH_REDIRECT_WITH_AREA_AR if is_arabic else copy.FREE_PATH_REDIRECT_WITH_AREA_EN
        return _plain_response(template.format(
            area=_area_label(area, is_arabic),
            suggestions=_format_name_list(suggestions, is_arabic),
        ))
    return _plain_response(copy.FREE_PATH_REDIRECT_AR if is_arabic else copy.FREE_PATH_REDIRECT_EN)


def _resolution_note(
    compound_names: list[str],
    resolved_from: Optional[dict[str, str]],
    is_arabic: bool,
) -> str:
    if not resolved_from:
        return ""
    pairs = []
    for compound in compound_names:
        developer = resolved_from.get(compound)
        if developer:
            pairs.append(f"{_display_name(developer, is_arabic)} -> {compound}")
    if not pairs:
        return ""
    prefix = "المقارنة استخدمت: " if is_arabic else "Compared concrete compounds: "
    return prefix + ("، " if is_arabic else ", ").join(pairs)


async def handle_turn(
    query: str,
    session: FreePathSession,
    db: AsyncSession,
) -> dict[str, Any]:
    """
    Public entry point. Mutates `session` in place; the caller is responsible
    for committing the transaction.
    """
    is_arabic = _is_arabic(query)
    state = session.state or STATE_AWAITING_NAMES

    if state == STATE_DONE:
        return _comparison_used_upsell(is_arabic)

    if state == STATE_MISSING_DATA:
        return await _handle_missing_data(query, session, db, is_arabic)

    return await _handle_awaiting_names(query, session, db, is_arabic)


async def _handle_awaiting_names(
    query: str,
    session: FreePathSession,
    db: AsyncSession,
    is_arabic: bool,
) -> dict[str, Any]:
    entities = local_intent_extractor.extract_entities(query)
    comparison_intent = local_intent_extractor.is_comparison_intent(query)

    if not entities:
        return _names_redirect_response(query, is_arabic)

    if len(entities) > 3:
        names = ", ".join(name for name, _ in entities)
        text = (
            copy.TOO_MANY_AR.format(names=names)
            if is_arabic
            else copy.TOO_MANY_EN.format(names=names)
        )
        return _plain_response(text)

    if len(entities) == 1 and entities[0][1] == "developer":
        return await _run_single_developer(entities[0][0], session, db, is_arabic)

    resolved: list[str] = []
    resolved_from: dict[str, str] = {}
    for name, kind in entities:
        if kind == "developer":
            compound = await resolve_to_compound(name, db)
            if compound is None:
                suggestions = list_developer_compounds(name)[:3]
                template = (
                    copy.DEVELOPER_NO_FLAGSHIP_AR if is_arabic
                    else copy.DEVELOPER_NO_FLAGSHIP_EN
                )
                return _plain_response(template.format(
                    developer=name,
                    suggestions=", ".join(suggestions) if suggestions else "—",
                ))
            if compound != name:
                resolved_from[compound] = name
            resolved.append(compound)
        else:
            resolved.append(name)

    # Deduplicate while preserving order.
    seen: set[str] = set()
    deduped: list[str] = []
    for name in resolved:
        if name not in seen:
            seen.add(name)
            deduped.append(name)

    if len(deduped) == 1:
        return await _run_single_compound(deduped[0], session, db, is_arabic)
    return await _run_multi_compound(deduped, session, db, is_arabic, resolved_from)


async def _handle_missing_data(
    query: str,
    session: FreePathSession,
    db: AsyncSession,
    is_arabic: bool,
) -> dict[str, Any]:
    """
    User was asked to swap a compound. We expect exactly one new entity in
    their reply. Anything else → stay in MISSING_DATA and re-prompt.

    Uses session.missing_compound to locate and replace the exact entry that
    failed (CQ1 fix) rather than always replacing candidates[-1].
    """
    entities = local_intent_extractor.extract_entities(query)
    if not entities:
        missing_name = session.missing_compound or "—"
        return _plain_response(
            copy.MISSING_RESALE_AR.format(compound=missing_name)
            if is_arabic else copy.MISSING_RESALE_EN.format(compound=missing_name)
        )

    name, kind = entities[0]
    if kind == "developer":
        replacement = await resolve_to_compound(name, db)
        if replacement is None:
            suggestions = list_developer_compounds(name)[:3]
            template = (
                copy.DEVELOPER_NO_FLAGSHIP_AR if is_arabic
                else copy.DEVELOPER_NO_FLAGSHIP_EN
            )
            return _plain_response(template.format(
                developer=name,
                suggestions=", ".join(suggestions) if suggestions else "—",
            ))
    else:
        replacement = name

    candidates = list(session.candidate_names or [])
    if not candidates:
        session.state = STATE_AWAITING_NAMES
        session.candidate_names = [replacement]
        session.mode = MODE_SINGLE
        session.missing_compound = None
        return await _run_single_compound(replacement, session, db, is_arabic)

    # Replace the specific compound that triggered MISSING_DATA (CQ1 fix).
    # Fall back to replacing the last entry if tracking info was lost.
    failed = session.missing_compound
    if failed and failed in candidates:
        idx = candidates.index(failed)
        candidates[idx] = replacement
    else:
        candidates[-1] = replacement

    session.candidate_names = candidates
    session.missing_compound = None

    if len(candidates) == 1:
        return await _run_single_compound(candidates[0], session, db, is_arabic)
    return await _run_multi_compound(candidates, session, db, is_arabic)


async def _run_single_compound(
    compound_name: str,
    session: FreePathSession,
    db: AsyncSession,
    is_arabic: bool,
) -> dict[str, Any]:
    session.mode = MODE_SINGLE
    session.candidate_names = [compound_name]
    result = await best_deals_in_compound(compound_name, db)

    if result["missing"] in ("no_resale_listings", "no_dev_benchmark"):
        session.state = STATE_MISSING_DATA
        session.missing_compound = compound_name
        suggestions = await similar_compounds(compound_name, db, limit=3)
        response = _plain_response(
            copy.MISSING_RESALE_AR.format(compound=compound_name)
            if is_arabic else copy.MISSING_RESALE_EN.format(compound=compound_name)
        )
        if suggestions:
            response["similar_compounds"] = suggestions
        return response

    top = result["top_listings"]
    if not top:
        session.state = STATE_MISSING_DATA
        session.missing_compound = compound_name
        suggestions = await similar_compounds(compound_name, db, limit=3)
        response = _plain_response(
            copy.MISSING_RESALE_AR.format(compound=compound_name)
            if is_arabic else copy.MISSING_RESALE_EN.format(compound=compound_name)
        )
        if suggestions:
            response["similar_compounds"] = suggestions
        return response

    properties: list[dict[str, Any]] = []
    for i, listing in enumerate(top):
        if i == 0:
            type_label = (
                copy.TYPE_LABEL_AR.get(listing["type"], listing["type"])
                if is_arabic else listing["type"].title()
            )
            properties.append({
                "id": listing["property_id"],
                "title": listing["title"] or f"{type_label} — {compound_name}",
                "location": listing.get("compound") or compound_name,
                "compound": compound_name,
                "developer": listing.get("developer") or "",
                "type": listing["type"],
                "type_label": type_label,
                "size_sqm": listing["size_sqm"],
                "bedrooms": listing.get("bedrooms") or 0,
                "price": listing["resale_price"],
                "price_per_sqm": listing.get("price_per_sqm"),
                "image_url": listing.get("image_url") or "",
                "url": listing.get("nawy_url"),
                "status": "Resale",
                "dev_avg": listing["dev_avg"],
                "gap_egp": listing["gap_egp"],
                "gap_pct": listing.get("gap_pct"),
                "tags": ["best-deal"] if not is_arabic else ["أفضل-عرض"],
                "locked": False,
            })
        else:
            properties.append({
                "compound": compound_name,
                "locked": True,
                "lock_reason": "premium_required",
            })

    best = top[0]
    type_label_ar = copy.TYPE_LABEL_AR.get(best["type"], best["type"])
    if is_arabic:
        headline = copy.SINGLE_TOP_HEADLINE_AR.format(
            compound=compound_name,
            type_ar=type_label_ar,
            size=best["size_sqm"] or "—",
            price=_fmt_price_short(best["resale_price"]),
            gap_egp=_format_egp(best["gap_egp"]),
        )
    else:
        headline = copy.SINGLE_TOP_HEADLINE_EN.format(
            compound=compound_name,
            type_en=best["type"].title(),
            size=best["size_sqm"] or "—",
            price=_fmt_price_short(best["resale_price"]),
            gap_egp=_format_egp(best["gap_egp"]),
        )

    # Append delivery track record if available.
    developer = best.get("developer") or ""
    delivery_line = _delivery_track_record_line(developer, is_arabic)
    if delivery_line:
        headline = f"{headline}\n{delivery_line}"

    session.state = STATE_DONE
    session.comparison_used = True
    response = {
        "type": "comparison",
        "response_type": "free_local",
        "text": headline,
        "properties": properties,
        "show_upsell": False,
        "upsell_reason": None,
        "cta_actions": [],
    }
    _maybe_attach_deal_cta(session, response, is_arabic)
    return response


async def _run_single_developer(
    developer_name: str,
    session: FreePathSession,
    db: AsyncSession,
    is_arabic: bool,
) -> dict[str, Any]:
    session.mode = MODE_SINGLE
    session.candidate_names = [developer_name]

    compounds = list_developer_compounds(developer_name)
    if not compounds:
        return await _run_single_compound(developer_name, session, db, is_arabic)

    all_deals: list[dict[str, Any]] = []
    for compound in compounds:
        result = await best_deals_in_compound(compound, db)
        if result.get("missing") is False:
            all_deals.extend(result.get("top_listings") or [])

    all_deals.sort(key=lambda deal: deal.get("gap_egp") or 0, reverse=True)
    top = all_deals[:3]

    if not top:
        session.state = STATE_MISSING_DATA
        session.missing_compound = developer_name
        template = copy.DEVELOPER_MISSING_DEALS_AR if is_arabic else copy.DEVELOPER_MISSING_DEALS_EN
        return _plain_response(template.format(
            developer=_display_name(developer_name, is_arabic),
            suggestions=", ".join(compounds[:3]) if compounds else "—",
        ))

    properties: list[dict[str, Any]] = []
    for i, listing in enumerate(top):
        compound = listing.get("compound") or developer_name
        if i == 0:
            type_label = (
                copy.TYPE_LABEL_AR.get(listing["type"], listing["type"])
                if is_arabic else listing["type"].title()
            )
            properties.append({
                "id": listing["property_id"],
                "title": listing["title"] or f"{type_label} — {compound}",
                "location": compound,
                "compound": compound,
                "developer": listing.get("developer") or developer_name,
                "type": listing["type"],
                "type_label": type_label,
                "size_sqm": listing["size_sqm"],
                "bedrooms": listing.get("bedrooms") or 0,
                "price": listing["resale_price"],
                "price_per_sqm": listing.get("price_per_sqm"),
                "image_url": listing.get("image_url") or "",
                "url": listing.get("nawy_url"),
                "status": "Resale",
                "dev_avg": listing["dev_avg"],
                "gap_egp": listing["gap_egp"],
                "gap_pct": listing.get("gap_pct"),
                "tags": ["best-deal"] if not is_arabic else ["أفضل-عرض"],
                "locked": False,
            })
        else:
            properties.append({
                "compound": compound,
                "developer": listing.get("developer") or developer_name,
                "locked": True,
                "lock_reason": "premium_required",
            })

    best = top[0]
    best_compound = best.get("compound") or developer_name
    type_label_ar = copy.TYPE_LABEL_AR.get(best["type"], best["type"])
    if is_arabic:
        headline = copy.DEVELOPER_TOP_HEADLINE_AR.format(
            developer=_display_name(developer_name, is_arabic),
            compound=best_compound,
            type_ar=type_label_ar,
            size=best["size_sqm"] or "—",
            price=_fmt_price_short(best["resale_price"]),
            gap_egp=_format_egp(best["gap_egp"]),
        )
    else:
        headline = copy.DEVELOPER_TOP_HEADLINE_EN.format(
            developer=developer_name,
            compound=best_compound,
            type_en=best["type"].title(),
            size=best["size_sqm"] or "—",
            price=_fmt_price_short(best["resale_price"]),
            gap_egp=_format_egp(best["gap_egp"]),
        )

    delivery_line = _delivery_track_record_line(developer_name, is_arabic)
    if delivery_line:
        headline = f"{headline}\n{delivery_line}"

    session.state = STATE_DONE
    session.comparison_used = True
    response = {
        "type": "comparison",
        "response_type": "free_local",
        "text": headline,
        "properties": properties,
        "show_upsell": False,
        "upsell_reason": None,
        "cta_actions": [],
    }
    _maybe_attach_deal_cta(session, response, is_arabic)
    return response


async def _run_multi_compound(
    compound_names: list[str],
    session: FreePathSession,
    db: AsyncSession,
    is_arabic: bool,
    resolved_from: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    session.mode = MODE_MULTI
    session.candidate_names = list(compound_names)
    result = await compare_compounds(compound_names, db)

    if result["missing_compound"]:
        session.state = STATE_MISSING_DATA
        missing = result["missing_compound"]
        session.missing_compound = missing  # CQ1: track which compound failed
        suggestions = await similar_compounds(missing, db, limit=3)
        response = _plain_response(
            copy.MISSING_RESALE_AR.format(compound=missing)
            if is_arabic else copy.MISSING_RESALE_EN.format(compound=missing)
        )
        if suggestions:
            response["similar_compounds"] = suggestions
        return response

    if not result["winner"]:
        session.state = STATE_AWAITING_NAMES
        session.candidate_names = []
        session.comparison_used = False
        return _plain_response(
            copy.NO_POSITIVE_GAP_AR.format(names=_format_name_list(compound_names, is_arabic))
            if is_arabic else copy.NO_POSITIVE_GAP_EN.format(names=_format_name_list(compound_names, is_arabic))
        )

    winner = result["winner"]
    properties: list[dict[str, Any]] = []
    winning_entry = next(c for c in result["per_compound"] if c["compound"] == winner)

    apt_seg = winning_entry.get("apartment")
    villa_seg = winning_entry.get("villa")
    if apt_seg and villa_seg:
        winner_type, winner_seg = (
            ("apartment", apt_seg) if apt_seg["gap_egp"] >= villa_seg["gap_egp"]
            else ("villa", villa_seg)
        )
    elif apt_seg:
        winner_type, winner_seg = "apartment", apt_seg
    elif villa_seg:
        winner_type, winner_seg = "villa", villa_seg
    else:
        winner_type, winner_seg = "apartment", {"gap_egp": 0.0, "res_avg": 0.0}

    type_label = (
        copy.TYPE_LABEL_AR.get(winner_type, winner_type)
        if is_arabic else winner_type.title()
    )

    # Include confidence tier in the winner card so the frontend can render the badge.
    winner_confidence = winner_seg.get("confidence", "indicative") if winner_seg else "indicative"

    properties.append({
        "id": f"compound:{winner}:{winner_type}",
        "title": f"{type_label} — {winner}",
        "location": winner,
        "compound": winner,
        "type": winner_type,
        "type_label": type_label,
        "price": winner_seg.get("res_avg", 0.0),
        "dev_avg": winner_seg.get("dev_avg"),
        "gap_egp": winner_seg.get("gap_egp"),
        "apartment": apt_seg,
        "villa": villa_seg,
        "max_gap_egp": winning_entry.get("max_gap_egp"),
        "confidence": winner_confidence,
        "confidence_label": _confidence_label(winner_confidence, is_arabic),
        "data_as_of": winning_entry.get("data_as_of"),
        "status": "Best price",
        "tags": ["أفضل-عرض"] if is_arabic else ["best-deal"],
        "locked": False,
    })

    for entry in result["per_compound"]:
        if entry["compound"] == winner:
            continue
        # Include confidence data on non-winner entries too for locked cards.
        entry_apt = entry.get("apartment")
        entry_villa = entry.get("villa")
        best_seg = entry_apt or entry_villa or {}
        entry_confidence = best_seg.get("confidence", "indicative") if best_seg else "indicative"
        properties.append({
            "compound": entry["compound"],
            "confidence": entry_confidence,
            "data_as_of": entry.get("data_as_of"),
            "locked": True,
            "lock_reason": "premium_required",
        })

    apt = winning_entry.get("apartment")
    villa = winning_entry.get("villa")
    if apt and villa:
        if apt["gap_egp"] >= villa["gap_egp"]:
            type_key, gap = "apartment", apt["gap_egp"]
        else:
            type_key, gap = "villa", villa["gap_egp"]
    elif apt:
        type_key, gap = "apartment", apt["gap_egp"]
    elif villa:
        type_key, gap = "villa", villa["gap_egp"]
    else:
        type_key, gap = "apartment", winning_entry.get("max_gap_egp") or 0.0

    if is_arabic:
        headline = copy.MULTI_WINNER_HEADLINE_AR.format(
            n=len(compound_names),
            winner=winner,
            gap_egp=_format_egp(gap),
            type_ar=copy.TYPE_LABEL_AR.get(type_key, type_key),
        )
    else:
        headline = copy.MULTI_WINNER_HEADLINE_EN.format(
            n=len(compound_names),
            winner=winner,
            gap_egp=_format_egp(gap),
            type_en=type_key.title(),
        )

    note = _resolution_note(compound_names, resolved_from, is_arabic)
    if note:
        headline = f"{headline}\n{note}"

    # Append delivery track records for all compared developers if available.
    developers_noted: set[str] = set()
    for entry in result["per_compound"]:
        compound = entry["compound"]
        # Find developer via the resolved_from map (developer→compound) reversed.
        developer = None
        if resolved_from:
            developer = resolved_from.get(compound)
        if developer and developer not in developers_noted:
            delivery_line = _delivery_track_record_line(developer, is_arabic)
            if delivery_line:
                headline = f"{headline}\n{delivery_line}"
                developers_noted.add(developer)

    # Indicative tier disclaimer when winner segment has low sample count.
    if winner_confidence == "indicative":
        disclaimer = (
            "⚠️ بيانات أولية — عدد العينات محدود، يُنصح بالتحقق من المصادر"
            if is_arabic else
            "⚠️ Indicative data — limited samples, verify before deciding"
        )
        headline = f"{headline}\n{disclaimer}"

    session.state = STATE_DONE
    session.comparison_used = True
    response = {
        "type": "comparison",
        "response_type": "free_local",
        "text": headline,
        "properties": properties,
        "show_upsell": False,
        "upsell_reason": None,
        "cta_actions": [],
    }
    _maybe_attach_deal_cta(session, response, is_arabic)
    return response


def _maybe_attach_deal_cta(
    session: FreePathSession,
    response: dict[str, Any],
    is_arabic: bool,
) -> None:
    """
    Attach the deal-submission CTA to the response once per session (D9 spec).
    Sets session.has_shown_deal_cta so subsequent turns don't repeat it.
    The frontend uses the `deal_cta_delay_ms` key to show the CTA after 5s.
    """
    if session.has_shown_deal_cta:
        return
    session.has_shown_deal_cta = True
    cta_text = (
        "هل اشتريت أو بعت في هذا الكمبوند؟ سجّل صفقتك واحصل على الباقة المتقدمة مجاناً."
        if is_arabic else
        "Bought or sold in this compound? Submit your deal and unlock Premium free."
    )
    response["deal_cta"] = {
        "text": cta_text,
        "action_id": "submit_deal",
        "delay_ms": 5000,
    }


def _comparison_used_upsell(is_arabic: bool) -> dict[str, Any]:
    text = copy.COMPARISON_USED_AR if is_arabic else copy.COMPARISON_USED_EN
    return {
        "type": "upsell",
        "response_type": "free_local",
        "text": text,
        "properties": [],
        "show_upsell": True,
        "upsell_reason": "comparison_used",
        "cta_actions": _cta_actions(is_arabic),
    }
