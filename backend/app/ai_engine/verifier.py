"""
Claude-native hallucination guardrail (Token-Guard inspired).

Runs AFTER the primary response is returned to the user — this module is
designed for async, fire-and-forget invocation so it never adds latency to
the user-facing reply.

Three-stage pipeline (analogous to Token-Guard's token/segment/global stages):
  1. Claim extraction    — Haiku extracts atomic factual claims (price, area,
                           ROI, delivery, developer, legal) from the response.
  2. Claim verification  — each claim is checked against the retrieved RAG
                           context (properties_mentioned), market_indicators,
                           and (optionally) DB lookups. A per-claim Haiku
                           judgement is requested only when structured checks
                           are inconclusive.
  3. Global clustering   — unverified claims are persisted to
                           `hallucination_flags` so a weekly clustering job
                           can surface recurring hallucination patterns.

The public entry point is `log_hallucination_flags(...)` which swallows all
exceptions so the caller can safely `asyncio.create_task(...)` it.
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from anthropic import AsyncAnthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import config
from app.database import AsyncSessionLocal


logger = logging.getLogger(__name__)


# Haiku model — cheap + fast, suitable for post-hoc verification.
# Mirrors the model string already used in ingestion/llm_normalizer.py.
VERIFIER_MODEL = os.getenv("VERIFIER_MODEL", "claude-haiku-4-5-20251001")

# Token budget for the extractor. Tight on purpose — we only want claims.
_EXTRACTOR_MAX_TOKENS = 700

# Max response chars to send to the verifier. Long narratives get truncated —
# the important factual claims are almost always near property mentions.
_MAX_RESPONSE_CHARS = 4000

CLAIM_TYPES = ("price", "roi", "area", "delivery", "developer", "legal", "other")
SEVERITIES = ("low", "medium", "high")


@dataclass
class ExtractedClaim:
    """A single atomic factual claim extracted from the response."""

    claim_type: str
    text: str
    numeric_value: Optional[float] = None
    unit: Optional[str] = None
    subject: Optional[str] = None  # e.g. compound name, developer name

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_type": self.claim_type,
            "text": self.text,
            "numeric_value": self.numeric_value,
            "unit": self.unit,
            "subject": self.subject,
        }


@dataclass
class ClaimVerdict:
    """Outcome of verifying a single claim against grounded evidence."""

    claim: ExtractedClaim
    verified: bool
    severity: str  # low | medium | high
    evidence_source: Optional[str] = None
    reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim": self.claim.to_dict(),
            "verified": self.verified,
            "severity": self.severity,
            "evidence_source": self.evidence_source,
            "reason": self.reason,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: Claim extraction (Haiku + JSON tool-use)
# ─────────────────────────────────────────────────────────────────────────────

_EXTRACTOR_SYSTEM = """You extract atomic factual claims from Egyptian real-estate AI replies.

A claim is a single verifiable statement of fact — a price, ROI %, area, delivery date,
developer name, legal/compliance statement. Ignore greetings, hedges, questions,
and opinions.

Return JSON only. No prose, no markdown, no backticks.

Schema:
{
  "claims": [
    {
      "claim_type": "price" | "roi" | "area" | "delivery" | "developer" | "legal" | "other",
      "text": "<verbatim sentence fragment with the claim>",
      "numeric_value": <number or null>,
      "unit": "EGP" | "USD" | "sqm" | "%" | "years" | null,
      "subject": "<compound/developer/user name if relevant, else null>"
    }
  ]
}

