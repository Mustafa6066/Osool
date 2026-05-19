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
)
from app.ai_engine.flagship_compounds import (
    DEVELOPER_TO_COMPOUNDS,
    list_developer_compounds,
    resolve_to_compound,
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

    # DONE is the upsell-only terminal state. Any further turn here is gated
    # at the router layer (comparison_used == True), but we handle it here too
    # for completeness.
    if state == STATE_DONE:
        return _comparison_used_upsell(is_arabic)

    # In MISSING_DATA we're waiting for the user to name a replacement compound.
    if state == STATE_MISSING_DATA:
        return await _handle_missing_data(query, session, db, is_arabic)

    # Default path: AWAITING_NAMES (or VALIDATING re-entry from a prior failure).
    return await _handle_awaiting_names(query, session, db, is_arabic)


async def _handle_awaiting_names(
    query: str,
    session: FreePathSession,
    db: AsyncSession,
    is_arabic: bool,
) -> dict[str, Any]:
    entities = local_intent_extractor.extract_entities(query)

    # Non-comparison intent with no entities → redirect.
    if not entities and not local_intent_extractor.is_comparison_intent(query):
        return _plain_response(
            copy.FREE_PATH_REDIRECT_AR if is_arabic else copy.FREE_PATH_REDIRECT_EN
        )

    if len(entities) == 0:
        # Intent looks like comparison but no names yet.
        return _plain_response(
            copy.FREE_PATH_REDIRECT_AR if is_arabic else copy.FREE_PATH_REDIRECT_EN
        )

    if len(entities) > 3:
        names = ", ".join(name for name, _ in entities)
        text = (
            copy.TOO_MANY_AR.format(names=names)
            if is_arabic
            else copy.TOO_MANY_EN.format(names=names)
        )
        return _plain_response(text)

    # Resolve any developer entries to flagship compounds.
    resolved: list[str] = []
    for name, kind in entities:
        if kind == "developer":
            compound = await resolve_to_compound(name, db)
            if compound is None:
                # Developer is tracked but no flagship has enough rows — ask
                # the user to pick a specific compound.
                suggestions = list_developer_compounds(name)[:3]
                template = (
                    copy.DEVELOPER_NO_FLAGSHIP_AR if is_arabic
                    else copy.DEVELOPER_NO_FLAGSHIP_EN
                )
                return _plain_response(template.format(
                    developer=name,
                    suggestions=", ".join(suggestions) if suggestions else "—",
                ))
            resolved.append(compound)
        else:
            resolved.append(name)

    # Deduplicate while preserving order — a user might mention "Sodic" and
    # "Sodic East" and we resolved both to the same compound.
    seen: set[str] = set()
    deduped: list[str] = []
    for name in resolved:
        if name not in seen:
            seen.add(name)
            deduped.append(name)

    if len(deduped) == 1:
        return await _run_single_compound(deduped[0], session, db, is_arabic)
    return await _run_multi_compound(deduped, session, db, is_arabic)


async def _handle_missing_data(
    query: str,
    session: FreePathSession,
    db: AsyncSession,
    is_arabic: bool,
) -> dict[str, Any]:
    """
    User was asked to swap a compound. We expect exactly one new entity in
    their reply. Anything else → stay in MISSING_DATA and re-prompt.
    """
    entities = local_intent_extractor.extract_entities(query)
    if not entities:
        return _plain_response(
            copy.MISSING_RESALE_AR.format(compound="—")
            if is_arabic else copy.MISSING_RESALE_EN.format(compound="—")
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

    # Swap the first entry whose data was missing. Conservative implementation:
    # we don't track which one specifically failed; instead, retry the entire
    # candidate set with the new compound appended in place of the last entry.
    candidates = list(session.candidate_names or [])
    if not candidates:
        # Lost state — restart awaiting.
        session.state = STATE_AWAITING_NAMES
        session.candidate_names = [replacement]
        session.mode = MODE_SINGLE
        return await _run_single_compound(replacement, session, db, is_arabic)

    candidates[-1] = replacement
    session.candidate_names = candidates
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

    if result["missing"] == "no_resale_listings" or result["missing"] == "no_dev_benchmark":
        session.state = STATE_MISSING_DATA
        return _plain_response(
            copy.MISSING_RESALE_AR.format(compound=compound_name)
            if is_arabic else copy.MISSING_RESALE_EN.format(compound=compound_name)
        )

    top = result["top_listings"]
    if not top:
        session.state = STATE_MISSING_DATA
        return _plain_response(
            copy.MISSING_RESALE_AR.format(compound=compound_name)
            if is_arabic else copy.MISSING_RESALE_EN.format(compound=compound_name)
        )

    # Build the property cards: #1 unblurred (full numbers), the rest locked.
    # Field names must match the frontend's mapChatPropertyToProperty (chat-utils.ts):
    # price, location, image_url, developer, bedrooms, size_sqm, price_per_sqm, url, status.
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
                "tags": ["best-deal"] if is_arabic is False else ["أفضل-عرض"],
                "locked": False,
            })
        else:
            # Locked card: explicit marker so the frontend renders a single
            # "unlock to see more" tile instead of a fake property row.
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

    session.state = STATE_DONE
    session.comparison_used = True
    # NB: show_upsell stays False on the SUCCESS turn — the blurred property
    # cards already convey "there's more locked behind upgrade", and the
    # frontend's consultant-handoff chrome triggers on show_upsell|cta_actions
    # which would mis-frame this as "your question needs deep analysis".
    # The upsell fires on the NEXT turn via comparison_used gating.
    return {
        "type": "comparison",
        "response_type": "free_local",
        "text": headline,
        "properties": properties,
        "show_upsell": False,
        "upsell_reason": None,
        "cta_actions": [],
    }


async def _run_multi_compound(
    compound_names: list[str],
    session: FreePathSession,
    db: AsyncSession,
    is_arabic: bool,
) -> dict[str, Any]:
    session.mode = MODE_MULTI
    session.candidate_names = list(compound_names)
    result = await compare_compounds(compound_names, db)

    if result["missing_compound"]:
        session.state = STATE_MISSING_DATA
        missing = result["missing_compound"]
        return _plain_response(
            copy.MISSING_RESALE_AR.format(compound=missing)
            if is_arabic else copy.MISSING_RESALE_EN.format(compound=missing)
        )

    if not result["winner"]:
        session.state = STATE_MISSING_DATA
        return _plain_response(
            copy.MISSING_RESALE_AR.format(compound=compound_names[0])
            if is_arabic else copy.MISSING_RESALE_EN.format(compound=compound_names[0])
        )

    # Build property cards: winner card uses real numbers from the best-gap
    # segment so the frontend renders it as a regular property tile. Losing
    # compounds become locked tiles (single paywall row in the UI).
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
        "status": "Best price",
        "tags": ["أفضل-عرض"] if is_arabic else ["best-deal"],
        "locked": False,
    })
    for entry in result["per_compound"]:
        if entry["compound"] == winner:
            continue
        properties.append({
            "compound": entry["compound"],
            "locked": True,
            "lock_reason": "premium_required",
        })

    # Pick the type with the bigger gap for the headline copy.
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
        # Shouldn't happen — winner has max_gap_egp, so some segment had data.
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

    session.state = STATE_DONE
    session.comparison_used = True
    # See _run_single_compound for why show_upsell stays False on success.
    return {
        "type": "comparison",
        "response_type": "free_local",
        "text": headline,
        "properties": properties,
        "show_upsell": False,
        "upsell_reason": None,
        "cta_actions": [],
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
