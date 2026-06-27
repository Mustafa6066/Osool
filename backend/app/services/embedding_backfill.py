"""
Embedding Backfill Service
--------------------------
Nightly self-healing job for vector retrieval blind spots.

The zero-token scraper persists new/changed properties with
``embedding = NULL`` (see app/ingestion/repository.py), which excludes them
from pgvector ANN search until re-embedded. This job sweeps NULL-embedding
rows (newest first) in batches and fills them with
``text-embedding-3-small`` vectors, so blind spots last at most one day.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import Property

logger = logging.getLogger(__name__)

_EMBEDDING_MODEL = "text-embedding-3-small"
# OpenAI allows large batches; keep requests modest to bound memory/latency.
_API_BATCH_SIZE = 100
# Per-run cap so a huge backlog cannot blow the nightly token budget.
_MAX_PER_RUN = int(os.getenv("EMBED_BACKFILL_MAX_PER_RUN", "2000"))


def _build_embedding_text(prop: Property) -> str:
    """Canonical embedding text (X2). Unified in app.services.embedding_text so the
    in-process backfill, the standalone script, and the bulk seed all produce identical
    vectors. This path previously diverged (newline + Title-case + price); it now
    matches the live corpus format (pipe, lowercase, no price)."""
    from app.services.embedding_text import build_property_embedding_text

    return build_property_embedding_text(prop)


async def run_embedding_backfill(max_rows: Optional[int] = None) -> dict:
    """
    Embed available properties whose ``embedding`` is NULL, newest first.

    Returns a summary dict: {"scanned": int, "embedded": int, "failed": int}.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("[embed-backfill] OPENAI_API_KEY not set — skipping run.")
        return {"scanned": 0, "embedded": 0, "failed": 0}

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)
    cap = max_rows or _MAX_PER_RUN
    summary = {"scanned": 0, "embedded": 0, "failed": 0}

    async with AsyncSessionLocal() as db:
        rows = (
            await db.execute(
                select(Property)
                .where(Property.embedding.is_(None), Property.is_available.is_(True))
                .order_by(Property.scraped_at.desc().nullslast())
                .limit(cap)
            )
        ).scalars().all()

        summary["scanned"] = len(rows)
        if not rows:
            logger.info("[embed-backfill] No NULL-embedding properties — nothing to do.")
            return summary

        for i in range(0, len(rows), _API_BATCH_SIZE):
            batch = rows[i : i + _API_BATCH_SIZE]
            texts = [_build_embedding_text(p) for p in batch]
            try:
                response = await client.embeddings.create(
                    model=_EMBEDDING_MODEL, input=texts
                )
            except Exception as exc:
                summary["failed"] += len(batch)
                logger.error(
                    "[embed-backfill] Embedding API failed for batch %d-%d: %s",
                    i, i + len(batch), exc,
                )
                continue

            for prop, datum in zip(batch, response.data):
                prop.embedding = datum.embedding
                summary["embedded"] += 1

            # Track spend through the shared cost monitor (best-effort)
            try:
                from app.services.cost_monitor import cost_monitor
                cost_monitor.log_usage(
                    model=_EMBEDDING_MODEL,
                    input_tokens=response.usage.total_tokens,
                    output_tokens=0,
                    context="embedding_backfill",
                )
            except Exception:
                pass

            await db.commit()

    logger.info(
        "[embed-backfill] Done: scanned=%d embedded=%d failed=%d",
        summary["scanned"], summary["embedded"], summary["failed"],
    )
    return summary