If the reply contains no verifiable factual claims, return {"claims": []}.
"""


async def _extract_claims(
    client: AsyncAnthropic, response_text: str
) -> List[ExtractedClaim]:
    """Ask Haiku to enumerate atomic factual claims as JSON."""

    snippet = response_text.strip()[:_MAX_RESPONSE_CHARS]
    if not snippet:
        return []

    user_msg = (
        "Extract every atomic factual claim from this AI reply. "
        "Return JSON only.\n\n---\n" + snippet + "\n---"
    )

    try:
        resp = await client.messages.create(
            model=VERIFIER_MODEL,
            max_tokens=_EXTRACTOR_MAX_TOKENS,
            system=_EXTRACTOR_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
        )
    except Exception as e:  # pragma: no cover — network failures
        logger.warning(f"Verifier claim-extraction call failed: {e}")
        return []

    raw = "".join(
        block.text for block in resp.content if getattr(block, "type", None) == "text"
    ).strip()
    if not raw:
        return []

    # Strip accidental code fences just in case.
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.IGNORECASE).strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Verifier: claim extraction returned non-JSON; dropping")
        return []

    claims_raw = data.get("claims") if isinstance(data, dict) else None
    if not isinstance(claims_raw, list):
        return []

    out: List[ExtractedClaim] = []
    for item in claims_raw:
        if not isinstance(item, dict):
            continue
        claim_type = str(item.get("claim_type") or "other").lower()
        if claim_type not in CLAIM_TYPES:
            claim_type = "other"
        text = str(item.get("text") or "").strip()
        if not text:
            continue
        nv = item.get("numeric_value")
        try:
            numeric_value = float(nv) if nv is not None else None
        except (TypeError, ValueError):
            numeric_value = None
        out.append(
            ExtractedClaim(
                claim_type=claim_type,
                text=text[:500],
                numeric_value=numeric_value,
                unit=(str(item.get("unit")) if item.get("unit") else None),
                subject=(str(item.get("subject")) if item.get("subject") else None),
            )
        )
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: Per-claim verification against grounded evidence
# ─────────────────────────────────────────────────────────────────────────────


def _normalize(s: Any) -> str:
    return re.sub(r"\s+", " ", str(s or "").strip().lower())


def _price_match(claim_value: float, prop: Dict[str, Any]) -> bool:
    """True if `claim_value` (EGP) is within 2% of any numeric price field."""
    candidates = [prop.get("price"), prop.get("price_per_sqm")]
    for c in candidates:
        try:
            if c is None:
                continue
            cf = float(c)
            if cf <= 0:
                continue
            if abs(claim_value - cf) / cf <= 0.02:
                return True
        except (TypeError, ValueError):
            continue
    return False


def _area_match(claim_value: float, prop: Dict[str, Any]) -> bool:
    for key in ("size_sqm", "land_area"):
        try:
            c = prop.get(key)
            if c is None:
                continue
            cf = float(c)
            if cf <= 0:
                continue
            if abs(claim_value - cf) / cf <= 0.05:
                return True
        except (TypeError, ValueError):
            continue
    return False


def _developer_match(subject: str, props: Iterable[Dict[str, Any]]) -> bool:
    s = _normalize(subject)
    if not s:
        return False
    for p in props:
        for key in ("developer", "compound", "title", "location"):
            if s in _normalize(p.get(key)):
                return True
    return False


def _verify_structurally(
    claim: ExtractedClaim, properties_mentioned: List[Dict[str, Any]]
) -> Optional[ClaimVerdict]:
    """Deterministic checks that don't need an LLM.

    Returns a verdict ONLY when we can confidently decide either way; returns
    `None` when the claim needs LLM adjudication.
    """

    props = properties_mentioned or []

    if claim.claim_type == "price" and claim.numeric_value is not None:
        if any(_price_match(claim.numeric_value, p) for p in props):
            return ClaimVerdict(
                claim=claim,
                verified=True,
                severity="low",
                evidence_source="properties_mentioned.price",
                reason="price within 2% of a retrieved property",
            )
        if props:
            return ClaimVerdict(
                claim=claim,
                verified=False,
                severity="high",
                evidence_source="properties_mentioned.price",
                reason="price does not match any retrieved property within 2%",
            )
        return None

    if claim.claim_type == "area" and claim.numeric_value is not None:
        if any(_area_match(claim.numeric_value, p) for p in props):
            return ClaimVerdict(
                claim=claim,
                verified=True,
                severity="low",
                evidence_source="properties_mentioned.size_sqm",
                reason="area within 5% of a retrieved property",
            )
        if props:
            return ClaimVerdict(
                claim=claim,
                verified=False,
                severity="medium",
                evidence_source="properties_mentioned.size_sqm",
                reason="area does not match any retrieved property within 5%",
            )
        return None

    if claim.claim_type == "developer" and claim.subject:
        if _developer_match(claim.subject, props):
            return ClaimVerdict(
                claim=claim,
                verified=True,
                severity="low",
                evidence_source="properties_mentioned.developer",
                reason="developer/compound mentioned in retrieved properties",
            )
        if props:
            return ClaimVerdict(
                claim=claim,
                verified=False,
                severity="high",
                evidence_source="properties_mentioned.developer",
                reason="developer/compound not present in retrieved properties",
            )
        return None

    # ROI / delivery / legal / other — defer to LLM adjudication.
    return None


_ADJUDICATOR_SYSTEM = """You fact-check a single claim from a real-estate AI reply.

