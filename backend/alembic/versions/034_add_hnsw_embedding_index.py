"""Add HNSW index on properties.embedding for fast cosine similarity

Revision ID: 034_add_hnsw_embedding_index
Revises: 033_add_delivery_year
Create Date: 2026-05-27

The zero-token retrieval pipeline's L2d ('more like this') path uses
pgvector cosine similarity. Without an index, this is a sequential
scan over 22K+ rows (~150ms p99). An HNSW index brings it to ~5ms.

Run AFTER scripts/embed_backfill.py has populated the embedding column;
the index quality depends on real vectors being present.

Note: we DON'T use CONCURRENTLY here despite the pgvector docs
recommending it. CONCURRENTLY requires escaping Alembic's transactional
DDL, which is brittle across SQLAlchemy versions. With only ~22K rows
the in-transaction build completes in ~60 seconds with a brief table
lock — acceptable for a one-time migration.

Tuning:
    m = 16              -- max connections per node (default; balanced)
    ef_construction = 64 -- candidate set size during build (default)

Idempotent: IF NOT EXISTS guard so re-running is a no-op.
"""
from alembic import op


revision = "034_add_hnsw_embedding_index"
down_revision = "033_add_delivery_year"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_properties_embedding_hnsw
        ON properties USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_properties_embedding_hnsw")
