"""
One-shot embedding backfill for the properties table.

Walks rows WHERE embedding IS NULL, batches them through OpenAI's
text-embedding-3-small endpoint, and writes the resulting vectors
back via UPDATE properties SET embedding = $vec WHERE id = $id.

Run after migration 034 (which converts properties.embedding TEXT -> vector(1536))
lands. Cost on the current inventory (~22K rows, ~150 tokens each) is ~$0.07 total.
Wall time ~30 sec at concurrency 5.

The HNSW index is built by migration 043_build_hnsw_embedding_index (single-worker
build to fit Railway's /dev/shm budget), and the app startup probe (app/main.py)
alerts if it is missing. There is no 030_hnsw_embedding.py (030 is Paymob).

Usage:
    railway run --service Osool -- python -m scripts.embed_backfill
    railway run --service Osool -- python -m scripts.embed_backfill --batch-size 100 --max-rows 5000

This script is idempotent: running it twice writes embeddings only
for rows that still have embedding IS NULL. Safe to re-run after a
partial failure.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from typing import Optional

import asyncpg

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

DEFAULT_BATCH_SIZE = 100   # OpenAI accepts up to 2048 per call; 100 keeps payloads small
DEFAULT_CONCURRENCY = 5    # parallel HTTP calls (each batch is one call)
EMBEDDING_MODEL = "text-embedding-3-small"


def _canonical_text(row: dict) -> str:
    """
    The text we embed for each property. Stable across runs so the same
    property always produces the same embedding (assuming the model is
    unchanged). Order: identifying fields first, then descriptive ones.
    """
    parts: list[str] = []

    def add(label: str, val):
        if val is None:
            return
        s = str(val).strip()
        if s:
            parts.append(f"{label}: {s}")

    add("title", row.get("title"))
    add("type", row.get("type"))
    add("compound", row.get("compound"))
    add("developer", row.get("developer"))
    add("location", row.get("location"))
    add("size_sqm", row.get("size_sqm"))
    add("bedrooms", row.get("bedrooms"))
    add("bathrooms", row.get("bathrooms"))
    add("finishing", row.get("finishing"))
    add("delivery_date", row.get("delivery_date"))
    if row.get("is_nawy_now"):
        parts.append("tag: nawy_now (instant delivery)")
    if row.get("is_delivered"):
        parts.append("tag: delivered")
    add("sale_type", row.get("sale_type"))
    desc = (row.get("description") or "").strip()
    if desc:
        parts.append(f"description: {desc[:600]}")
    return " | ".join(parts)


async def _generate_batch(texts: list[str]) -> list[list[float]]:
    """One OpenAI call, batched. Returns vectors in the same order as input texts."""
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = await client.embeddings.create(
        input=texts,
        model=EMBEDDING_MODEL,
    )
    # Sort by index in case the API ever returns out-of-order (it doesn't, but defend)
    by_idx = sorted(response.data, key=lambda d: d.index)
    return [d.embedding for d in by_idx]


def _vector_to_pg_literal(vec: list[float]) -> str:
    """pgvector accepts the text form '[1.0,2.0,...]'."""
    return "[" + ",".join(f"{v:.7g}" for v in vec) + "]"


async def _backfill_batch(conn: asyncpg.Connection, rows: list[asyncpg.Record]) -> int:
    """Embed + write a single batch. Returns count of rows updated."""
    texts = [_canonical_text(dict(r)) for r in rows]
    vectors = await _generate_batch(texts)
    written = 0
    # UPDATE in a single statement via UNNEST for speed
    ids = [r["id"] for r in rows]
    vector_literals = [_vector_to_pg_literal(v) for v in vectors]
    await conn.execute(
        """
        WITH input AS (
            SELECT * FROM unnest($1::int[], $2::text[]) AS t(id, vec)
        )
        UPDATE properties p
        SET embedding = i.vec::vector
        FROM input i
        WHERE p.id = i.id
          AND p.embedding IS NULL
        """,
        ids, vector_literals,
    )
    written = len(rows)
    return written


async def backfill(
    batch_size: int = DEFAULT_BATCH_SIZE,
    concurrency: int = DEFAULT_CONCURRENCY,
    max_rows: Optional[int] = None,
) -> dict:
    url = os.environ.get("DATABASE_PUBLIC_URL") or os.environ["DATABASE_URL"]
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    conn = await asyncpg.connect(url, ssl="require")
    try:
        # Total to do — informational
        total_remaining = await conn.fetchval(
            "SELECT COUNT(*) FROM properties WHERE embedding IS NULL"
        )
        logger.info("[backfill] %s rows with embedding IS NULL", total_remaining)

        if max_rows:
            total_remaining = min(total_remaining, max_rows)

        sem = asyncio.Semaphore(concurrency)
        written_total = 0
        offset = 0

        async def process_batch(rows):
            nonlocal written_total
            async with sem:
                try:
                    n = await _backfill_batch(conn, rows)
                    written_total += n
                    logger.info(
                        "[backfill] +%d (total %d / %d, %.1f%%)",
                        n, written_total, total_remaining,
                        100.0 * written_total / max(1, total_remaining),
                    )
                except Exception as exc:
                    logger.error("[backfill] batch failed: %s", exc)

        while True:
            rows = await conn.fetch(
                """
                SELECT id, title, type, compound, developer, location,
                       size_sqm, bedrooms, bathrooms, finishing, delivery_date,
                       is_nawy_now, is_delivered, sale_type, description
                FROM properties
                WHERE embedding IS NULL
                ORDER BY id
                LIMIT $1
                """,
                batch_size,
            )
            if not rows:
                break
            if max_rows and written_total + len(rows) > max_rows:
                rows = rows[: max_rows - written_total]
                if not rows:
                    break
            await process_batch(rows)

        return {
            "total_remaining_before": total_remaining,
            "written": written_total,
        }
    finally:
        await conn.close()


def main() -> int:
    p = argparse.ArgumentParser(description="One-shot embedding backfill for properties.embedding")
    p.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    p.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    p.add_argument("--max-rows", type=int, default=None,
                   help="Stop after N rows (for safety / testing)")
    args = p.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY not set in environment")
        return 1

    result = asyncio.run(backfill(
        batch_size=args.batch_size,
        concurrency=args.concurrency,
        max_rows=args.max_rows,
    ))
    logger.info("[backfill] done. wrote=%(written)s remaining_before=%(total_remaining_before)s", result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