You are given:
  - the claim (JSON)
  - the grounded evidence (list of properties the AI retrieved, with price,
    size_sqm, developer, compound, delivery_date, etc.)

Decide whether the claim is SUPPORTED by the evidence, UNSUPPORTED (contradicted
or missing), or UNCERTAIN.

Return JSON only, no prose:
{
  "verified": true | false,
  "severity": "low" | "medium" | "high",
  "reason": "<one short sentence>"
}

Be conservative: prefer verified=false when evidence is absent.
Use severity=high for invented developers/compounds, concrete wrong prices, or
false legal/regulatory statements; medium for unverifiable ROI/delivery; low
for soft rounding or paraphrase.
"""


async def _adjudicate_with_llm(
    client: AsyncAnthropic,
    claim: ExtractedClaim,
    properties_mentioned: List[Dict[str, Any]],
) -> ClaimVerdict:
    """LLM-based fallback verification for claims without deterministic rules."""

    evidence = [
        {
            "compound": p.get("compound"),
            "developer": p.get("developer"),
            "price": p.get("price"),
            "size_sqm": p.get("size_sqm"),
            "delivery_date": p.get("delivery_date"),
            "location": p.get("location"),
        }
        for p in (properties_mentioned or [])[:6]
    ]

    user_msg = json.dumps(
        {"claim": claim.to_dict(), "evidence": evidence}, ensure_ascii=False
    )

    try:
        resp = await client.messages.create(
            model=VERIFIER_MODEL,
            max_tokens=200,
            system=_ADJUDICATOR_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
        )
    except Exception as e:  # pragma: no cover
        logger.warning(f"Verifier adjudicator call failed: {e}")
        # Treat as uncertain → flag with medium severity so it shows up in clusters.
        return ClaimVerdict(
            claim=claim,
            verified=False,
            severity="medium",
            evidence_source="adjudicator.error",
            reason=f"adjudicator error: {e}",
        )

    raw = "".join(
        b.text for b in resp.content if getattr(b, "type", None) == "text"
    ).strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.IGNORECASE).strip()

    try:
        data = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        data = {}

    verified = bool(data.get("verified", False))
    severity = str(data.get("severity") or "medium").lower()
    if severity not in SEVERITIES:
        severity = "medium"
    reason = str(data.get("reason") or "").strip()[:500] or None

    return ClaimVerdict(
        claim=claim,
        verified=verified,
        severity=severity,
        evidence_source="adjudicator.haiku",
        reason=reason,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Stage 3: Persistence (global tracking → enables weekly clustering)
# ─────────────────────────────────────────────────────────────────────────────


async def _persist_flags(
    session: AsyncSession,
    *,
    agent_name: str,
    session_id: Optional[str],
    user_id: Optional[int],
    query: Optional[str],
    response_text: str,
    verdicts: List[ClaimVerdict],
) -> int:
    """Persist UNVERIFIED verdicts as hallucination_flags rows.

    Verified claims are not stored — they'd drown the clustering signal.
    Returns the number of rows inserted.
    """

    # Local import so models.py stays loadable even if the migration hasn't
    # run yet in an older environment.
    try:
        from app.models import HallucinationFlag
    except ImportError:
        logger.warning("HallucinationFlag model unavailable; skipping persistence")
        return 0

    rows = 0
    truncated_response = (response_text or "")[:8000]
    truncated_query = (query or "")[:2000] if query else None

    for v in verdicts:
        if v.verified:
            continue
        flag = HallucinationFlag(
            agent_name=agent_name[:64],
            session_id=(session_id[:128] if session_id else None),
            user_id=user_id,
            query=truncated_query,
            response_text=truncated_response,
            claim_text=v.claim.text[:500],
            claim_type=v.claim.claim_type,
            verified=False,
            evidence_source=(v.evidence_source or "")[:128] or None,
            severity=v.severity,
            verifier_model=VERIFIER_MODEL,
            verifier_reason=v.reason,
        )
        session.add(flag)
        rows += 1

    if rows:
        await session.commit()
        logger.info(
            f"🚩 Verifier flagged {rows} claim(s) for agent={agent_name} "
            f"session={session_id}"
        )
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────


async def verify_response(
    response_text: str,
    properties_mentioned: Optional[List[Dict[str, Any]]] = None,
    *,
    client: Optional[AsyncAnthropic] = None,
) -> List[ClaimVerdict]:
    """Run extraction + verification and return verdicts.

    No DB persistence here — callers that want to log use
    `log_hallucination_flags`. Exposed separately so tests and admin tooling
    can inspect verdicts without a session.
    """

    if not response_text or not response_text.strip():
        return []

    own_client = client is None
    if own_client:
        client = AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)

    try:
        claims = await _extract_claims(client, response_text)
        if not claims:
            return []

        verdicts: List[ClaimVerdict] = []
        for claim in claims:
            structural = _verify_structurally(claim, properties_mentioned or [])
            if structural is not None:
                verdicts.append(structural)
                continue
            verdicts.append(
                await _adjudicate_with_llm(client, claim, properties_mentioned or [])
            )
        return verdicts
    finally:
        # AsyncAnthropic does not require explicit close, but be tidy if we own it.
        if own_client:
            try:
                await client.close()  # type: ignore[func-returns-value]
            except Exception:
                pass


async def log_hallucination_flags(
    response_text: str,
    properties_mentioned: Optional[List[Dict[str, Any]]] = None,
    *,
    agent_name: str = "wolf_brain",
    session_id: Optional[str] = None,
    user_id: Optional[int] = None,
    query: Optional[str] = None,
) -> Dict[str, Any]:
    """Fire-and-forget safe entry point used by the SPEAK stage.

    Creates its OWN DB session so it can survive the request scope being
    torn down. Swallows all exceptions — the caller can safely wrap this
    in `asyncio.create_task(...)` without worrying about crashing workers.
    """

    summary: Dict[str, Any] = {
        "agent_name": agent_name,
        "session_id": session_id,
        "total_claims": 0,
        "flagged": 0,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        verdicts = await verify_response(
            response_text=response_text,
            properties_mentioned=properties_mentioned or [],
        )
        summary["total_claims"] = len(verdicts)
        summary["flagged"] = sum(1 for v in verdicts if not v.verified)

        if not verdicts:
            return summary

        async with AsyncSessionLocal() as session:
            rows = await _persist_flags(
                session,
                agent_name=agent_name,
                session_id=session_id,
                user_id=user_id,
                query=query,
                response_text=response_text,
                verdicts=verdicts,
            )
            summary["persisted"] = rows
    except Exception as e:  # pragma: no cover — background task safety
        logger.warning(f"log_hallucination_flags failed silently: {e}")
        summary["error"] = str(e)

    summary["finished_at"] = datetime.now(timezone.utc).isoformat()
    return summary


__all__ = [
    "VERIFIER_MODEL",
    "ExtractedClaim",
    "ClaimVerdict",
    "verify_response",
    "log_hallucination_flags",
]
