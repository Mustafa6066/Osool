"""Add HNSW index on properties.embedding for fast cosine similarity

Revision ID: 034_add_hnsw_embedding_index
Revises: 033_add_delivery_year
Create Date: 2026-05-27

The zero-token retrieval pipeline's L2d ("more like this") path uses
pgvector cosine similarity. Without an index, this is a sequential
scan over 22K+ rows — ~150ms p99. An HNSW index brings it to ~5ms.

CRITICAL: This migration runs AFTER scripts/embed_backfill.py has
populated the embedding column for most rows. Building HNSW on an
empty/mostly-null column wastes memory and produces a bad index that
will be rebuilt later. The migration is safe to run on any state, but
the index quality depends on having real vectors in the column.

The CREATE INDEX uses CONCURRENTLY so it doesn't lock the properties
table during build (~60 sec on 22K rows). CONCURRENTLY cannot run
inside a transaction, so we use op.execute with autocommit semantics.

Tuning:
    m = 16              -- max connections per node (default; balanced)
    ef_construction = 64 -- candidate set size during build (default)

Both are sane defaults from the pgvector docs. Tune later if recall
needs to improve at the cost of build time.
"""
from alembic import op


revision = "034_add_hnsw_embedding_index"
down_revision = "033_add_delivery_year"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # CREATE INDEX CONCURRENTLY cannot run inside a transaction. Alembic
    # opens one by default; we have to break out of it.
    conn = op.get_bind()
    # AUTOCOMMIT for this DDL only
    conn.execute("COMMIT")  # close the autostart tx
    try:
        conn.exec_driver_sql(
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_properties_embedding_hnsw
            ON properties USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64)
            """
        )
    finally:
        # Re-open a tx so Alembic's own bookkeeping commit at the end of
        # the migration is well-formed.
        conn.execute("BEGIN")


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute("COMMIT")
    try:
        conn.exec_driver_sql(
            "DROP INDEX CONCURRENTLY IF EXISTS ix_properties_embedding_hnsw"
        )
    finally:
        conn.execute("BEGIN")
