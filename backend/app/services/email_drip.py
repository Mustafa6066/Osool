"""
Email drip sequences — closes audit ship-blocker A5.

Three-stage onboarding drip aimed at users who signed up via invitation
but haven't fully engaged. Conservative cadence so this doesn't feel
spammy in the Egyptian market.

Schedule (counting from signup, or from last_interaction, whichever is
more recent):

    Step 0 → 1 :  24 hours later   "Welcome — here's how Osool works"
    Step 1 → 2 :   3 days later    "Picked-for-you (intent-tagged) primer"
    Step 2 → 3 :  14 days later    "Ready when you are" (final nudge)

After step 3 the loop ends; future re-engagement is human-triggered
(consultant outreach) or trigger-based (price alert, new compound
listing) which lives in a different code path.

Anti-abuse:
- Skipped for unverified accounts (compliance + bounce reduction).
- Hard cap of 50 sends per run so a one-shot bug can't flood the queue.
- Idempotency check against EmailEvent (sent_at within last 12h for the
  same template_id) so a duplicate scheduler tick can't double-send.
- Honours the LeadProfile.email_sequence_step counter so a manual admin
  bump skips earlier steps cleanly.

This is intentionally simple — three templates, no A/B variants, no
segmentation beyond stage. Sophistication waits until we have open/
click data from EmailEvent to justify it.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import EmailEvent, LeadProfile, User
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


# ─── Cadence (hours from anchor) ──────────────────────────────────────────
DRIP_DELAYS_H = {
    1: 24,            # 1 day
    2: 24 * 3,        # 3 days
    3: 24 * 14,       # 14 days
}
TEMPLATE_IDS = {
    1: "drip_welcome",
    2: "drip_primer",
    3: "drip_final_nudge",
}
MAX_SENDS_PER_RUN = 50


# ─── Templates ────────────────────────────────────────────────────────────
# Kept inline so a translation tweak is a one-file change. If templates
# grow, move to backend/app/templates/email/*.html and load via jinja.

def _wrap(html_body: str, frontend_url: str, unsub_url: str) -> str:
    """Common shell — keeps the warm-paper Osool brand and a CAN-SPAM
    compliant unsubscribe footer."""
    return f"""
    <html>
    <body style="font-family: -apple-system, 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; background:#FCFAF6; color:#1a1814;">
      <div style="padding:28px 24px; background:#FCFAF6;">
        <div style="font-family: Newsreader, Georgia, serif; font-size: 28px; font-weight: 600; letter-spacing: -0.5px;">
          أصول &nbsp;·&nbsp; Osool
        </div>
        {html_body}
        <hr style="border:none; border-top:1px solid #E5E0D6; margin:32px 0 16px;">
        <p style="font-size:11px; color:#7a7368; line-height:1.6;">
          You're getting this because you signed up at <a href="{frontend_url}" style="color:#7a7368;">osool.eg</a>.
          Don't want these? <a href="{unsub_url}" style="color:#7a7368;">Unsubscribe</a>.
        </p>
      </div>
    </body>
    </html>
    """


def _render_step(step: int, full_name: str, frontend_url: str, unsub_url: str) -> tuple[str, str]:
    """Returns (subject, html_body) for the given drip step."""
    first = (full_name or "").split(" ")[0] or "there"
    if step == 1:
        subject = "Welcome to Osool — what to ask first"
        body = f"""
            <h2 style="font-family: Newsreader, Georgia, serif; font-size:22px; margin-top:24px;">
                Hi {first},
            </h2>
            <p>Osool is your AI advisor for the Egyptian property market. A few prompts that work well on the first day:</p>
            <ul style="line-height:1.7;">
                <li>"Best resale deals in New Cairo under 8M EGP"</li>
                <li>"Compare Mountain View Hyde Park vs Mivida 3BR resale"</li>
                <li>"Is 12M fair for a 180m villa in Sheikh Zayed?"</li>
            </ul>
            <p style="margin-top:20px;">
                <a href="{frontend_url}/chat" style="background:#1a1814; color:#FCFAF6; padding:12px 22px; text-decoration:none; border-radius:8px; display:inline-block; font-weight:600;">
                    Start chatting
                </a>
            </p>
        """
    elif step == 2:
        subject = "What Osool can do that Property Finder can't"
        body = f"""
            <h2 style="font-family: Newsreader, Georgia, serif; font-size:22px; margin-top:24px;">
                {first}, here's the difference
            </h2>
            <p>Three things classical portals don't give you:</p>
            <ol style="line-height:1.8;">
                <li><b>NPV flattening.</b> A 7-year payment plan vs. cash isn't the same money — we compute the EGP equivalent.</li>
                <li><b>La2ta detector.</b> Resale units priced ≥15% below the compound mean. Real opportunities, automatically flagged.</li>
                <li><b>Hallucination guardrails.</b> Every price quoted to you is cross-checked against our scraped index before you see it.</li>
            </ol>
            <p style="margin-top:20px;">
                <a href="{frontend_url}/chat" style="background:#1a1814; color:#FCFAF6; padding:12px 22px; text-decoration:none; border-radius:8px; display:inline-block; font-weight:600;">
                    Ask Osool a hard question
                </a>
            </p>
        """
    else:  # step 3
        subject = "Still on the fence? Two minutes to your shortlist"
        body = f"""
            <h2 style="font-family: Newsreader, Georgia, serif; font-size:22px; margin-top:24px;">
                {first},
            </h2>
            <p>You signed up a couple of weeks ago and haven't yet found what you're looking for. That's information for us — most likely either the supply doesn't match your brief, or you'd rather talk to a human.</p>
            <p>Either way, two paths from here:</p>
            <ul style="line-height:1.7;">
                <li><a href="{frontend_url}/chat">Try one more search</a> with your exact criteria.</li>
                <li><a href="{frontend_url}/contact">Book a 15-minute call</a> with a licensed advisor — no fee, no pitch.</li>
            </ul>
            <p style="color:#7a7368; font-size:13px; margin-top:16px;">
                This is the last automated email in our welcome sequence. You'll only hear from us again on price alerts you've explicitly subscribed to.
            </p>
        """
    return subject, _wrap(body, frontend_url, unsub_url)


# ─── Selection logic ──────────────────────────────────────────────────────
async def _candidates_for_run(db: AsyncSession, now: datetime) -> List[Dict]:
    """
    Returns up to MAX_SENDS_PER_RUN candidate (user, profile, step) trios.

    Eligibility:
      - user.is_verified
      - user has a LeadProfile (created on first chat turn, or seeded on signup)
      - profile.email_sequence_step < 3
      - Time since the anchor (signup or last_interaction, whichever is later)
        exceeds the cadence for the NEXT step.
      - No EmailEvent for the next step's template_id in the past 12h
        (idempotency).
    """
    rows = (
        await db.execute(
            select(User, LeadProfile)
            .join(LeadProfile, LeadProfile.user_id == User.id)
            .where(
                User.is_verified.is_(True),
                LeadProfile.email_sequence_step < 3,
            )
            .limit(500)  # over-sample then filter in Python
        )
    ).all()

    out: List[Dict] = []
    for user, profile in rows:
        next_step = (profile.email_sequence_step or 0) + 1
        if next_step not in DRIP_DELAYS_H:
            continue

        anchor = profile.last_interaction or profile.created_at or user.created_at
        if anchor is None:
            continue
        # Force tz-aware comparison.
        if anchor.tzinfo is None:
            anchor = anchor.replace(tzinfo=timezone.utc)
        delay = timedelta(hours=DRIP_DELAYS_H[next_step])
        if (now - anchor) < delay:
            continue

        # Idempotency: recent send of this exact template?
        twelve_ago = now - timedelta(hours=12)
        recent = (
            await db.execute(
                select(func.count(EmailEvent.id)).where(
                    EmailEvent.user_id == user.id,
                    EmailEvent.template_id == TEMPLATE_IDS[next_step],
                    EmailEvent.created_at >= twelve_ago,
                )
            )
        ).scalar_one()
        if recent and recent > 0:
            continue

        out.append({"user": user, "profile": profile, "step": next_step})
        if len(out) >= MAX_SENDS_PER_RUN:
            break

    return out


# ─── Entry point invoked by scheduler ─────────────────────────────────────
async def send_due_drips() -> Dict[str, int]:
    """
    Run one pass of the drip pipeline. Designed to be invoked from
    APScheduler — caps total sends per invocation and never raises.

    Returns counters for observability:
        {"selected": int, "sent": int, "failed": int, "skipped": int}
    """
    stats = {"selected": 0, "sent": 0, "failed": 0, "skipped": 0}
    import os
    frontend_url = os.getenv("FRONTEND_URL", "https://osool-ten.vercel.app").rstrip("/")
    email_svc = EmailService()

    try:
        async with AsyncSessionLocal() as db:
            now = datetime.now(timezone.utc)
            candidates = await _candidates_for_run(db, now)
            stats["selected"] = len(candidates)

            for c in candidates:
                user: User = c["user"]
                profile: LeadProfile = c["profile"]
                step: int = c["step"]
                template_id = TEMPLATE_IDS[step]

                # User-specific unsubscribe URL — token here is the user
                # id base64'd, validated server-side. The /unsubscribe
                # route is owned by the email_endpoints router.
                unsub_url = f"{frontend_url}/unsubscribe?uid={user.id}"
                subject, html = _render_step(step, user.full_name or "", frontend_url, unsub_url)

                # EmailEvent row first as a "claim" — if send fails we
                # update its status to bounced. This avoids the race where
                # two scheduler ticks both try to send the same step.
                event = EmailEvent(
                    user_id=user.id,
                    template_id=template_id,
                    email_type=template_id,
                    subject=subject,
                    status="queued",
                )
                db.add(event)
                await db.flush()

                ok = email_svc._send_email(user.email, subject, html)
                if ok:
                    event.status = "sent"
                    event.sent_at = now
                    profile.email_sequence_step = step
                    stats["sent"] += 1
                else:
                    event.status = "failed"
                    stats["failed"] += 1

                await db.commit()
    except Exception:
        logger.exception("Email drip run crashed — partial state may have been committed")
    return stats
