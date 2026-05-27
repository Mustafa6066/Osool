"""Convert properties.embedding to pgvector + add HNSW index

Revision ID: 034_add_hnsw_embedding_index
Revises: 033_add_delivery_year
Create Date: 2026-05-27

The properties.embedding column was originally created as TEXT (the
models.py fallback for environments where pgvector wasn't yet installed).
On Railway prod the pgvector extension IS installed (0.8.2) and 444
rows already contain JSON-stringified 1536-dim vectors in the TEXT
column. We need to:

  1. Convert the column type to vector(1536) — the cast 'embedding::vector'
     works because pgvector accepts the text form '[v1,v2,...]'.
  2. Build an HNSW index for fast cosine similarity (≤5ms p99 vs ~150ms
     sequential scan).

The cast is in-place and preserves existing data. The HNSW build runs
on whatever is currently populated (currently 444 vectors; will grow
as scripts/embed_backfill.py runs).

Note: not using CONCURRENTLY — Alembic's transactional DDL doesn't
play nicely with it on SQLAlchemy 2.x. With ~444 rows the build takes
seconds; lock is acceptable. After backfill grows the row count to
~22K the index will still rebuild fine in ~60 sec lock.

Idempotent: IF NOT EXISTS guards make re-runs safe.
"""
from alembic import op


revision = "034_add_hnsw_embedding_index"
down_revision = "033_add_delivery_year"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) Make sure the extension is enabled (idempotent).
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # 2) Convert the TEXT column to vector(1536). Existing TEXT values are
    #    JSON-stringified [v1,v2,...] arrays, which pgvector accepts as a
    #    text-form vector. NULL stays NULL. Wrap in DO block so we don't
    #    error on re-run if the column is already vector(1536).
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'properties'
                  AND column_name = 'embedding'
                  AND udt_name = 'text'
            ) THEN
                ALTER TABLE properties
                ALTER COLUMN embedding TYPE vector(1536)
                USING embedding::vector(1536);
            END IF;
        END
        $$;
        """
    )

    # 3) HNSW index (idempotent via IF NOT EXISTS).
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_properties_embedding_hnsw
        ON properties USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_properties_embedding_hnsw")
    # Revert the column back to TEXT, casting the vector to its text form.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'properties'
                  AND column_name = 'embedding'
                  AND udt_name = 'vector'
            ) THEN
                ALTER TABLE properties
                ALTER COLUMN embedding TYPE text
                USING embedding::text;
            END IF;
        END
        $$;
        """
    )
