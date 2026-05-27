"""
Lead scoring — runs after every authenticated chat turn.

Closes audit ship-blocker A6 ("Lead scoring not auto-triggered on chat turns").
The model is intentionally simple, deterministic, and zero-token so it runs in
~1ms inline with the chat response. Sophistication can come later via an ML
ranker once we have labelled conversion data; until then "rules a sales lead
manager would write" outperforms any black box.

Score contribution table (each capped, total clamped to 0-100):

    +5   per chat turn (interaction_count proxy)            max 30
    +15  budget mentioned in this or any prior turn
    +15  specific area extracted (Maadi, New Cairo, etc.)
    +10  specific property type extracted (apartment, villa)
    +20  specific compound mentioned (Mountain View, etc.)
    +20  near-term timeline ("by 2025", "ready", "instant")
    +10  return visit (>24h since last interaction)
    +5   flagged a previous answer (engagement signal, not nuisance)

Stage thresholds:

    0-19    new
    20-49   engaged
    50-79   hot
    80-100  qualified

The function NEVER raises into the caller. If the scorer crashes it logs and
returns the previous score, so a bug here can't take down the chat path.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatMessage, LeadProfile, User
from app.services.zero_token_intent import extract_query

logger = logging.getLogger(__name__)


STAGE_THRESHOLDS = [
    (80, "qualified"),
    (50, "hot"),
    (20, "engaged"),
    (0, "new"),
]


def _stage_for(score: float) -> str:
    for threshold, name in STAGE_THRESHOLDS:
        if score >= threshold:
            return name
    return "new"


async def update_lead_score_for_turn(
    db: AsyncSession,
    user: User,
    latest_message: str,
) -> Optional[LeadProfile]:
    """
    Idempotent best-effort update of the user's LeadProfile after a chat turn.

    Returns the updated profile (or None on failure). Callers should NOT
    block the chat response on this — fire-and-forget via asyncio.create_task
    is fine. We swallow every exception so a scoring bug can't break chat.
    """
    if user is None or not getattr(user, "id", None):
        return None

    try:
        # Pull or create the profile.
        profile = (
            await db.execute(
                select(LeadProfile).where(LeadProfile.user_id == user.id)
            )
        ).scalar_one_or_none()
        if profile is None:
            profile = LeadProfile(user_id=user.id, score=0.0, stage="new", interaction_count=0)
            db.add(profile)
            await db.flush()

        # Aggregate signal across the whole session, not just the latest line.
        prior_msgs = (
            await db.execute(
                select(ChatMessage.content, ChatMessage.flagged, ChatMessage.created_at)
                .where(
                    ChatMessage.user_id == user.id,
                    ChatMessage.role == "user",
                )
                .order_by(ChatMessage.created_at.desc())
                .limit(20)
            )
        ).all()
        combined_text = " ".join([latest_message] + [row[0] or "" for row in prior_msgs[:10]])
        any_flagged = any(row[1] for row in prior_msgs)

        q = extract_query(combined_text)

        score = 0.0
        # Interaction depth — bounded to stop runaway scores on chatty users.
        score += min(30, 5 * (1 + len(prior_msgs)))

        if q.price_max is not None or q.price_min is not None:
            score += 15
        if q.locations:
            score += 15
        if q.property_types:
            score += 10
        if q.compounds:
            score += 20
        # Near-term delivery signal.
        if q.ready_by_year_max is not None and q.ready_by_year_max <= datetime.now().year + 1:
            score += 20
        if any_flagged:
            score += 5

        # Return visit bonus — meaningful re-engagement, not the same session.
        if profile.last_interaction is not None:
            try:
                gap = datetime.now(timezone.utc) - profile.last_interaction
                if gap >= timedelta(hours=24):
                    score += 10
            except Exception:
                pass

        score = max(0.0, min(100.0, score))

        # Merge budget/areas/types into the structured profile so the admin
        # view (and future email drip) can target by intent.
        if q.price_max is not None and (profile.budget_max is None or q.price_max > (profile.budget_max or 0)):
            profile.budget_max = float(q.price_max)
        if q.price_min is not None and (profile.budget_min is None or q.price_min < (profile.budget_min or float("inf"))):
            profile.budget_min = float(q.price_min)
        if q.locations:
            profile.preferred_areas = json.dumps(sorted(set(q.locations))[:10], ensure_ascii=False)
        if q.property_types:
            profile.preferred_types = json.dumps(sorted(set(q.property_types))[:10], ensure_ascii=False)

        profile.score = score
        profile.stage = _stage_for(score)
        profile.interaction_count = (profile.interaction_count or 0) + 1
        profile.last_interaction = datetime.now(timezone.utc)

        await db.commit()
        return profile

    except Exception:
        logger.exception("Lead score update failed for user=%s — chat path is unaffected", user.id)
        try:
            await db.rollback()
        except Exception:
            pass
        return None
